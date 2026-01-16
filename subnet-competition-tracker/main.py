#!/usr/bin/env python3
"""
Subnet Competition Tracker

Tracks deregistrations and replacements across Bittensor subnets to identify
the most competitive mining pools. Competition is measured by how frequently
UIDs change ownership (hotkeys).
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
from collections import defaultdict

if TYPE_CHECKING:
    import bittensor as bt


class SubnetCompetitionTracker:
    """Tracks and analyzes subnet competition based on deregistrations/replacements."""

    def __init__(self, data_dir: str = "snapshots", network: str = "finney"):
        """
        Initialize the tracker.

        Args:
            data_dir: Directory to store snapshot data
            network: Bittensor network to monitor (default: finney)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.network = network
        self.subtensor = None

    def connect(self):
        """Connect to the Bittensor network."""
        if self.subtensor is None:
            import bittensor as bt
            print(f"Connecting to {self.network} network...")
            self.subtensor = bt.Subtensor(network=self.network)
            print(f"Connected to {self.subtensor.network}")

    def get_all_subnet_ids(self) -> List[int]:
        """
        Fetch all subnet IDs from the network.

        Returns:
            List of subnet netuid values
        """
        try:
            self.connect()
            netuids = self.subtensor.get_all_subnets_netuid()
            return netuids
        except Exception as e:
            print(f"Failed to get subnet IDs: {e}", file=sys.stderr)
            return []

    def get_subnet_metagraph(self, netuid: int) -> Optional[object]:
        """
        Fetch metagraph data for a specific subnet.

        Args:
            netuid: The subnet netuid

        Returns:
            Metagraph object, or None on error
        """
        try:
            self.connect()
            metagraph = self.subtensor.metagraph(netuid=netuid)
            return metagraph
        except Exception as e:
            print(f"Failed to get metagraph for subnet {netuid}: {e}", file=sys.stderr)
            return None

    def extract_uid_hotkey_mapping(self, metagraph: object) -> Dict[int, str]:
        """
        Extract UID to hotkey mapping from metagraph.

        Args:
            metagraph: Bittensor metagraph object

        Returns:
            Dictionary mapping UID to hotkey address
        """
        mapping = {}

        # Metagraph has lists: .uids and .hotkeys that are aligned by index
        for i, uid in enumerate(metagraph.uids):
            hotkey = metagraph.hotkeys[i]
            mapping[int(uid.item())] = str(hotkey)

        return mapping

    def take_snapshot(self) -> str:
        """
        Take a snapshot of all subnet metagraphs.

        Returns:
            Path to the snapshot file
        """
        timestamp = datetime.now().isoformat()
        snapshot = {
            "timestamp": timestamp,
            "network": self.network,
            "subnets": {}
        }

        print(f"Taking snapshot at {timestamp}...")
        subnet_ids = self.get_all_subnet_ids()
        print(f"Found {len(subnet_ids)} subnets")

        for netuid in subnet_ids:
            if netuid is None:
                continue
            print(f"  Fetching subnet {netuid}...", end=" ", flush=True)
            metagraph = self.get_subnet_metagraph(netuid)
            if metagraph:
                uid_mapping = self.extract_uid_hotkey_mapping(metagraph)

                # Store basic metadata as well
                snapshot["subnets"][str(netuid)] = {
                    "uid_hotkey_map": uid_mapping,
                    "n_neurons": len(metagraph.uids),
                    "block": metagraph.block.item() if hasattr(metagraph.block, 'item') else int(metagraph.block)
                }
                print(f"✓ ({len(uid_mapping)} UIDs)")
            else:
                print("✗ (failed)")

        # Save snapshot
        snapshot_file = self.data_dir / f"snapshot_{timestamp.replace(':', '-')}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)

        print(f"\nSnapshot saved to {snapshot_file}")
        return str(snapshot_file)

    def load_snapshot(self, filepath: str) -> Dict:
        """Load a snapshot from file."""
        with open(filepath, 'r') as f:
            return json.load(f)

    def get_all_snapshots(self) -> List[Path]:
        """Get all snapshot files sorted by timestamp."""
        snapshots = list(self.data_dir.glob("snapshot_*.json"))
        return sorted(snapshots)

    def compare_snapshots(self, old_snapshot: Dict, new_snapshot: Dict) -> Dict[str, Dict]:
        """
        Compare two snapshots to detect deregistrations and replacements.

        Args:
            old_snapshot: Earlier snapshot
            new_snapshot: Later snapshot

        Returns:
            Dictionary mapping netuid to change statistics
        """
        changes = {}

        old_subnets = old_snapshot.get("subnets", {})
        new_subnets = new_snapshot.get("subnets", {})

        # Check all subnets that exist in both snapshots
        for netuid in set(old_subnets.keys()) | set(new_subnets.keys()):
            old_mapping = old_subnets.get(netuid, {}).get("uid_hotkey_map", {})
            new_mapping = new_subnets.get(netuid, {}).get("uid_hotkey_map", {})

            # Convert string keys to int for comparison
            old_mapping = {int(k): v for k, v in old_mapping.items()}
            new_mapping = {int(k): v for k, v in new_mapping.items()}

            # Find UIDs where hotkey changed (deregistration + replacement)
            replacements = []
            new_registrations = []
            deregistrations = []

            for uid in set(old_mapping.keys()) | set(new_mapping.keys()):
                old_hotkey = old_mapping.get(uid)
                new_hotkey = new_mapping.get(uid)

                if old_hotkey and new_hotkey and old_hotkey != new_hotkey:
                    # UID exists in both but hotkey changed = replacement
                    replacements.append({
                        "uid": uid,
                        "old_hotkey": old_hotkey,
                        "new_hotkey": new_hotkey
                    })
                elif old_hotkey and not new_hotkey:
                    # UID was in old but not new = deregistration (no replacement yet)
                    deregistrations.append({"uid": uid, "hotkey": old_hotkey})
                elif new_hotkey and not old_hotkey:
                    # UID in new but not old = new registration
                    new_registrations.append({"uid": uid, "hotkey": new_hotkey})

            if replacements or new_registrations or deregistrations:
                changes[netuid] = {
                    "replacements": replacements,
                    "new_registrations": new_registrations,
                    "deregistrations": deregistrations,
                    "total_changes": len(replacements) + len(new_registrations) + len(deregistrations),
                    "replacement_count": len(replacements),
                    "total_uids_old": len(old_mapping),
                    "total_uids_new": len(new_mapping)
                }

        return changes

    def analyze_competition(self, min_snapshots: int = 2) -> Dict:
        """
        Analyze competition across all snapshots.

        Args:
            min_snapshots: Minimum number of snapshots required for analysis

        Returns:
            Analysis results with competition metrics per subnet
        """
        snapshots = self.get_all_snapshots()

        if len(snapshots) < min_snapshots:
            print(f"Need at least {min_snapshots} snapshots for analysis. Found {len(snapshots)}.")
            return {}

        print(f"\nAnalyzing {len(snapshots)} snapshots...")

        # Aggregate changes across all snapshot pairs
        subnet_stats = defaultdict(lambda: {
            "total_replacements": 0,
            "total_new_registrations": 0,
            "total_deregistrations": 0,
            "total_changes": 0,
            "time_periods": 0,
            "total_uids": 0,
            "uid_samples": 0
        })

        for i in range(len(snapshots) - 1):
            old_snap = self.load_snapshot(snapshots[i])
            new_snap = self.load_snapshot(snapshots[i + 1])

            changes = self.compare_snapshots(old_snap, new_snap)

            for netuid, change_data in changes.items():
                stats = subnet_stats[netuid]
                stats["total_replacements"] += change_data["replacement_count"]
                stats["total_new_registrations"] += len(change_data["new_registrations"])
                stats["total_deregistrations"] += len(change_data["deregistrations"])
                stats["total_changes"] += change_data["total_changes"]
                stats["time_periods"] += 1

                # Track average UIDs for percentage calculation
                stats["total_uids"] += change_data.get("total_uids_new", 0)
                stats["uid_samples"] += 1

        # Calculate competition scores
        results = {}
        for netuid, stats in subnet_stats.items():
            # Competition score = replacements per time period
            # Higher score = more competitive
            competition_score = stats["total_replacements"] / stats["time_periods"] if stats["time_periods"] > 0 else 0
            avg_uids = stats["total_uids"] / stats["uid_samples"] if stats["uid_samples"] > 0 else 1
            replacement_percentage = (stats["total_replacements"] / (stats["time_periods"] * avg_uids) * 100) if avg_uids > 0 and stats["time_periods"] > 0 else 0

            results[netuid] = {
                **stats,
                "competition_score": competition_score,
                "avg_replacements_per_period": competition_score,
                "avg_deregistrations_per_period": stats["total_deregistrations"] / stats["time_periods"] if stats["time_periods"] > 0 else 0,
                "avg_total_changes_per_period": stats["total_changes"] / stats["time_periods"] if stats["time_periods"] > 0 else 0,
                "avg_uids": avg_uids,
                "replacement_percentage": replacement_percentage
            }

        return results

    def print_competition_ranking(self, results: Dict, sort_by: str = "replacements"):
        """
        Print subnet competition ranking.

        Args:
            results: Analysis results from analyze_competition()
            sort_by: Field to sort by (replacements, deregistrations, percentage, changes)
        """
        if not results:
            print("No competition data available.")
            return

        # Determine sort key based on parameter
        sort_keys = {
            "replacements": "competition_score",
            "deregistrations": "avg_deregistrations_per_period",
            "percentage": "replacement_percentage",
            "changes": "avg_total_changes_per_period"
        }
        sort_key = sort_keys.get(sort_by, "competition_score")

        # Sort by selected metric (descending)
        ranked = sorted(
            results.items(),
            key=lambda x: x[1][sort_key],
            reverse=True
        )

        print("\n" + "="*130)
        print("SUBNET COMPETITION RANKING")
        print(f"(Sorted by: {sort_by})")
        print("="*130)
        print()
        print(f"{'Rank':<6} {'Netuid':<8} {'Repl.':<8} {'Dereg.':<8} {'% Repl.':<10} "
              f"{'Total Repl.':<12} {'Total Dereg.':<12} {'Avg UIDs':<10} {'Periods':<10}")
        print("-"*130)

        for rank, (netuid, stats) in enumerate(ranked, 1):
            print(f"{rank:<6} {netuid:<8} "
                  f"{stats['avg_replacements_per_period']:<8.2f} "
                  f"{stats['avg_deregistrations_per_period']:<8.2f} "
                  f"{stats['replacement_percentage']:<10.2f} "
                  f"{stats['total_replacements']:<12} "
                  f"{stats['total_deregistrations']:<12} "
                  f"{stats['avg_uids']:<10.0f} "
                  f"{stats['time_periods']:<10}")

        print()
        print("="*130)
        top_netuid = ranked[0][0]
        top_stats = ranked[0][1]
        print(f"Most competitive subnet (by {sort_by}): Netuid {top_netuid} - "
              f"Replacements: {top_stats['avg_replacements_per_period']:.2f}/period, "
              f"Deregistrations: {top_stats['avg_deregistrations_per_period']:.2f}/period, "
              f"{top_stats['replacement_percentage']:.1f}% replaced")
        print("="*130)


