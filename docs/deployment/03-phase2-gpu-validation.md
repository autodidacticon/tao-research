# Phase 2: GPU Validation

**Duration:** 1-2 weeks
**Cost:** $150-500
**Risk:** Medium

## 🎯 Objective

Validate full end-to-end GPU operations with ONE cheapest GPU node. Practice all day-2 operations extensively before committing to production scale.

## ⚠️ Critical: Why This Phase is Essential

This is where you:
- **Validate GPU detection** and drivers work correctly
- **Practice operations** 5-10 times before production
- **Understand costs** and validate profitability model
- **Build confidence** in troubleshooting
- **Discover issues** in controlled environment

**DO NOT SKIP THIS PHASE** - The $150-500 investment prevents $5000+ production mistakes.

## 📋 Prerequisites

### Completed Phase 1

- [ ] Phase 1 exit criteria met
- [ ] Control plane validation passed
- [ ] Ansible playbooks tested
- [ ] Operations documented

### GPU Provider Selection

Choose cheapest GPU with dedicated static IP:

| Provider | GPU Type | Specs | Cost | Recommendation |
|----------|----------|-------|------|----------------|
| **Shadeform** | T4 | 16GB VRAM | $0.30-0.50/hr (~$7-12/day) | ✅ Best value |
| **AWS** | g4dn.xlarge (T4) | 16GB VRAM, 4 vCPU, 16GB RAM | $0.526/hr (~$13/day) | Good availability |
| **Latitude.sh** | L40S | 48GB VRAM | ~$30/day | High performance |
| **Hyperstack** | A100 | 40-80GB VRAM | $1-2/hr (~$24-48/day) | High cost |

**Recommendation:** Start with **Shadeform T4** or **AWS g4dn.xlarge** for lowest cost.

### Budget Planning

| Item | Daily Cost | 2-Week Cost |
|------|-----------|-------------|
| CPU Node | $1-3 | $14-42 |
| GPU Node (T4) | $7-13 | $98-182 |
| **Total Estimate** | **$8-16/day** | **$112-224** |

Budget **$150-500** to allow for learning time and potential issues.

## 🚀 Step 1: Provision Infrastructure

### Option A: AWS (Most Accessible)

```bash
# Via AWS Console:
# 1. EC2 → Launch Instance
# 2. Name: chutes-staging-cpu-0
# 3. AMI: Ubuntu 22.04 LTS
# 4. Instance type: t3.2xlarge (8 vCPU, 32GB RAM)
# 5. Key pair: Create or use existing
# 6. Network: Default VPC, Auto-assign public IP
# 7. Storage: 100GB gp3
# 8. Launch

# Note CPU node IP: X.X.X.X

# Repeat for GPU:
# 1. EC2 → Launch Instance
# 2. Name: chutes-staging-gpu-0
# 3. AMI: Ubuntu 22.04 LTS (or Deep Learning AMI if pre-installed drivers)
# 4. Instance type: g4dn.xlarge (4 vCPU, 16GB RAM, 1x T4)
# 5. Key pair: Same as CPU node
# 6. Network: Same VPC, Auto-assign public IP
# 7. Storage: 200GB gp3 (for model cache)
# 8. Launch

# Note GPU node IP: Y.Y.Y.Y
```

### Option B: Shadeform (Cheapest)

```bash
# Via Shadeform Console:
# 1. Select provider with T4 available
# 2. Ensure static public IP included
# 3. Note IPs for both nodes
```

### Security Groups (AWS) / Firewall

**CPU Node:**
```
22      # SSH
32000   # Miner API
32001   # Monitor
30080   # Grafana
30090   # Prometheus
6443    # k3s API
```

**GPU Node:**
```
22      # SSH
32000   # Agent API
30500   # Registry proxy
8000    # GraVal bootstrap
6443    # k3s API
```

**Important:** Allow all traffic between CPU and GPU nodes (same VPC).

## 📝 Step 2: Update Staging Inventory

Update `~/chutes-deployment/inventory/staging.yml`:

```yaml
all:
  children:
    control:
      hosts:
        chutes-miner-cpu-0:
          ansible_host: X.X.X.X  # CPU node IP
          external_ip: X.X.X.X

    workers:
      hosts:
        chutes-miner-gpu-0:
          ansible_host: Y.Y.Y.Y  # GPU node IP
          external_ip: Y.Y.Y.Y

  vars:
    ansible_user: ubuntu
    ansible_ssh_private_key_file: ~/.ssh/staging-key.pem
    ssh_keys:
      - "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"

    user: chutes
    hotkey_path: "~/.bittensor/wallets/staging/hotkeys/staging"
    chart_values: "~/chutes-deployment/values/staging-values.yaml"
    grafana_password: "{{ lookup('env', 'STAGING_GRAFANA_PASSWORD') }}"
```

