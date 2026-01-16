# Phase 3: Production Deployment

**Duration:** Ongoing
**Cost:** $400-2000+/mo
**Risk:** Managed

## 🎯 Objective

Deploy and scale production chutes-miner with full confidence, validated procedures, and incremental growth.

## ⚠️ Critical Prerequisites

### Phase 2 Complete

- [ ] ALL Phase 2 exit criteria met
- [ ] Practiced operations 20+ times
- [ ] Profitability validated
- [ ] Budget approved
- [ ] Team trained

### Production Requirements

- [ ] Registered on subnet 64
- [ ] Production Bittensor wallet created and secured
- [ ] Production wallet funded (for registration)
- [ ] Budget allocated for ongoing costs
- [ ] Monitoring/alerting configured
- [ ] On-call rotation defined (if team)
- [ ] Disaster recovery plan written

## 🚀 Production Deployment Checklist

```bash
#!/bin/bash
# Run this interactive checklist before production deployment

echo "=== PRODUCTION DEPLOYMENT CHECKLIST ==="
echo ""
echo "⚠️  This will deploy to PRODUCTION infrastructure"
echo "⚠️  All costs will be REAL and ONGOING"
echo ""

read -p "✓ Completed Phase 0, 1, and 2? (yes/no): " response
[[ "$response" != "yes" ]] && { echo "Complete prior phases first!"; exit 1; }

read -p "✓ Registered on subnet 64? (yes/no): " response
[[ "$response" != "yes" ]] && { echo "Register: btcli subnet register --netuid 64"; exit 1; }

read -p "✓ Production hotkey created and secured? (yes/no): " response
[[ "$response" != "yes" ]] && { echo "Create production wallet!"; exit 1; }

read -p "✓ Reviewed and customized Gepetto strategy? (yes/no): " response
[[ "$response" != "yes" ]] && { echo "Review gepetto.py!"; exit 1; }

read -p "✓ Budget approved ($400-2000+/mo)? (yes/no): " response
[[ "$response" != "yes" ]] && { echo "Get budget approval!"; exit 1; }

read -p "✓ All runbooks validated? (yes/no): " response
[[ "$response" != "yes" ]] && { echo "Validate runbooks in Phase 2!"; exit 1; }

echo ""
echo "✅ All prerequisites met - Ready for production!"
```

## 📝 Step 1: Register on Subnet 64

```bash
# Ensure production wallet is created
btcli wallet list

# Register miner
btcli subnet register \
    --netuid 64 \
    --wallet.name production \
    --wallet.hotkey production

# Verify registration
btcli wallet overview \
    --wallet.name production \
    --netuid 64

# Important: DO NOT announce an axon
# All communication is via websocket connections
```

## 🏗️ Step 2: Plan Infrastructure

### Recommended Starting Configuration

```
Production Minimum (Cost-Effective):
├── 1x CPU Node (4 cores, 32GB RAM)
│   └── Cost: ~$50-100/mo
└── 1-2x GPU Nodes (T4 or L40S)
    └── Cost: ~$350-800/mo total

Total: ~$400-900/mo
```

### Scaling Strategy

**Start small, scale based on data:**

1. **Week 1-2:** 1 CPU + 1 GPU (validate production)
2. **Week 3-4:** Add 1-2 more GPUs (if profitable)
3. **Month 2+:** Scale to diverse GPU portfolio

**GPU Diversity Recommended:**
- Cheap: 2x T4 (for low-cost chutes)
- Mid-range: 2x L40S (balanced)
- High-end: 1x A100 (high-value chutes)

## 📋 Step 3: Create Production Inventory

Create `~/chutes-deployment/inventory/production.yml`:

```yaml
all:
  children:
    control:
      hosts:
        chutes-miner-cpu-0:
          ansible_host: 198.51.100.10  # Production IP
          external_ip: 198.51.100.10

    workers:
      hosts:
        chutes-miner-gpu-0:
          ansible_host: 198.51.100.20
          external_ip: 198.51.100.20
          gpu_type: t4
          hourly_cost: 0.50

        # Add more GPU nodes as you scale
        # chutes-miner-gpu-1:
        #   ansible_host: 198.51.100.21
        #   external_ip: 198.51.100.21
        #   gpu_type: l40s
        #   hourly_cost: 1.20

  vars:
    ansible_user: ubuntu
    ansible_ssh_private_key_file: ~/.ssh/production-key.pem
    ssh_keys:
      - "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"

    user: chutes
    hotkey_path: "~/.bittensor/wallets/production/hotkeys/production"
    chart_values: "~/chutes-deployment/values/prod-values.yaml"
    grafana_password: "{{ lookup('env', 'PROD_GRAFANA_PASSWORD') }}"
```

