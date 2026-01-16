# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains **Bittensor network tools** including subnet analysis and a proof-of-concept mining operation deployment system.

### Project 1: Subnet Competition Tracker

Located in `subnet-competition-tracker/`, this tool analyzes Bittensor subnet mining pool competition by tracking deregistration and replacement rates over time.

**Core Concept:** Competition is measured by how frequently UIDs change ownership (hotkeys), indicating miners being pushed out and replaced by new registrants.

### Project 2: Chutes Miner

Located in `chutes-miner/`, this is a **proof-of-concept implementation** for deploying mining operations on Bittensor's Chutes subnet (netuid 64). Chutes is a permissionless, serverless, AI-centric compute platform where miners provide GPU compute resources.

**Core Concept:** Provide GPU compute for AI workloads, optimizing for cold start times and total compute time to maximize incentives. Mining on Chutes requires running containerized AI applications (called "chutes") on your GPU infrastructure.

---

## SUBNET COMPETITION TRACKER

### Setup and Dependencies

```bash
cd subnet-competition-tracker
uv sync
```

### Taking Snapshots

Capture current state of all subnet metagraphs:

```bash
uv run main.py snapshot
```

This connects to Bittensor network via SDK, queries all subnets, extracts UID-to-hotkey mappings, and saves timestamped JSON in `snapshots/`.

### Analyzing Competition

After collecting multiple snapshots over time:

```bash
# Default: sort by replacements per period
uv run main.py analyze

# Sort by replacement percentage
uv run main.py analyze --sort-by percentage

# Sort by deregistrations
uv run main.py analyze --sort-by deregistrations

# Sort by total changes (replacements + deregistrations + new registrations)
uv run main.py analyze --sort-by changes
```

### Comparing Two Snapshots

```bash
uv run main.py compare \
  --snapshot1 snapshots/snapshot_2024-01-07T10-00-00.json \
  --snapshot2 snapshots/snapshot_2024-01-07T11-00-00.json
```

### Registration Cost Analysis

```bash
# Run all examples (compares costs across competitive subnets)
uv run examples.py

# Get cost for a specific subnet
uv run python3 -c "
from examples import estimate_registration_usd
estimate_registration_usd(netuid=1, tao_price_usd=50.0)
"

# Compare specific subnets
uv run python3 -c "
from examples import compare_registration_costs
compare_registration_costs([1, 83, 21, 68, 38])
"

# Export all subnet costs as CSV
uv run python3 -c "
from examples import get_all_subnet_costs
get_all_subnet_costs(output_csv=True)
" > subnet_costs.csv
```

### Architecture - Subnet Competition Tracker

#### main.py - SubnetCompetitionTracker

**Core Class:** `SubnetCompetitionTracker`

**Key Methods:**
- `take_snapshot()` - Captures current state of all subnet metagraphs via Bittensor SDK
- `analyze_competition()` - Compares consecutive snapshots, calculates competition metrics
- `compare_snapshots()` - Diffs two snapshots to detect replacements, deregistrations, new registrations
- `print_competition_ranking()` - Outputs ranked subnets by competition level

**Data Flow:**
1. SDK connection via `bittensor.Subtensor(network="finney")`
2. Query all subnets: `subtensor.get_all_subnets_netuid()`
3. For each subnet: `subtensor.metagraph(netuid)`
4. Extract UID→hotkey mappings from metagraph objects
5. Store in JSON snapshots with timestamp, network, and subnet data

#### Competition Metrics

**Three Event Types Tracked:**
1. **Replacements** - UID exists in both snapshots but hotkey changed (primary competition metric)
2. **Deregistrations** - UID exists in old snapshot only (miner lost slot)
3. **New Registrations** - UID exists in new snapshot only (new miner joined)

**Metrics Calculated:**
- Average replacements per snapshot period
- Average deregistrations per period
- Replacement percentage (% of UIDs replaced per period)
- Total replacements/deregistrations across all periods
- Average UID count per subnet