## 🎯 Step 3: Deploy Control Plane (If Not Already)

```bash
cd ~/git/tao-research/chutes-miner/ansible/k3s

# Deploy control plane
ansible-playbook -i ~/chutes-deployment/inventory/staging.yml \
    playbooks/site.yml \
    --limit control

# Verify
~/chutes-deployment/scripts/validate-deployment.sh staging
```

## 🎮 Step 4: Deploy GPU Node

```bash
cd ~/git/tao-research/chutes-miner/ansible/k3s

# Deploy GPU node (will take 15-25 minutes)
ansible-playbook -i ~/chutes-deployment/inventory/staging.yml \
    playbooks/site.yml \
    --tags add-nodes \
    --limit chutes-miner-gpu-0

# What this does:
# - Installs NVIDIA drivers
# - Installs CUDA toolkit
# - Installs k3s agent
# - Deploys GPU-specific charts
# - Configures GraVal bootstrap
# - Sets up registry proxy
```

Monitor progress:
```bash
# SSH to GPU node
ssh -i ~/.ssh/staging-key.pem ubuntu@Y.Y.Y.Y

# Check NVIDIA driver installation
nvidia-smi
# Should show GPU details

# Check k3s installation
sudo kubectl get nodes
# Should show node Ready

# Check pods
sudo kubectl get pods -n chutes
# Should see: agent, registry-proxy, graval-bootstrap

exit
```

## 🔧 Step 5: Add Node to Miner Inventory

```bash
# Install chutes-miner CLI (if not already installed)
pip install chutes-miner-cli

# Add GPU node to miner
chutes-miner add-node \
  --name chutes-miner-gpu-0 \
  --validator 5Dt7HZ7Zpw4DppPxFM7Ke3Cm7sDAWhsZXmM5ZAmE7dSVJbcQ \
  --hourly-cost 0.50 \
  --gpu-short-ref t4 \
  --hotkey ~/.bittensor/wallets/staging/hotkeys/staging \
  --agent-api http://Y.Y.Y.Y:32000 \
  --miner-api http://X.X.X.X:32000

# Verify node added
curl http://X.X.X.X:32000/api/servers | jq .

# Should see chutes-miner-gpu-0 in response
```

## ✅ Step 6: Comprehensive Validation

### GPU Detection

```bash
ssh -i ~/.ssh/staging-key.pem ubuntu@Y.Y.Y.Y

# Verify GPU
nvidia-smi

# Check GraVal can see GPU
curl http://localhost:8000/ping
# Should return "pong"

curl http://localhost:8000/devices
# Should return GPU device info

exit
```

### Agent API

```bash
# From your local machine
curl http://Y.Y.Y.Y:32000/health
# Should return OK
```

### Registry Proxy

```bash
curl -v http://Y.Y.Y.Y:30500/v2/
# Should get registry response
```

### Database Verification

```bash
ssh -i ~/.ssh/staging-key.pem ubuntu@X.X.X.X

sudo kubectl exec -it deployment/postgres -n chutes -- \
    psql -U chutes -d chutes

# Check servers table
SELECT * FROM servers WHERE name='chutes-miner-gpu-0';

# Check GPUs table
SELECT * FROM gpus WHERE server_id=(SELECT id FROM servers WHERE name='chutes-miner-gpu-0');

\q
exit
```

### Full Validation

```bash
~/chutes-deployment/scripts/validate-deployment.sh staging
```

All checks should pass!

## 🎓 Step 7: Practice Day-2 Operations

**Critical:** Practice each operation 5-10 times. Build muscle memory!

### Operation 1: Update Gepetto (Practice 5x)

See [Update Gepetto Runbook](../runbooks/update-gepetto.md)

**Practice scenarios:**
1. Simple threshold change
2. Add new selection criteria
3. Modify cost optimization
4. Add logging
5. Intentional syntax error (practice rollback)

### Operation 2: Monitor Chute Deployments

```bash
# Watch Gepetto logs
ssh ubuntu@X.X.X.X 'sudo kubectl logs -f deployment/gepetto -n chutes'

# Watch for chute deployments on GPU node
ssh ubuntu@Y.Y.Y.Y 'watch sudo kubectl get pods -n chutes-jobs'

# Check deployment status in database
ssh ubuntu@X.X.X.X \
    'sudo kubectl exec -it deployment/postgres -n chutes -- \
    psql -U chutes -d chutes -c "SELECT * FROM deployments ORDER BY created_at DESC LIMIT 10;"'
```

### Operation 3: Backup and Restore (Practice 3x)

```bash
# Create backup
~/chutes-deployment/scripts/backup-state.sh staging

# Intentionally break something
ssh ubuntu@X.X.X.X \
    'sudo kubectl exec -it deployment/postgres -n chutes -- \
    psql -U chutes -d chutes -c "DROP TABLE servers;"'

# Restore from backup
~/chutes-deployment/scripts/rollback.sh staging ~/chutes-backups/staging-TIMESTAMP.tar.gz

# Verify restoration
~/chutes-deployment/scripts/validate-deployment.sh staging
```

