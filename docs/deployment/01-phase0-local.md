# Phase 0: Local Mastery

**Duration:** 1-2 weeks
**Cost:** $0
**Risk:** None

## 🎯 Objective

Achieve 100% confidence in tooling, configurations, and business logic **before** spending any money on cloud infrastructure.

## 📋 Prerequisites

### Software Requirements

- **Docker Desktop** (Mac/Windows) or **Docker Engine** (Linux)
- **kubectl** - Kubernetes CLI
- **k3d** - k3s in Docker
- **Helm** - Kubernetes package manager
- **Python 3.12+** - For chutes-miner development
- **Git** - Version control

### Installation

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install kubectl k3d helm python@3.12 git

# Install Docker Desktop from https://www.docker.com/products/docker-desktop
```

**Linux:**
```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# k3d
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Docker
sudo apt update && sudo apt install -y docker.io
sudo usermod -aG docker $USER
```

## 🗂️ Directory Structure

Create organized workspace:

```bash
mkdir -p ~/chutes-deployment/{inventory,values,scripts,docs/runbooks}
cd ~/chutes-deployment

# Clone the chutes-miner repo
git clone https://github.com/rayonlabs/chutes-miner ~/git/tao-research/chutes-miner
```

Directory layout:
```
~/chutes-deployment/
├── inventory/
│   ├── local.yml           # k3d cluster definitions
│   ├── staging.yml         # (Phase 1+)
│   └── production.yml      # (Phase 3)
├── values/
│   ├── local-values.yaml   # Mock mode enabled
│   ├── staging-values.yaml # (Phase 1+)
│   └── prod-values.yaml    # (Phase 3)
├── scripts/
│   ├── setup-local-k3d.sh
│   ├── validate-local.sh
│   ├── deploy-local.sh
│   └── teardown-local.sh
└── docs/
    └── runbooks/
        ├── update-gepetto.md
        ├── add-node.md
        └── troubleshooting.md
```

## 🚀 Step 1: Create Multi-Cluster k3d Environment

### Setup Script

Create `~/chutes-deployment/scripts/setup-local-k3d.sh`:

```bash
#!/bin/bash
set -e

echo "=========================================="
echo "  Creating Local k3d Environment"
echo "=========================================="

# Cleanup any existing clusters
echo "Cleaning up existing clusters..."
k3d cluster delete chutes-control 2>/dev/null || true
k3d cluster delete chutes-gpu-0 2>/dev/null || true
k3d cluster delete chutes-gpu-1 2>/dev/null || true

# Create control plane cluster
echo ""
echo "Creating control plane cluster..."
k3d cluster create chutes-control \
  --servers 1 \
  --port "32000:32000@loadbalancer" \
  --port "32001:32001@loadbalancer" \
  --port "30080:30080@loadbalancer" \
  --port "30090:30090@loadbalancer" \
  -v "/tmp/chutes-control-data:/var/snap@all" \
  --wait

# Create GPU worker clusters (simulated)
echo ""
echo "Creating GPU worker cluster 0..."
k3d cluster create chutes-gpu-0 \
  --servers 1 \
  --port "32100:32000@loadbalancer" \
  -v "/tmp/chutes-gpu-0-data:/var/snap@all" \
  --wait

echo ""
echo "Creating GPU worker cluster 1..."
k3d cluster create chutes-gpu-1 \
  --servers 1 \
  --port "32200:32000@loadbalancer" \
  -v "/tmp/chutes-gpu-1-data:/var/snap@all" \
  --wait

# Rename contexts for consistency with production
echo ""
echo "Setting up contexts..."
kubectl config rename-context k3d-chutes-control chutes-miner-cpu-0
kubectl config rename-context k3d-chutes-gpu-0 chutes-miner-gpu-0
kubectl config rename-context k3d-chutes-gpu-1 chutes-miner-gpu-1

# Verify clusters
echo ""
echo "Verifying clusters..."
kubectl --context chutes-miner-cpu-0 get nodes
kubectl --context chutes-miner-gpu-0 get nodes
kubectl --context chutes-miner-gpu-1 get nodes