#### examples.py - Registration Cost Analysis

**Functions:**
- `get_registration_cost(netuid)` - Fetches burn cost and subnet info via SDK
- `compare_registration_costs(netuids)` - Multi-subnet cost comparison
- `estimate_registration_usd(netuid, tao_price_usd)` - USD cost calculator
- `get_all_subnet_costs()` - Cost data for all subnets (CSV or formatted table)

**Uses:** `subtensor.get_subnet_info(netuid)` to access `info.burn` (registration cost)

#### Data Storage

**Snapshot Format:**
```json
{
  "timestamp": "2024-01-07T10:00:00",
  "network": "finney",
  "subnets": {
    "1": {
      "uid_hotkey_map": {"0": "5C4hrfjw9DjX...", "1": "5HEo565WAy4D..."},
      "n_neurons": 256,
      "block": 1234567
    }
  }
}
```

Stored in `snapshots/` directory with timestamp in filename.

### Technical Details - Subnet Competition Tracker

#### Bittensor SDK Integration

This project uses **direct SDK access** (not CLI subprocesses) for:
- Faster data retrieval
- Direct metagraph object access
- Native Python integration with type hints
- Efficient resource usage

**Key SDK Objects:**
- `bt.Subtensor` - Network connection
- `metagraph.uids` - List of UIDs (aligned by index with hotkeys)
- `metagraph.hotkeys` - List of hotkey addresses
- `SubnetInfo.burn` - Registration burn cost (Balance object, e.g., "τ0.004396")

#### Requirements

- Python 3.14+
- `uv` package manager
- Bittensor SDK (`bittensor>=10.0.1`)
- Network access to Bittensor finney (default) or testnet

### Key Insights - Subnet Competition Tracker

#### Competition Analysis Workflow

Requires at least 2 snapshots. Best practice:
1. Take initial snapshot
2. Wait time period (e.g., 1 hour, 1 day)
3. Take another snapshot
4. Repeat several times
5. Run analysis across all snapshots

More snapshots over longer periods = more accurate competition metrics.

#### Cost vs Competition Pattern

**Low cost ≠ always high competition**

Actual pattern: `Competition = Interest / (Cost + Subnet_Quality)`

Examples:
- Subnet 1: τ0.0044 ($0.22) → 48% replacement (extreme competition)
- Subnet 83: τ0.0323 ($1.62) → 23% replacement (high but stable)
- Subnet 38: τ0.0514 ($2.57) → 2.7% replacement + 97% empty (collapsed subnet)

High cost can signal either "quality subnet with high barriers" OR "dead subnet with historical activity."

#### UID Tracking Implementation

Metagraphs have aligned lists: `metagraph.uids[i]` corresponds to `metagraph.hotkeys[i]`. Extract via:

```python
for i, uid in enumerate(metagraph.uids):
    hotkey = metagraph.hotkeys[i]
    mapping[int(uid.item())] = str(hotkey)
```

`.item()` converts torch tensors to Python scalars.

---

## CHUTES MINER (Proof of Concept)

**IMPORTANT:** This is proof-of-concept code for deploying mining operations on Bittensor subnet 64 (Chutes). The goal is to provide GPU compute for AI workloads, optimizing for cold start times and total compute efficiency.

### Mining Concept

**Incentive Model:**
- Rewards based on total compute time provided to the network
- Bounties for being first to provide inference on new applications
- 7-day rolling window for weight calculations (requires patience and stability)
- Never register more than one UID per miner (adds capacity instead of competing with yourself)

**GPU Strategy:**
- Run diverse GPU types: cheap (T4, A5000, A10) to powerful (8x H100 nodes)
- RAM requirement: Must have ≥ VRAM per GPU (e.g., 4x A40 @ 48GB VRAM = 192GB RAM minimum)
- Storage considerations: Ensure adequate space under `/var/snap` for HuggingFace cache and images

