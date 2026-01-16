# Subnet Competition Tracker

A tool to analyze and rank Bittensor subnets by mining pool competition based on deregistration and replacement rates.

## Overview

This tool monitors Bittensor subnet metagraphs over time to identify which subnets have the most competitive mining pools. Competition is measured by tracking how frequently UIDs change ownership (hotkeys), which indicates miners being deregistered and replaced by new registrants.

## Prerequisites

- Python 3.14+
- `uv` package manager
- Access to a Bittensor network (default: finney)

## Technical Details

This tool uses the **Bittensor SDK** (`bittensor` Python package) for direct network access, providing:
- Faster data retrieval compared to CLI subprocess calls
- Direct access to metagraph objects and their attributes
- Native Python integration with proper type hints
- More efficient resource usage

## Installation

The project is managed with `uv` and uses the Bittensor SDK for direct network access.

```bash
cd subnet-competition-tracker
uv sync
```

This will install all dependencies including `bittensor>=10.0.1`.

## Usage

### 1. Take a Snapshot

Capture the current state of all subnet metagraphs:

```bash
uv run main.py snapshot
```

This will:
- Connect to the Bittensor network using the SDK
- Query all subnet netuids via `subtensor.get_all_subnets_netuid()`
- For each subnet, fetch the metagraph data via `subtensor.metagraph(netuid)`
- Extract UID-to-hotkey mappings from metagraph objects
- Save a timestamped snapshot in the `snapshots/` directory

### 2. Analyze Competition

After collecting multiple snapshots over time, analyze the competition:

```bash
# Default: sort by replacements per period
uv run main.py analyze

# Sort by replacement percentage
uv run main.py analyze --sort-by percentage

# Sort by deregistrations per period
uv run main.py analyze --sort-by deregistrations

# Sort by total changes per period (replacements + deregistrations + new registrations)
uv run main.py analyze --sort-by changes
```

**Sorting Options:**
- `replacements` (default) - Subnets with most UID replacements per period
- `percentage` - Subnets with highest % of UIDs replaced
- `deregistrations` - Subnets with most deregistrations (miners losing slots)
- `changes` - Subnets with most total activity (all types of changes)

This will:
- Load all snapshots from the `snapshots/` directory
- Compare consecutive snapshots to detect changes
- Calculate competition metrics per subnet
- Display a ranked list with:
  - **Repl.**: Average replacements per snapshot period
  - **Dereg.**: Average deregistrations per snapshot period
  - **% Repl.**: Percentage of UIDs that were replaced per period
  - **Total Repl.**: Total replacements across all periods
  - **Total Dereg.**: Total deregistrations across all periods
  - **Avg UIDs**: Average number of UIDs in the subnet
  - **Periods**: Number of snapshot comparison periods analyzed

### 3. Compare Two Snapshots

Compare two specific snapshots to see detailed changes:

```bash
uv run main.py compare --snapshot1 snapshots/snapshot_2024-01-07T10-00-00.json --snapshot2 snapshots/snapshot_2024-01-07T11-00-00.json
```

### Options

- `--data-dir DIR`: Specify custom directory for snapshots (default: `snapshots`)
- `--network NETWORK`: Specify Bittensor network (default: `finney`)

## How It Works

### Competition Metrics

The tool tracks three types of events:

1. **Replacements**: When a UID exists in both snapshots but the hotkey changed
   - Indicates a miner was deregistered and immediately replaced
   - Primary metric for competition

2. **Deregistrations**: When a UID exists in old snapshot but not in new
   - Indicates a miner lost their slot

3. **New Registrations**: When a UID exists in new snapshot but not in old
   - Indicates a new miner joined

### Competition Score

The competition score is calculated as:

```
Competition Score = Total Replacements / Number of Time Periods
```

Higher scores indicate more competitive subnets where miners are frequently being pushed out.

## Example Workflow

```bash
# Take initial snapshot
uv run main.py snapshot

# Wait some time (e.g., 1 hour, 1 day)
# Take another snapshot
uv run main.py snapshot

# Repeat several times to build historical data

# Analyze competition across all snapshots
uv run main.py analyze
```

### Example Output

```
==================================================================================================================================
SUBNET COMPETITION RANKING
(Sorted by: percentage)
==================================================================================================================================

Rank   Netuid   Repl.    Dereg.   % Repl.    Total Repl.  Total Dereg. Avg UIDs   Periods
----------------------------------------------------------------------------------------------------------------------------------
1      1        123.00   0.00     48.05      246          0            256        2
2      68       29.00    0.00     45.31      58           0            64         2
3      83       58.00    0.00     22.66      116          0            256        2
4      21       48.00    0.00     18.75      96           0            256        2
5      92       38.00    0.00     18.27      76           0            208        2
...

==================================================================================================================================
Most competitive subnet (by percentage): Netuid 1 - Replacements: 123.00/period, Deregistrations: 0.00/period, 48.1% replaced
==================================================================================================================================
```

**Interpretation:**
- **Subnet 1**: Most competitive - 48% of all UIDs were replaced per period (123 replacements/period)
- **Subnet 68**: 45% replacement rate but smaller subnet (64 UIDs vs 256)
- **Subnet 83**: High absolute replacements (58/period) = 23% of the subnet

## Data Storage

Snapshots are stored as JSON files in the `snapshots/` directory with the following structure:

```json
{
  "timestamp": "2024-01-07T10:00:00",
  "network": "finney",
  "subnets": {
    "1": {
      "uid_hotkey_map": {
        "0": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        "1": "5HEo565WAy4Dbq3Sv271SAi7syBSofyfhhwRNjFNSM9UnrKT",
        ...
      },
      "n_neurons": 256,
      "block": 1234567
    },
    ...
  }
}
```

## Automated Monitoring

To run continuous monitoring, set up a cron job or systemd timer:

```bash
# Example: Take a snapshot every hour
0 * * * * cd /path/to/subnet-competition-tracker && uv run main.py snapshot
```

## Notes

- The tool requires at least 2 snapshots to perform analysis
- More snapshots over longer time periods provide more accurate competition metrics
- Snapshot data can be large depending on the number of subnets and UIDs
- Uses the Bittensor SDK directly for efficient network access
- First connection to the network may take a few moments to establish