echo ""
echo "=========================================="
echo "  ✅ Local k3d Environment Ready"
echo "=========================================="
echo ""
echo "Control Plane:  http://localhost:32000"
echo "GPU Node 0:     http://localhost:32100"
echo "GPU Node 1:     http://localhost:32200"
echo "Grafana:        http://localhost:30080"
echo "Prometheus:     http://localhost:30090"
echo ""
echo "Contexts:"
echo "  - chutes-miner-cpu-0  (control plane)"
echo "  - chutes-miner-gpu-0  (GPU node 0)"
echo "  - chutes-miner-gpu-1  (GPU node 1)"
echo ""
echo "Next: Create inventory and deploy charts"
```

Make executable and run:
```bash
chmod +x ~/chutes-deployment/scripts/setup-local-k3d.sh
~/chutes-deployment/scripts/setup-local-k3d.sh
```

## 📝 Step 2: Create Local Inventory

Create `~/chutes-deployment/inventory/local.yml`:

```yaml
all:
  children:
    control:
      hosts:
        chutes-miner-cpu-0:
          ansible_connection: local
          ansible_host: localhost
          k3d_cluster: chutes-control

    workers:
      hosts:
        chutes-miner-gpu-0:
          ansible_connection: local
          ansible_host: localhost
          k3d_cluster: chutes-gpu-0
          gpu_type: "A100"  # Simulated
          hourly_cost: "1.50"

        chutes-miner-gpu-1:
          ansible_connection: local
          ansible_host: localhost
          k3d_cluster: chutes-gpu-1
          gpu_type: "L40S"  # Simulated
          hourly_cost: "1.20"

  vars:
    ansible_user: "{{ lookup('env', 'USER') }}"
    ssh_keys: []
    user: "{{ lookup('env', 'USER') }}"

    # Mock test wallet (DO NOT use in production!)
    hotkey_path: "~/.bittensor/wallets/test/hotkeys/test"

    chart_values: "~/chutes-deployment/values/local-values.yaml"
    mock_mode: true
```

## ⚙️ Step 3: Create Local Values

Create `~/chutes-deployment/values/local-values.yaml`:

```yaml
# Enable multi-cluster mode (same as production)
multiCluster: true

# Mock mode configuration
mockMode:
  enabled: true
  gpuNodes: 2
  gpuPerNode: 4
  gpuTypes:
    chutes-miner-gpu-0: "A100"
    chutes-miner-gpu-1: "L40S"

# Disable Calico for local (uses default CNI)
calico: false

# Validators (mock for local testing)
validators:
  defaultRegistry: "localhost:5000"
  defaultApi: "http://localhost:8080"
  supported:
    - hotkey: "mock_validator_test"
      registry: "localhost:5000"
      api: "http://localhost:8080"
      socket: "ws://localhost:8080/ws"

# Miner API
minerApi:
  image: parachutes/miner:k3s-latest
  imagePullPolicy: IfNotPresent
  service:
    type: NodePort
    nodePort: 32000
    port: 8000
    targetPort: 8000
  resources:
    requests:
      cpu: "250m"
      memory: "512Mi"
    limits:
      cpu: "500m"
      memory: "1Gi"

# Gepetto
gepetto:
  image: parachutes/miner:k3s-latest
  imagePullPolicy: IfNotPresent
  resources:
    requests:
      cpu: "250m"
      memory: "512Mi"
    limits:
      cpu: "500m"
      memory: "1Gi"

# PostgreSQL
postgres:
  image: postgres:16
  persistence:
    enabled: true
  resources:
    requests:
      cpu: "250m"
      memory: "512Mi"
    limits:
      cpu: "500m"
      memory: "1Gi"
  database:
    name: chutes
    user: chutes
  service:
    type: ClusterIP
    port: 5432

# Redis
redis:
  image: redis:7
  resources:
    requests:
      cpu: "100m"
      memory: "256Mi"
    limits:
      cpu: "250m"
      memory: "512Mi"
  service:
    type: ClusterIP
    port: 6379

# Cache settings (smaller for local)
cache:
  max_age_days: 7
  max_size_gb: 10
  overrides:
    chutes-miner-gpu-0: 5
    chutes-miner-gpu-1: 5

# Mock miner credentials (test only!)
minerCredentials:
  ss58Address: "5E6xfU3oNU7y1a7pQwoc31fmUjwBZ2gKcNCw8EXsdtCQieUQ"
  secretSeed: "e031170f32b4cda05df2f3cf6bc8d7687b683bbce23d9fa960c0b3fc21641b8a"
```

## 🚀 Step 4: Deploy Charts Locally

### Create Namespaces

```bash
# Control plane
kubectl create namespace chutes --context chutes-miner-cpu-0