### Development Commands - Chutes Miner

#### Local Development Setup

```bash
cd chutes-miner

# Create shared virtual environment for all packages
make venv

# Activate environment
source .venv/bin/activate

# List all packages in monorepo
make list-packages

# Run tests locally (fast)
make test-local

# Run linting
make lint-local

# Format code
make reformat
```

#### Docker Development

```bash
# Build all package images
make build

# Build specific package
make build chutes-miner

# Build standalone images (cache-cleaner, etc.)
make images

# Tag images for Docker Hub
make tag

# Run full CI pipeline locally
make ci
```

#### Chutes Miner API Development

```bash
cd docker/chutes-miner

# Start PostgreSQL and Redis
docker compose up -d postgres redis

# Run API server
docker compose up api

# Seed database with test data
docker compose run --rm db-seed
```

API available at `http://localhost:8080`.

### Infrastructure Setup (Production)

#### Prerequisites

**Server Requirements:**
- Bare metal or VM (NOT Runpod/Vast)
- Static, dedicated IPs (1:1 port mapping, no shared/dynamic IPs)
- Ubuntu 22.04 (recommended, no pre-installed NVIDIA drivers)
- One non-GPU server: 4 cores, 32GB RAM (runs k3s, postgres, redis, gepetto, API)
- GPU servers: As many as desired with [supported GPUs](https://github.com/rayonlabs/chutes-api/blob/main/api/gpu.py)

**Networking Requirements:**
- Disable firewalls OR configure:
  - All traffic between inventory nodes (all ports/protocols)
  - Kubernetes ephemeral port range (30000-32767) on GPU nodes (public)
  - API nodePort access (default: 32000) from management machine

**Storage Setup:**
- Check primary storage mount location before provisioning
- May need bind mount to `/var/snap` (e.g., latitude.sh uses `/home`, hyperstack uses `/ephemeral`)

```bash
# Example bind mount if needed
rsync -azv /var/snap/ /home/snap/
echo '/home/snap /var/snap none bind 0 0' >> /etc/fstab
mount -a
```

#### Configuration

**1. Local Configuration Setup**

```bash
mkdir ~/chutes
touch ~/chutes/inventory.yml
touch ~/chutes/values.yaml
```

**2. Define Inventory** (`~/chutes/inventory.yml`)

Copy from `ansible/k3s/inventory.yml` and customize:

```yaml
all:
  children:
    control:
      hosts:
        chutes-miner-cpu-0:
          ansible_host: 1.0.0.0
    workers:
      hosts:
        chutes-miner-gpu-0:
          ansible_host: 1.0.0.1
        chutes-miner-gpu-1:
          ansible_host: 1.0.0.2
  vars:
    ansible_user: ubuntu
    ansible_ssh_private_key_file: ~/.ssh/key.pem
    ssh_keys:
      - "ssh-rsa AAAAB... user@domain.com"
    user: yourusername
    hotkey_path: "~/.bittensor/wallets/[WALLET]/hotkeys/[HOTKEY]"
    chart_values: "~/chutes/values.yaml"
    grafana_password: <REPLACE_ME>
```

**3. Set Chart Values** (`~/chutes/values.yaml`)

```yaml
cache:
  max_age_days: 30
  max_size_gb: 850
  overrides:
    # Per-node cache size overrides (GB)
    # chutes-miner-gpu-0: 1000
```

**4. Install Ansible**

```bash
# Mac
brew install ansible

# Ubuntu/Debian
sudo apt -y update && sudo apt -y install ansible python3-pip

# Install collections
ansible-galaxy collection install community.general kubernetes.core ansible.posix
```

**5. Bootstrap Infrastructure**

From `chutes-miner/ansible/k3s/`:

```bash
ansible-playbook -i ~/chutes/inventory.yml playbooks/site.yml
```

**6. Configure Gepetto Strategy**

Gepetto is the core optimization component. Customize `src/chutes-miner/chutes_miner/gepetto.py` for your strategy (chute selection, scaling, bounties).

Create ConfigMap:

```bash
cd src/chutes-miner/chutes_miner
kubectl create configmap gepetto-code --context chutes-miner-cpu-0 --from-file=gepetto.py -n chutes
```

Update after changes:

```bash
kubectl create configmap gepetto-code --from-file=gepetto.py -o yaml --dry-run=client | kubectl apply --context chutes-miner-cpu-0 -n chutes -f -
kubectl rollout restart deployment/gepetto --context chutes-miner-cpu-0 -n chutes
```

**7. Register on Subnet 64**

```bash
btcli subnet register --netuid 64 --wallet.name [COLDKEY] --wallet.hotkey [HOTKEY]
```

**Do NOT announce an axon** - all communication via websocket connections.

**8. Add GPU Nodes to Miner**

Install CLI (auto-installed on control node):

```bash
pip install chutes-miner-cli
```

For each GPU node:

```bash
chutes-miner add-node \
  --name [SERVER_NAME_FROM_INVENTORY] \
  --validator [VALIDATOR_HOTKEY] \
  --hourly-cost [HOURLY_COST_PER_GPU] \
  --gpu-short-ref [GPU_TYPE] \
  --hotkey ~/.bittensor/wallets/[WALLET]/hotkeys/[HOTKEY] \
  --agent-api http://[GPU_NODE_IP]:32000 \
  --miner-api http://[CPU_NODE_IP]:32000
```

#### Adding Servers Post-Deployment

Update `~/chutes/inventory.yml`, then:

```bash
ansible-playbook -i ~/chutes/inventory.yml playbooks/site.yml --tags add-nodes
chutes-miner add-node ...  # Run for new node
```

#### Chart Updates

```bash
# Update all charts
ansible-playbook -i ~/chutes/inventory.yml playbooks/deploy-charts.yml

# Update specific charts
ansible-playbook -i ~/chutes/inventory.yml playbooks/deploy-charts.yml --tags miner-charts
ansible-playbook -i ~/chutes/inventory.yml playbooks/deploy-charts.yml --tags miner-gpu-charts
ansible-playbook -i ~/chutes/inventory.yml playbooks/deploy-charts.yml --tags monitoring-charts
```

#### Restart Kubernetes Resources

```bash
ansible-playbook -i ~/chutes/inventory.yml playbooks/restart-k8s.yml
```

### Architecture - Chutes Miner

#### Monorepo Structure

```
src/
├── chutes-common/       # Shared utilities and types
├── chutes-miner/        # Main miner API and Gepetto
├── chutes-miner-cli/    # CLI for node management
├── chutes-agent/        # Agent running on GPU nodes
├── chutes-monitor/      # Monitoring components
├── chutes-registry/     # Docker registry proxy
└── graval-bootstrap/    # GPU validation bootstrap

charts/
├── chutes-miner/        # Helm charts for API/core components
├── chutes-miner-gpu/    # Helm charts for GPU node components
└── chutes-monitoring/   # Helm charts for monitoring stack

ansible/k3s/             # Ansible automation for k3s provisioning
docker/                  # Docker configs per package
tests/                   # Tests organized by package
```

#### Key Components

**PostgreSQL**
- Tracks all servers, GPUs, deployments via SQLAlchemy
- Deployed with host volume in kubernetes cluster
- Auto-configured by helm charts

**Redis**
- Pubsub for event coordination (chute added/removed, GPU added, etc.)
- Triggers event handlers across miner components
- Auto-configured by helm charts

**GraVal Bootstrap**
- Custom C/CUDA library for GPU validation: https://github.com/rayonlabs/graval
- Uses matrix multiplications seeded by device info to verify GPU authenticity
- VRAM capacity test: 95% of total VRAM must be available
- Encrypts traffic with keys only decryptable by advertised GPU
- Runs automatically when nodes join cluster and when chutes deploy

**Registry Proxy**
- Nginx-based proxy on each miner for private Docker images
- Injects Bittensor key signatures for authentication
- Images appear as: `[validator_hotkey].localregistry.chutes.ai:30500/[user]/[image]:[tag]`
- Subdomain points to 127.0.0.1 → NodePort routing to local registry service
- Nginx auth subrequest to miner API (see `charts/chutes-miner-gpu/templates/registry-cm.yaml`)
- Miner API injects signatures (see `src/chutes-miner/.../registry/router.py`)
- Proxies to validator registry with validated signatures

**Miner API**
- Server/inventory management
- Websocket connection to validator API
- Docker registry authentication
- Runs on CPU node (port 32000 default)
- Auto-deployed via helm charts

**Gepetto** 🧙‍♂️
- **Most critical component for optimization**
- Provisions, scales, deletes chutes (containerized AI apps)
- Attempts to claim bounties (first inference rewards)
- Strategy directly impacts total compute time and rewards
- Customize in `src/chutes-miner/chutes_miner/gepetto.py`
- Deployed as ConfigMap, runs on CPU node

**Agent**
- Runs on each GPU node
- Manages local chute deployments
- Communicates with miner API
- Handles GraVal validation
- Deployed via `chutes-miner-gpu` helm chart

#### Data Flow

1. **Validator** sends chute requests via websocket → **Miner API**
2. **Gepetto** selects optimal servers/GPUs based on cost, availability, strategy
3. **Miner API** signals **Agent** on selected GPU node
4. **Agent** pulls image via **Registry Proxy** (with Bittensor auth)
5. **GraVal** validates GPU and calculates decryption keys
6. Chute deployed on GPU, handles inference requests
7. Compute time tracked, incentives calculated over 7-day window

#### Important Technical Notes

**GPU Node Networking:**
- Each GPU node is standalone k3s cluster (not joined to main cluster)
- Validator sends traffic directly to GPU nodes (not routed through CPU node)
- Requires public, dedicated IPv4 (not private ranges like 192.168.x.x or 10.x.x.x)
- Egress and ingress must use same IP (no NAT with different source IP)

**Kubernetes Setup:**
- Uses k3s (lightweight Kubernetes) via Ansible automation
- CPU node: control plane + API + Gepetto + PostgreSQL + Redis
- GPU nodes: standalone clusters running chute workloads
- NodePort services for public chute access (30000-32767 range)

**Context Management:**
- `ktx`: Switch between kubernetes contexts
- `kns`: Switch between kubernetes namespaces
- Contexts: `chutes-miner-cpu-0` (control), `chutes-miner-gpu-X` (GPU nodes)
- Kubeconfig authoritative location: `/etc/rancher/k3s/k3s.yaml`

**Monitoring:**
- Grafana available at `http://[CONTROL_NODE_IP]:30080`
- Default dashboards provided
- Metrics federated from GPU clusters to control plane Prometheus

### Key Development Insights - Chutes Miner

**Optimization Focus:**
- Customize Gepetto strategy for maximum compute time
- Balance cost efficiency (hourly GPU cost) vs. availability
- Optimize cold start times (model caching, image pre-pulling)
- Strategic bounty claiming (first inference bonuses)

**Common Pitfalls:**
- Insufficient RAM relative to VRAM → deployment failures
- Storage not mounted under `/var/snap` → cache issues
- Shared/dynamic IPs → validation failures
- Registering multiple UIDs → self-competition (DON'T DO THIS)
- Insufficient patience (7-day window for rewards)

**Testing Strategy:**
- Use `make test-local` for fast iteration during development
- Use `make test` for Docker-based CI environment matching
- 90% code coverage target (enforced locally)
- Add tests for all code changes

**Monorepo Development:**
- Single shared `.venv` for all packages (manage dependencies carefully)
- Target specific packages: `make <command> <package-name>`
- Tag images for Docker Hub: `make tag`
- Run full CI: `make ci`