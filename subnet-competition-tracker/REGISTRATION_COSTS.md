# How to Find Registration Costs

This guide explains how to find and interpret registration costs for Bittensor subnets using the SDK.

## Quick Reference

### Method 1: Using Bittensor SDK (Python)

```python
import bittensor as bt

# Connect to network
st = bt.Subtensor(network="finney")

# Get subnet info
info = st.get_subnet_info(netuid=1)

# Registration cost is in the 'burn' attribute
print(f"Registration cost: {info.burn}")
# Output: τ0.004396

# Convert to float for calculations
cost_tao = float(str(info.burn).replace('τ', ''))
print(f"Cost in TAO: {cost_tao:.6f}")
# Output: Cost in TAO: 0.004396
```

### Method 2: Using btcli (Command Line)

```bash
# Get all subnet info including burn costs
btcli subnets list --json-output

# Get specific subnet hyperparameters
btcli subnets hyperparameters --netuid 1 --json-output
```

### Method 3: Using the Examples Script

```bash
# Single subnet cost calculator
uv run python3 -c "
from examples import estimate_registration_usd
estimate_registration_usd(netuid=1, tao_price_usd=50.0)
"

# Compare multiple subnets
uv run python3 -c "
from examples import compare_registration_costs
compare_registration_costs([1, 83, 21, 68, 38])
"

# Get ALL subnet costs as CSV
uv run python3 -c "
from examples import get_all_subnet_costs
get_all_subnet_costs(output_csv=True)
" > subnet_costs.csv
```

## Understanding Registration Costs

### What is the Burn Cost?

The **burn cost** is the amount of TAO (τ) that must be permanently destroyed (burned) to register a new neuron (miner/validator) on a subnet.

**Key Points:**
- TAO is converted to subnet-specific Alpha (α) tokens
- The Alpha is then burned during registration
- Cost is dynamic based on subnet economics
- Different subnets have vastly different costs

### Cost Ranges (as of current data)

| Cost Range | Example | Interpretation |
|------------|---------|----------------|
| τ0.001 - τ0.005 | Subnet 1 (τ0.0044) | 🟢 **Very Low Barrier** - Easy entry, expect high competition |
| τ0.005 - τ0.020 | Subnet 21 (τ0.0019) | 🟡 **Medium Barrier** - Moderate filter |
| τ0.020 - τ0.050 | Subnet 83 (τ0.0323) | 🔴 **High Barrier** - Significant cost |
| τ0.050+ | Subnet 38 (τ0.0514) | 🔴 **Very High Barrier** - Major investment |

### Real-World Cost Examples (@ $50/TAO)

| Netuid | Burn Cost (τ) | USD Cost | Subnet Status | Competition Level |
|--------|---------------|----------|---------------|-------------------|
| 1 | 0.004396 | $0.22 | 256/256 FULL | 🔥 Extreme (48% replacement) |
| 21 | 0.001852 | $0.09 | 256/256 FULL | 🔥 High (18.8% replacement) |
| 83 | 0.032321 | $1.62 | 256/256 FULL | 🔥 Very High (22.7% replacement) |
| 68 | 0.024327 | $1.22 | 64/64 FULL | 🔥 High (45.3% replacement) |
| 100 | 0.000678 | $0.03 | 256/256 FULL | 🔥 High (16% replacement) |
| 38 | 0.051413 | $2.57 | 7/256 EMPTY | ❄️ Collapsed (2.7% replacement) |

## Relationship Between Cost and Competition

### Observation: Low Cost ≠ High Competition

While you might expect **low cost → high competition**, the data shows more nuance:

**Subnet 1** (τ0.0044, $0.22):
- Cheapest among competitive subnets
- **Result**: 48% replacement rate - EXTREME competition
- **Why**: Low barrier → many challengers → constant churn

**Subnet 83** (τ0.0323, $1.62):
- 7x more expensive than Subnet 1
- **Result**: 23% replacement rate - still very competitive, but more stable
- **Why**: Higher barrier → fewer but more serious challengers

**Subnet 38** (τ0.0514, $2.57):
- Most expensive in our sample
- **Result**: 2.7% replacement, 97% empty
- **Why**: High cost + underlying subnet issues → no one wants in

### The Real Pattern:

```
Competition = (Interest in Subnet) / (Cost Barrier + Subnet Quality)

High Interest + Low Cost = Extreme Competition (Subnet 1)
High Interest + High Cost = Moderate Competition (Subnet 83)
Low Interest + Any Cost = Low Competition (Subnet 38)
```

## Advanced: Programmatic Cost Analysis

### Get Cost Data for All Subnets