## ⚙️ Step 4: Create Production Values

Create `~/chutes-deployment/values/prod-values.yaml`:

```yaml
multiCluster: true
calico: true

validators:
  defaultRegistry: registry.chutes.ai
  defaultApi: https://api.chutes.ai
  supported:
    - hotkey: 5Dt7HZ7Zpw4DppPxFM7Ke3Cm7sDAWhsZXmM5ZAmE7dSVJbcQ
      registry: registry.chutes.ai
      api: https://api.chutes.ai
      socket: wss://ws.chutes.ai

# Production resource limits (tune based on your hardware)
minerApi:
  image: parachutes/miner:k3s-latest
  imagePullPolicy: Always
  service:
    type: NodePort
    nodePort: 32000
  resources:
    requests:
      cpu: "500m"
      memory: "1Gi"
    limits:
      cpu: "1"
      memory: "2Gi"

gepetto:
  image: parachutes/miner:k3s-latest
  imagePullPolicy: Always
  resources:
    requests:
      cpu: "1"
      memory: "2Gi"
    limits:
      cpu: "2"
      memory: "4Gi"

postgres:
  image: postgres:16
  persistence:
    enabled: true
  resources:
    requests:
      cpu: "1"
      memory: "2Gi"
    limits:
      cpu: "2"
      memory: "4Gi"

redis:
  image: redis:7
  resources:
    requests:
      cpu: "1"
      memory: "1Gi"
    limits:
      cpu: "2"
      memory: "2Gi"

cache:
  max_age_days: 30
  max_size_gb: 500
  overrides:
    # Adjust per node based on available storage
    # chutes-miner-gpu-0: 1000
    # chutes-miner-gpu-1: 1500

# Will be replaced by Ansible
minerCredentials:
  ss58Address: "REPLACE_WITH_ANSIBLE"
  secretSeed: "REPLACE_WITH_ANSIBLE"
```

## 🚀 Step 5: Deploy Production (Incremental)

```bash
# Use the deployment script
~/chutes-deployment/scripts/deploy.sh production

# This will:
# 1. Create backup (if existing production)
# 2. Deploy control plane
# 3. Validate control plane
# 4. Deploy GPU nodes one at a time
# 5. Validate each GPU node
# 6. Add nodes to miner inventory
```

**Manual alternative:**

```bash
cd ~/git/tao-research/chutes-miner/ansible/k3s

# 1. Deploy control plane
ansible-playbook -i ~/chutes-deployment/inventory/production.yml \
    playbooks/site.yml \
    --limit control

# Wait 2 minutes, then validate
~/chutes-deployment/scripts/validate-deployment.sh production

# 2. Deploy first GPU node
ansible-playbook -i ~/chutes-deployment/inventory/production.yml \
    playbooks/site.yml \
    --tags add-nodes \
    --limit chutes-miner-gpu-0

# Wait 2 minutes, then validate
~/chutes-deployment/scripts/validate-deployment.sh production

# 3. Add to miner inventory
chutes-miner add-node \
  --name chutes-miner-gpu-0 \
  --validator 5Dt7HZ7Zpw4DppPxFM7Ke3Cm7sDAWhsZXmM5ZAmE7dSVJbcQ \
  --hourly-cost 0.50 \
  --gpu-short-ref t4 \
  --hotkey ~/.bittensor/wallets/production/hotkeys/production \
  --agent-api http://198.51.100.20:32000 \
  --miner-api http://198.51.100.10:32000
```

## 📊 Step 6: Initial Monitoring (Critical First 48 Hours)

### Hour 1-24: Intensive Monitoring