### Operation 4: Troubleshooting (Practice 5x)

See [Troubleshooting Runbook](../runbooks/troubleshooting.md)

**Intentionally cause issues:**

1. **Kill Gepetto pod** - Watch it restart
```bash
ssh ubuntu@X.X.X.X 'sudo kubectl delete pod -l app=gepetto -n chutes'
```

2. **Fill disk space** - Monitor alerts
```bash
ssh ubuntu@Y.Y.Y.Y 'dd if=/dev/zero of=/var/snap/testfile bs=1M count=5000'
```

3. **Stop k3s** - Practice recovery
```bash
ssh ubuntu@Y.Y.Y.Y 'sudo systemctl stop k3s-agent'
# Wait 2 minutes
ssh ubuntu@Y.Y.Y.Y 'sudo systemctl start k3s-agent'
```

4. **Corrupt ConfigMap** - Practice rollback
```bash
# Intentionally break Gepetto syntax
# Practice identifying issue from logs
# Practice rollback procedure
```

### Operation 5: Monitoring (Practice Daily)

**Daily checks:**
- Grafana dashboards
- Prometheus targets
- PostgreSQL query for active chutes
- Check GPU utilization
- Review costs in provider console

## 💰 Step 8: Validate Profitability Model

### Track Actual Costs

```bash
# AWS: Check billing dashboard daily
# Note actual daily spend

# Create cost tracking spreadsheet:
# Date | CPU Cost | GPU Cost | Total | Chutes Deployed | Compute Hours | $/Hour
```

### Measure Performance

```sql
-- SSH to control plane
ssh ubuntu@X.X.X.X

sudo kubectl exec -it deployment/postgres -n chutes -- psql -U chutes -d chutes

-- Query deployment statistics
SELECT
    COUNT(*) as total_chutes,
    COUNT(CASE WHEN status='running' THEN 1 END) as running,
    COUNT(CASE WHEN status='failed' THEN 1 END) as failed,
    ROUND(AVG(EXTRACT(EPOCH FROM (started_at - created_at))), 2) as avg_cold_start_seconds
FROM deployments
WHERE created_at > NOW() - INTERVAL '24 hours';

\q
exit
```

### Calculate Break-Even

```
Daily Cost: $X
Compute Hours Provided: Y hours
Effective Cost: $X/Y per hour

Compare to:
- Subnet 64 incentive rate
- Other miners' performance
- Alternative uses of capital
```

**Decision Point:** Is this profitable enough to scale?

## 🎯 Exit Criteria

### Technical Validation

- [ ] GPU node deployed successfully
- [ ] NVIDIA drivers installed and working
- [ ] GraVal validation passing
- [ ] Registry proxy authenticating correctly
- [ ] Agent API functional
- [ ] Node in miner database
- [ ] Can deploy test chute successfully
- [ ] Chute accessible via NodePort
- [ ] Monitoring showing GPU metrics
- [ ] All validation scripts pass

### Operational Readiness

- [ ] Practiced Gepetto updates 5+ times
- [ ] Practiced troubleshooting 5+ times
- [ ] Practiced backup/restore 3+ times
- [ ] Know how to read Grafana dashboards
- [ ] Know how to query PostgreSQL
- [ ] Know how to check logs
- [ ] All runbooks validated against real infrastructure
- [ ] Comfortable with all operations

### Business Validation

- [ ] Tracked costs for 7+ days
- [ ] Measured actual performance
- [ ] Calculated profitability
- [ ] Understand economics
- [ ] Decision made on production scale

## 🧹 Cleanup Options

### Option A: Keep Running (Recommended)

Keep infrastructure running for 2 weeks total to:
- Get full profitability data
- Practice operations extensively
- Build confidence
- Learn the system

**Cost:** ~$150-500 for 2 weeks

### Option B: Destroy After Validation

If need to minimize costs:
```bash
# Terminate both instances
# Via provider console
```

**Cost:** ~$50-150 for 3-7 days

## 📊 Phase 2 Outcomes

After completing Phase 2, you should have:

1. **Confidence** - Practiced operations 20+ times
2. **Knowledge** - Deep understanding of system
3. **Runbooks** - Validated procedures
4. **Data** - Real profitability metrics
5. **Skills** - Troubleshooting experience
6. **Documentation** - Updated with real-world learnings

## 🚀 Next Steps

Once all exit criteria met → **[Phase 3: Production Deployment](04-phase3-production.md)**

---

**Time Investment:** 1-2 weeks
**Cost:** $150-500
**Outcome:** Complete operational readiness for production