```python
import bittensor as bt
import csv

st = bt.Subtensor(network="finney")
all_netuids = st.get_all_subnets_netuid()

# Collect costs
subnet_costs = []
for netuid in all_netuids:
    info = st.get_subnet_info(netuid=netuid)
    cost_tao = float(str(info.burn).replace('τ', ''))

    subnet_costs.append({
        'netuid': netuid,
        'cost_tao': cost_tao,
        'occupancy': info.subnetwork_n / info.max_n,
        'is_full': info.subnetwork_n >= info.max_n
    })

# Sort by cost
subnet_costs.sort(key=lambda x: x['cost_tao'], reverse=True)

# Output
for s in subnet_costs[:10]:  # Top 10 most expensive
    print(f"Subnet {s['netuid']}: τ{s['cost_tao']:.6f} "
          f"({s['occupancy']*100:.0f}% full)")
```

### Combine with Competition Tracker

```python
# Add registration cost to competition analysis
from main import SubnetCompetitionTracker

tracker = SubnetCompetitionTracker()
results = tracker.analyze_competition()

# Enrich with cost data
st = bt.Subtensor(network="finney")
for netuid, stats in results.items():
    info = st.get_subnet_info(netuid=int(netuid))
    cost = float(str(info.burn).replace('τ', ''))

    stats['registration_cost_tao'] = cost
    stats['cost_per_replacement'] = cost if stats['avg_replacements_per_period'] > 0 else 0

# Find most cost-effective competitive subnets
# (high competition but low entry cost)
efficient = sorted(
    results.items(),
    key=lambda x: x[1]['replacement_percentage'] / x[1]['registration_cost_tao'],
    reverse=True
)[:10]

print("Most Cost-Effective Competitive Subnets:")
for netuid, stats in efficient:
    print(f"Netuid {netuid}: {stats['replacement_percentage']:.1f}% competition "
          f"for only τ{stats['registration_cost_tao']:.6f}")
```

## What Determines Registration Cost?

The registration cost is based on the **Dynamic TAO** (DTAO) economic model:

1. **Alpha Token Supply**: Each subnet has its own Alpha (α) token
2. **Bonding Curve**: TAO ↔ Alpha exchange rate follows a bonding curve
3. **Registration Burns Alpha**: Registration requires burning Alpha tokens
4. **Cost Reflects Demand**: Higher demand for subnet → higher Alpha price → higher burn cost

### Factors Affecting Cost:

- **Subnet popularity**: More registrations → higher Alpha price
- **Emissions**: Higher emissions → more attractive → higher demand
- **Current supply**: Alpha in circulation affects price
- **Recent activity**: Recent registrations/deregistrations shift the curve

## FAQ

### Q: Why is Subnet 38 so expensive yet empty?

**A:** High cost is a *result* of past activity, not current demand. The subnet likely:
1. Had high demand in the past (drove up Alpha price)
2. Experienced a mass exodus (249 deregistrations)
3. Left with high Alpha price but no interest
4. Acts as a warning signal: "Stay away!"

### Q: Can I see historical cost changes?

**A:** Yes! Store `SubnetInfo.burn` in your snapshots:

```python
# In main.py's take_snapshot():
snapshot["subnets"][str(netuid)] = {
    "uid_hotkey_map": uid_mapping,
    "n_neurons": len(metagraph.uids),
    "block": metagraph.block.item(),
    "burn_cost": str(info.burn)  # Add this
}
```

### Q: What's a "reasonable" registration cost?

**A:** Depends on your goals:
- **Testing/Learning**: < τ0.01 ($0.50)
- **Serious Mining**: τ0.01 - τ0.05 ($0.50 - $2.50)
- **High-Stakes**: > τ0.05 ($2.50+)

At current TAO prices, even "expensive" subnets cost < $3 to register.

### Q: Does PoW registration bypass the cost?

**A:** No, PoW has its own cost:
- **Computational cost**: Electricity + hardware
- **Time cost**: Solving difficulty puzzle
- **Difficulty**: Some subnets have PoW difficulty set to max (18.4 quintillion)

For most subnets, burning TAO is cheaper than PoW.

## Tools Reference

### Bittensor SDK Methods

```python
st = bt.Subtensor(network="finney")

# Get subnet info (includes burn cost)
info = st.get_subnet_info(netuid=1)
# Access: info.burn

# Get list of all subnet IDs
netuids = st.get_all_subnets_netuid()

# Get metagraph (for UID/hotkey data)
metagraph = st.metagraph(netuid=1)

# Get subnet hyperparameters
# (Note: burn cost is in SubnetInfo, not hyperparameters)
hyperparams = st.get_subnet_hyperparameters(netuid=1)
```

### btcli Commands

```bash
# List all subnets with basic info
btcli subnets list

# Get detailed subnet info (JSON)
btcli subnets list --json-output | jq '.[] | select(.netuid == "1")'

# Show subnet metagraph
btcli subnets show --netuid 1

# Get hyperparameters
btcli subnets hyperparameters --netuid 1
```

## See Also

- `examples.py` - Runnable examples for cost analysis
- `main.py` - Competition tracker (can be extended with cost data)
- `README.md` - Project overview and usage guide
