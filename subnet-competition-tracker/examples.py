#!/usr/bin/env python3
"""
Examples: How to Find and Interpret Registration Costs

This script demonstrates various ways to query and analyze subnet
registration costs using the Bittensor SDK.
"""

import sys
import bittensor as bt


def get_registration_cost(netuid: int, network: str = "finney") -> dict:
    """
    Get registration cost and related info for a subnet.

    Args:
        netuid: The subnet netuid
        network: Bittensor network (default: finney)

    Returns:
        Dictionary with cost and subnet information
    """
    st = bt.Subtensor(network=network)
    info = st.get_subnet_info(netuid=netuid)

    # Parse burn cost (comes as Balance object like "τ0.004396")
    cost_tao = float(str(info.burn).replace('τ', ''))

    return {
        "netuid": netuid,
        "burn_cost_tao": cost_tao,
        "burn_cost_alpha": info.burn,  # Original Balance object
        "max_neurons": info.max_n,
        "current_neurons": info.subnetwork_n,
        "occupancy_percent": (info.subnetwork_n / info.max_n * 100) if info.max_n > 0 else 0,
        "is_full": info.subnetwork_n >= info.max_n,
        "difficulty": info.difficulty,
        "immunity_period_blocks": info.immunity_period,
        "tempo": info.tempo
    }


def compare_registration_costs(netuids: list, network: str = "finney"):
    """
    Compare registration costs across multiple subnets.

    Args:
        netuids: List of subnet netuids to compare
        network: Bittensor network (default: finney)
    """
    print("="*100)
    print("SUBNET REGISTRATION COST COMPARISON")
    print("="*100)
    print()

    print(f"{'Netuid':<8} {'Cost (τ)':<15} {'Cost (α)':<20} {'Slots':<15} "
          f"{'Full':<6} {'Difficulty':<15}")
    print("-"*100)

    costs = []
    for netuid in netuids:
        info = get_registration_cost(netuid, network)
        costs.append(info)

        print(f"{info['netuid']:<8} "
              f"τ{info['burn_cost_tao']:<13.6f} "
              f"{str(info['burn_cost_alpha']):<20} "
              f"{info['current_neurons']}/{info['max_neurons']:<10} "
              f"{'Yes' if info['is_full'] else 'No':<6} "
              f"{info['difficulty']:<15,}")

    print()
    print("="*100)
    print("COST ANALYSIS")
    print("="*100)

    # Find cheapest and most expensive
    costs_sorted = sorted(costs, key=lambda x: x['burn_cost_tao'])
    cheapest = costs_sorted[0]
    most_expensive = costs_sorted[-1]

    print(f"\nCheapest:  Subnet {cheapest['netuid']} @ τ{cheapest['burn_cost_tao']:.6f}")
    print(f"Most Expensive: Subnet {most_expensive['netuid']} @ τ{most_expensive['burn_cost_tao']:.6f}")
    print(f"Price Ratio: {most_expensive['burn_cost_tao'] / cheapest['burn_cost_tao']:.1f}x difference")

    # Full vs not full analysis
    full_subnets = [c for c in costs if c['is_full']]
    not_full_subnets = [c for c in costs if not c['is_full']]

    if full_subnets and not_full_subnets:
        avg_full = sum(c['burn_cost_tao'] for c in full_subnets) / len(full_subnets)
        avg_not_full = sum(c['burn_cost_tao'] for c in not_full_subnets) / len(not_full_subnets)

        print(f"\nAverage cost for FULL subnets: τ{avg_full:.6f}")
        print(f"Average cost for NOT FULL subnets: τ{avg_not_full:.6f}")


