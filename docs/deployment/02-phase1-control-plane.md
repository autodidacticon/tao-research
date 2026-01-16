# Phase 1: Cloud Control Plane Validation

**Duration:** 2-4 days
**Cost:** $5-20
**Risk:** Low

## 🎯 Objective

Validate Ansible automation, networking, and infrastructure on real cloud **WITHOUT** expensive GPU nodes.

## 📋 Prerequisites

### Completed Phase 0

- [ ] All Phase 0 exit criteria met
- [ ] Runbooks written
- [ ] Operations practiced locally

### Cloud Provider Account

Choose one provider for CPU-only node:

| Provider | Instance Type | Specs | Monthly | Hourly | Recommendation |
|----------|--------------|-------|---------|--------|----------------|
| **Hetzner** | CPX41 | 4 cores, 32GB | $30 | ~$0.04 | ✅ Best value |
| **DigitalOcean** | CPU 4 cores, 32GB | 4 cores, 32GB | $168 | $0.23 | Good |
| **Vultr** | 4 cores, 32GB | 4 cores, 32GB | $96 | $0.13 | Good |
| **AWS** | t3.2xlarge | 8 cores, 32GB | ~$243 | $0.33 | Expensive |

**Use hourly billing** - Total cost for this phase: **$5-20**

### Requirements

- Static public IPv4 address
- SSH access
- Firewall rules configurable
- Ubuntu 22.04 image available

## 🚀 Step 1: Provision Server

### Hetzner Example

```bash
# Via Hetzner Cloud Console:
# 1. Create project "chutes-staging"
# 2. Add Server:
#    - Location: Any
#    - Image: Ubuntu 22.04
#    - Type: CPX41 (4 vCPU, 32GB RAM)
#    - Networking: Public IPv4
#    - SSH Key: Add your public key
#    - Name: chutes-staging-cpu-0

# Note the public IP address: X.X.X.X
```

### Firewall Configuration

Configure firewall to allow:

```bash
# Required ports
22     # SSH
32000  # Miner API (NodePort)
32001  # Monitor API (NodePort)
30080  # Grafana (NodePort)
30090  # Prometheus (NodePort)
6443   # k3s API
```

Most providers: Configure in web console
Hetzner: Create Firewall, attach to server

## 📝 Step 2: Create Staging Inventory

Create `~/chutes-deployment/inventory/staging.yml`:

```yaml
all:
  children:
    control:
      hosts:
        chutes-miner-cpu-0:
          ansible_host: X.X.X.X  # Replace with your server IP
          external_ip: X.X.X.X   # Same as ansible_host

    # No workers in Phase 1 - control plane only

  vars:
    ansible_user: ubuntu
    ansible_ssh_private_key_file: ~/.ssh/hetzner-staging.pem  # Your SSH key
    ssh_keys:
      - "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"  # Your public key

    user: chutes

    # Create test hotkey for staging
    hotkey_path: "~/.bittensor/wallets/staging/hotkeys/staging"

    chart_values: "~/chutes-deployment/values/staging-values.yaml"

    # Grafana password
    grafana_password: "{{ lookup('env', 'STAGING_GRAFANA_PASSWORD') }}"
```

## 🔑 Step 3: Create Staging Wallet

```bash
# Install btcli if not already installed
pip install bittensor

# Create staging wallet (for testing only)
btcli wallet new_coldkey --wallet.name staging
btcli wallet new_hotkey --wallet.name staging --wallet.hotkey staging

# Verify hotkey path
ls ~/.bittensor/wallets/staging/hotkeys/staging

# Set Grafana password
export STAGING_GRAFANA_PASSWORD="your-secure-password-here"
```

## ⚙️ Step 4: Create Staging Values

Create `~/chutes-deployment/values/staging-values.yaml`:

```yaml
# Use production-equivalent settings (NO mock mode!)
multiCluster: true
calico: true

# Real validator configuration
validators:
  defaultRegistry: registry.chutes.ai
  defaultApi: https://api.chutes.ai
  supported:
    - hotkey: 5Dt7HZ7Zpw4DppPxFM7Ke3Cm7sDAWhsZXmM5ZAmE7dSVJbcQ
      registry: registry.chutes.ai
      api: https://api.chutes.ai
      socket: wss://ws.chutes.ai

# Production-equivalent resource limits
minerApi:
  image: parachutes/miner:k3s-latest
  imagePullPolicy: Always
  service:
    type: NodePort
    nodePort: 32000
    port: 8000
    targetPort: 8000
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
      cpu: "500m"
      memory: "2Gi"
    limits:
      cpu: "1"
      memory: "2Gi"

postgres:
  image: postgres:16
  persistence:
    enabled: true
  resources:
    requests:
      cpu: "500m"
      memory: "1Gi"
    limits:
      cpu: "1"
      memory: "2Gi"
  database:
    name: chutes
    user: chutes
  service:
    type: ClusterIP
    port: 5432

redis:
  image: redis:7
  resources:
    requests:
      cpu: "1"
      memory: "512Mi"
    limits:
      cpu: "1"
      memory: "1Gi"
  service:
    type: ClusterIP
    port: 6379

cache:
  max_age_days: 30
  max_size_gb: 100

# Will be replaced by Ansible during deployment
minerCredentials:
  ss58Address: "REPLACE_WITH_ANSIBLE"
  secretSeed: "REPLACE_WITH_ANSIBLE"
```