def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Track and analyze Bittensor subnet competition",
        add_help=True
    )
    parser.add_argument(
        "command",
        choices=["snapshot", "analyze", "compare"],
        help="Command to run"
    )
    parser.add_argument(
        "--data-dir",
        default="snapshots",
        help="Directory to store snapshots (default: snapshots)"
    )
    parser.add_argument(
        "--network",
        default="finney",
        help="Bittensor network (default: finney)"
    )
    parser.add_argument(
        "--snapshot1",
        help="First snapshot file for comparison"
    )
    parser.add_argument(
        "--snapshot2",
        help="Second snapshot file for comparison"
    )
    parser.add_argument(
        "--sort-by",
        choices=["replacements", "deregistrations", "percentage", "changes"],
        default="replacements",
        help="Sort analysis by: replacements (default), deregistrations, percentage, or total changes"
    )

    # Parse only known args to avoid conflicts with bittensor's internal args
    args, unknown = parser.parse_known_args()

    tracker = SubnetCompetitionTracker(
        data_dir=args.data_dir,
        network=args.network
    )

    if args.command == "snapshot":
        tracker.take_snapshot()

    elif args.command == "analyze":
        results = tracker.analyze_competition()
        tracker.print_competition_ranking(results, sort_by=args.sort_by)

    elif args.command == "compare":
        if not args.snapshot1 or not args.snapshot2:
            print("Error: --snapshot1 and --snapshot2 required for compare command")
            sys.exit(1)

        old_snap = tracker.load_snapshot(args.snapshot1)
        new_snap = tracker.load_snapshot(args.snapshot2)
        changes = tracker.compare_snapshots(old_snap, new_snap)

        print("\n" + "="*80)
        print("SNAPSHOT COMPARISON")
        print("="*80)
        print(f"Old: {old_snap['timestamp']}")
        print(f"New: {new_snap['timestamp']}")
        print()

        for netuid, change_data in sorted(changes.items()):
            print(f"Subnet {netuid}:")
            print(f"  Replacements: {change_data['replacement_count']}")
            print(f"  New registrations: {len(change_data['new_registrations'])}")
            print(f"  Deregistrations: {len(change_data['deregistrations'])}")
            print()


if __name__ == "__main__":
    main()