def estimate_registration_usd(netuid: int, tao_price_usd: float = 50.0, network: str = "finney"):
    """
    Calculate registration cost in USD.

    Args:
        netuid: The subnet netuid
        tao_price_usd: Current TAO price in USD (default: 50)
        network: Bittensor network (default: finney)
    """
    info = get_registration_cost(netuid, network)
    cost_usd = info['burn_cost_tao'] * tao_price_usd

    print("="*80)
    print(f"REGISTRATION COST CALCULATOR - Subnet {netuid}")
    print("="*80)
    print()
    print(f"Burn cost:        τ{info['burn_cost_tao']:.6f} TAO")
    print(f"TAO price:        ${tao_price_usd:.2f}")
    print(f"USD cost:         ${cost_usd:.2f}")
    print()
    print(f"Subnet status:    {info['current_neurons']}/{info['max_neurons']} slots "
          f"({'FULL' if info['is_full'] else 'AVAILABLE'})")
    print(f"Immunity period:  {info['immunity_period_blocks']:,} blocks "
          f"(~{info['immunity_period_blocks'] * 12 / 3600:.1f} hours)")
    print()

    # Registration economics
    print("REGISTRATION ECONOMICS:")
    if info['is_full']:
        print("  • Subnet is FULL - registration will KICK OUT lowest performer")
        print("  • Your cost: Registration burn fee")
        print(f"  • Your risk: Must outperform bottom miner within {info['immunity_period_blocks']:,} blocks")
    else:
        slots_available = info['max_neurons'] - info['current_neurons']
        print(f"  • Subnet has {slots_available} AVAILABLE slots")
        print("  • Your cost: Registration burn fee only")
        print("  • Your risk: Lower - no immediate competition")

    print()
    print("COST BARRIER ASSESSMENT:")
    if info['burn_cost_tao'] < 0.005:
        print("  🟢 Very Low Barrier - Easy entry, expect high competition")
    elif info['burn_cost_tao'] < 0.02:
        print("  🟡 Medium Barrier - Moderate filter on participants")
    else:
        print("  🔴 High Barrier - Significant cost filters casual attempts")


def get_all_subnet_costs(network: str = "finney", output_csv: bool = False):
    """
    Get registration costs for ALL subnets.

    Args:
        network: Bittensor network (default: finney)
        output_csv: If True, output CSV format for easy import
    """
    st = bt.Subtensor(network=network)
    all_netuids = st.get_all_subnets_netuid()

    print(f"Found {len(all_netuids)} subnets on {network}")
    print()

    if output_csv:
        print("netuid,burn_cost_tao,current_neurons,max_neurons,occupancy_pct,is_full,difficulty")
        for netuid in all_netuids:
            try:
                info = get_registration_cost(netuid, network)
                print(f"{info['netuid']},"
                      f"{info['burn_cost_tao']:.6f},"
                      f"{info['current_neurons']},"
                      f"{info['max_neurons']},"
                      f"{info['occupancy_percent']:.2f},"
                      f"{info['is_full']},"
                      f"{info['difficulty']}")
            except Exception as e:
                print(f"{netuid},ERROR,ERROR,ERROR,ERROR,ERROR,ERROR # {e}", file=sys.stderr)
    else:
        costs = []
        for netuid in all_netuids:
            try:
                info = get_registration_cost(netuid, network)
                costs.append(info)
            except Exception as e:
                print(f"Error fetching subnet {netuid}: {e}")

        # Sort by cost
        costs.sort(key=lambda x: x['burn_cost_tao'], reverse=True)

        print(f"{'Rank':<6} {'Netuid':<8} {'Cost (τ)':<15} {'Slots':<15} {'Full':<6} {'Occupancy':<10}")
        print("-"*70)

        for rank, info in enumerate(costs, 1):
            print(f"{rank:<6} {info['netuid']:<8} "
                  f"τ{info['burn_cost_tao']:<13.6f} "
                  f"{info['current_neurons']}/{info['max_neurons']:<10} "
                  f"{'Yes' if info['is_full'] else 'No':<6} "
                  f"{info['occupancy_percent']:<9.1f}%")


def main():
    """Run examples."""
    import sys

    print("\n" + "="*100)
    print("EXAMPLE 1: Get registration cost for a single subnet")
    print("="*100 + "\n")

    estimate_registration_usd(netuid=1, tao_price_usd=50.0)

    print("\n" + "="*100)
    print("EXAMPLE 2: Compare costs across competitive subnets")
    print("="*100 + "\n")

    competitive_subnets = [1, 83, 21, 18, 6, 55, 100, 120]
    compare_registration_costs(competitive_subnets)

    print("\n" + "="*100)
    print("EXAMPLE 3: Get costs for all subnets (top 20 by cost)")
    print("="*100 + "\n")

    st = bt.Subtensor(network="finney")
    all_netuids = st.get_all_subnets_netuid()[:20]  # Limit to first 20 for demo

    get_all_subnet_costs(network="finney", output_csv=False)


if __name__ == "__main__":
    main()