# GPU nodes
kubectl create namespace chutes --context chutes-miner-gpu-0
kubectl create namespace chutes --context chutes-miner-gpu-1
```

### Create Secrets

```bash
# Miner credentials (mock - same for all contexts)
for ctx in chutes-miner-cpu-0 chutes-miner-gpu-0 chutes-miner-gpu-1; do
  kubectl create secret generic miner-credentials \
    --context $ctx \
    -n chutes \
    --from-literal=ss58='5E6xfU3oNU7y1a7pQwoc31fmUjwBZ2gKcNCw8EXsdtCQieUQ' \
    --from-literal=seed='e031170f32b4cda05df2f3cf6bc8d7687b683bbce23d9fa960c0b3fc21641b8a'
done
```

### Deploy Control Plane Charts

```bash
cd ~/git/tao-research/chutes-miner

helm install chutes-miner charts/chutes-miner \
  --kube-context chutes-miner-cpu-0 \
  -n chutes \
  -f ~/chutes-deployment/values/local-values.yaml
```

### Deploy GPU Charts

```bash
# GPU Node 0
helm install chutes-miner-gpu charts/chutes-miner-gpu \
  --kube-context chutes-miner-gpu-0 \
  -n chutes \
  -f ~/chutes-deployment/values/local-values.yaml

# GPU Node 1
helm install chutes-miner-gpu charts/chutes-miner-gpu \
  --kube-context chutes-miner-gpu-1 \
  -n chutes \
  -f ~/chutes-deployment/values/local-values.yaml
```

### Verify Deployments

```bash
# Control plane
kubectl get pods -n chutes --context chutes-miner-cpu-0

# Should see:
# - postgres
# - redis
# - gepetto
# - miner-api

# GPU nodes
kubectl get pods -n chutes --context chutes-miner-gpu-0
kubectl get pods -n chutes --context chutes-miner-gpu-1

# Should see:
# - agent
# - registry-proxy (daemonset)
```

## ✅ Step 5: Validation

Copy the comprehensive validation script from `docs/scripts/validate-deployment.sh` and run:

```bash
~/chutes-deployment/scripts/validate-deployment.sh local
```

All checks should pass!

## 🧙 Step 6: Customize Gepetto

This is where you optimize for profitability!

```bash
cd ~/git/tao-research/chutes-miner
cp src/chutes-miner/chutes_miner/gepetto.py ~/gepetto-custom.py
vim ~/gepetto-custom.py

# Make your changes to chute selection logic
# Test syntax
python3 -m py_compile ~/gepetto-custom.py

# Deploy to local
kubectl create configmap gepetto-code \
  --context chutes-miner-cpu-0 \
  --from-file=gepetto.py=~/gepetto-custom.py \
  -n chutes \
  -o yaml --dry-run=client | kubectl apply -f -

# Restart Gepetto
kubectl rollout restart deployment/gepetto \
  --context chutes-miner-cpu-0 \
  -n chutes

# Watch logs
kubectl logs -f deployment/gepetto \
  --context chutes-miner-cpu-0 \
  -n chutes
```

## 📚 Step 7: Write Runbooks

Document every operation as you learn it:

1. **Update Gepetto** - See `docs/runbooks/update-gepetto.md`
2. **Add GPU Node** - See `docs/runbooks/add-gpu-node.md`
3. **Troubleshooting** - See `docs/runbooks/troubleshooting.md`

Practice each operation 3-5 times in local environment.

## 🎯 Exit Criteria

Before proceeding to Phase 1, validate:

- [ ] All k3d clusters running
- [ ] All pods in Running state
- [ ] Miner API accessible: `curl http://localhost:32000/health`
- [ ] PostgreSQL accessible and initialized
- [ ] Redis accessible
- [ ] Gepetto running without CrashLoopBackOff
- [ ] Can update Gepetto ConfigMap successfully
- [ ] Can view Grafana dashboards (if deployed)
- [ ] All validation scripts pass
- [ ] Written runbooks for all operations
- [ ] Team practiced deployments 3+ times

## 🧹 Cleanup

When done with local environment:

```bash
# Delete all clusters
k3d cluster delete chutes-control chutes-gpu-0 chutes-gpu-1

# Clean up data
rm -rf /tmp/chutes-*-data
```

## 🚀 Next Steps

Once all exit criteria are met → **[Phase 1: Control Plane Validation](02-phase1-control-plane.md)**

---

**Time Investment:** 1-2 weeks
**Cost:** $0
**Outcome:** Complete understanding of tooling and operations