```bash
# Watch Gepetto logs continuously
ssh ubuntu@198.51.100.10 'sudo kubectl logs -f deployment/gepetto -n chutes'

# In separate terminal: Watch for chute deployments
ssh ubuntu@198.51.100.20 'watch sudo kubectl get pods -n chutes-jobs'

# Check every hour:
# - Grafana dashboards
# - GPU utilization
# - Deployment success rate
# - Error logs
# - Cost accumulation
```

### Day 2-7: Regular Monitoring

**Daily checks:**
- Morning: Review Grafana dashboards
- Midday: Check deployment success rate
- Evening: Review costs and profitability
- Before bed: Check for any errors

**Set up alerts:**
- Gepetto crashes
- High deployment failure rate
- GPU utilization < 50% or > 95%
- Cost exceeds budget
- Database issues

## 📈 Step 7: Scaling Strategy

### Week 1-2: Validate Single GPU

**Goals:**
- Confirm profitability with 1 GPU
- Understand cost patterns
- Optimize Gepetto strategy
- Build operational rhythm

**Metrics to track:**
- Daily cost
- Compute hours provided
- Deployment success rate
- Average cold start time
- Revenue/incentives (if measurable)

### Week 3-4: Add Second GPU

**If profitable:**
```bash
# Add to inventory
vim ~/chutes-deployment/inventory/production.yml

# Deploy
ansible-playbook -i ~/chutes-deployment/inventory/production.yml \
    playbooks/site.yml \
    --tags add-nodes \
    --limit chutes-miner-gpu-1

# Add to miner
chutes-miner add-node [...]
```

**Monitor for 1 week** - Does profitability scale linearly?

### Month 2+: Diversify GPU Portfolio

**Add variety:**
- Different GPU types (T4, L40S, A100)
- Different cost points
- Optimize for various chute types

**Scale incrementally:**
- Add 1-2 GPUs per week
- Monitor impact on profitability
- Adjust Gepetto strategy
- Track ROI per GPU type

## 💾 Step 8: Operational Procedures

### Daily Operations

1. **Morning:** Review dashboards, check overnight deployments
2. **Midday:** Quick health check
3. **Evening:** Review costs, plan next day

### Weekly Operations

1. **Backup database** (automated recommended)
2. **Review Gepetto performance**
3. **Optimize strategy if needed**
4. **Cost/revenue analysis**
5. **Capacity planning**

### Monthly Operations

1. **Deep cost analysis**
2. **ROI calculation per GPU**
3. **Strategy review**
4. **Infrastructure optimization**
5. **Scale planning**

## 🚨 Disaster Recovery

### Automatic Backups

Setup cron job for daily backups:

```bash
# On control plane
crontab -e

# Add:
0 2 * * * /home/ubuntu/backup-chutes.sh
```

Create `/home/ubuntu/backup-chutes.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
mkdir -p $BACKUP_DIR

kubectl exec deployment/postgres -n chutes -- \
    pg_dump -U chutes chutes > $BACKUP_DIR/chutes-$(date +\%Y\%m\%d).sql

# Keep last 30 days
find $BACKUP_DIR -name "chutes-*.sql" -mtime +30 -delete
```

### Recovery Procedures

See [Backup and Restore Runbook](../runbooks/backup-restore.md)

## 🎯 Success Metrics

### Technical Health

- Uptime > 99%
- Deployment success rate > 95%
- Average cold start < 2 minutes
- GPU utilization 60-80% (optimal)

### Business Health

- Profitability per GPU > 0
- ROI time < 6 months
- Incentive share growing
- Cost per compute hour decreasing

### Operational Health

- No unplanned downtime
- All operations documented
- Team comfortable with procedures
- Continuous optimization

## 🚀 Next Steps

1. **Monitor closely** for first 2 weeks
2. **Optimize Gepetto** based on data
3. **Scale incrementally** based on profitability
4. **Document learnings**
5. **Share knowledge** with community

---

**You did it!** You've deployed a production chutes-miner with confidence, validated procedures, and incremental growth. Keep optimizing and scaling!

## 📞 Support

- **Issues:** [Chutes GitHub](https://github.com/rayonlabs/chutes-miner/issues)
- **Community:** [Bittensor Discord](https://discord.gg/bittensor)
- **Subnet 64:** #subnet-64 channel

---

**Time Investment:** Ongoing
**Cost:** $400-2000+/mo (scales with GPUs)
**Outcome:** Production mining operation