## 🚀 Step 5: Test Ansible Dry Run

```bash
cd ~/git/tao-research/chutes-miner/ansible/k3s

# Syntax check
ansible-playbook -i ~/chutes-deployment/inventory/staging.yml \
    playbooks/site.yml \
    --syntax-check

# Check mode (shows what would change)
ansible-playbook -i ~/chutes-deployment/inventory/staging.yml \
    playbooks/site.yml \
    --check \
    --diff \
    --limit control

# If check mode looks good, proceed to actual deployment
```

## 🎯 Step 6: Deploy Control Plane

```bash
cd ~/git/tao-research/chutes-miner/ansible/k3s

# Deploy (will take 10-15 minutes)
ansible-playbook -i ~/chutes-deployment/inventory/staging.yml \
    playbooks/site.yml \
    --limit control

# Monitor deployment
# You should see:
# - System packages installed
# - k3s installed
# - Helm charts deployed
# - Services starting
```

## ✅ Step 7: Validate Deployment

### SSH Connectivity

```bash
ssh -i ~/.ssh/hetzner-staging.pem ubuntu@X.X.X.X

# Once connected:
sudo kubectl get nodes
# Should show node in Ready state

sudo kubectl get pods -n chutes
# Should show all pods Running

exit
```

### Network Access

```bash
# Miner API health check
curl http://X.X.X.X:32000/health

# Should return OK

# Grafana
open http://X.X.X.X:30080
# Login: admin / <STAGING_GRAFANA_PASSWORD>

# Prometheus
curl http://X.X.X.X:30090/api/v1/targets
```

### Run Validation Script

```bash
~/chutes-deployment/scripts/validate-deployment.sh staging
```

All critical checks should pass!

### Database Inspection

```bash
ssh -i ~/.ssh/hetzner-staging.pem ubuntu@X.X.X.X

sudo kubectl exec -it deployment/postgres -n chutes -- \
    psql -U chutes -d chutes

# Inside psql:
\dt  # List tables (should see servers, gpus, deployments, etc.)
\q   # Quit

exit
```

## 📚 Step 8: Practice Operations

### Update Gepetto

```bash
# Edit locally
vim ~/gepetto-custom.py

# Create ConfigMap (use actual context)
kubectl create configmap gepetto-code \
  --kubeconfig=<(ssh ubuntu@X.X.X.X 'sudo cat /etc/rancher/k3s/k3s.yaml' | sed "s/127.0.0.1/X.X.X.X/") \
  --from-file=gepetto.py=~/gepetto-custom.py \
  -n chutes \
  -o yaml --dry-run=client | kubectl apply -f -

# Restart
kubectl rollout restart deployment/gepetto \
  --kubeconfig=<(ssh ubuntu@X.X.X.X 'sudo cat /etc/rancher/k3s/k3s.yaml' | sed "s/127.0.0.1/X.X.X.X/") \
  -n chutes

# Watch logs
ssh ubuntu@X.X.X.X 'sudo kubectl logs -f deployment/gepetto -n chutes'
```

### Backup Database

```bash
ssh ubuntu@X.X.X.X \
  'sudo kubectl exec deployment/postgres -n chutes -- pg_dump -U chutes chutes' \
  > ~/staging-backup-$(date +%Y%m%d).sql

# Verify backup
ls -lh ~/staging-backup-*.sql
```

## 🎯 Exit Criteria

- [ ] Server provisioned with static IP
- [ ] SSH access working
- [ ] Ansible playbook executed successfully
- [ ] k3s node in Ready state
- [ ] All pods in Running state (postgres, redis, gepetto, miner-api)
- [ ] Miner API accessible on port 32000
- [ ] Grafana accessible on port 30080
- [ ] Prometheus accessible on port 30090
- [ ] PostgreSQL accepting connections
- [ ] Database schema initialized
- [ ] No firewall/networking issues
- [ ] Can update Gepetto ConfigMap
- [ ] Can backup database
- [ ] All validation scripts pass
- [ ] Documented any issues encountered

## 🧹 Cleanup (Important!)

**DESTROY SERVER** after validation to stop costs:

```bash
# Via Hetzner Console:
# 1. Go to Servers
# 2. Select chutes-staging-cpu-0
# 3. Delete server
# 4. Confirm deletion

# Verify no charges accumulating
```

**Total Phase 1 Cost:** ~$5-20 (48-96 hours @ hourly rate)

## 📊 Lessons Learned

Document in your runbooks:

- Any Ansible playbook issues encountered
- Firewall rule adjustments needed
- SSH connectivity problems
- k3s installation quirks
- Helm chart deployment issues
- Networking discoveries

This knowledge is **gold** for Phase 3 production deployment!

## 🚀 Next Steps

Once all exit criteria met and server destroyed → **[Phase 2: GPU Validation](03-phase2-gpu-validation.md)**

---

**Time Investment:** 2-4 days
**Cost:** $5-20
**Outcome:** Validated infrastructure automation on real cloud
