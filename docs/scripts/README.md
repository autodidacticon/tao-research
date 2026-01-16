# Deployment Scripts

This directory contains automation scripts for chutes-miner deployment and operations.

## Available Scripts

### validate-deployment.sh

**Purpose:** Universal validation script that works across all environments (local, staging, production)

**Usage:**
```bash
./validate-deployment.sh <environment> [inventory-file]

# Examples:
./validate-deployment.sh local
./validate-deployment.sh staging
./validate-deployment.sh production
```

**What it checks:**
- Infrastructure (node reachability, k8s API)
- Services (PostgreSQL, Redis, Gepetto, Miner API)
- Database (connectivity, schema initialization)
- Configuration (ConfigMaps, Secrets)
- GPU nodes (if configured)
- Monitoring (Grafana, Prometheus)
- Deployment health (success rate)

**Exit codes:**
- `0` - All critical checks passed
- `1` - One or more critical checks failed

---

## Additional Scripts to Create

Based on the deployment documentation, you should create these additional scripts in your `~/chutes-deployment/scripts/` directory:

### setup-local-k3d.sh

Creates multi-cluster k3d environment for local development.

See: `docs/deployment/01-phase0-local.md` for implementation

### deploy.sh

Universal deployment wrapper for all environments.

See: `docs/deployment/00-overview.md` for implementation

### backup-state.sh

Creates backups of PostgreSQL database and Kubernetes configurations.

```bash
#!/bin/bash
# Usage: ./backup-state.sh <environment>

ENVIRONMENT="${1:-production}"
BACKUP_DIR="$HOME/chutes-backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="${ENVIRONMENT}-${TIMESTAMP}"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

mkdir -p "$BACKUP_PATH"

echo "Creating backup: $BACKUP_NAME"

# Backup PostgreSQL
kubectl --context chutes-miner-cpu-0 -n chutes exec deployment/postgres -- \
    pg_dump -U chutes chutes > "$BACKUP_PATH/postgres-dump.sql"

# Backup Gepetto ConfigMap
kubectl --context chutes-miner-cpu-0 -n chutes get configmap gepetto-code -o yaml \
    > "$BACKUP_PATH/gepetto-configmap.yaml"

# Backup miner credentials
kubectl --context chutes-miner-cpu-0 -n chutes get secret miner-credentials -o yaml \
    > "$BACKUP_PATH/miner-credentials.yaml"

# Create tarball
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"
rm -rf "$BACKUP_PATH"

echo "✅ Backup complete: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
```

### rollback.sh

Restores from backup.

```bash
#!/bin/bash
# Usage: ./rollback.sh <environment> <backup-file>

ENVIRONMENT="${1}"
BACKUP_FILE="${2}"

if [[ -z "$ENVIRONMENT" || -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 <environment> <backup_file>"
    exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

read -p "⚠️  Rollback $ENVIRONMENT to $BACKUP_FILE? (yes/no): " response
[[ "$response" != "yes" ]] && { echo "Aborted"; exit 1; }

BACKUP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$BACKUP_DIR"

# Restore PostgreSQL
kubectl --context chutes-miner-cpu-0 -n chutes exec -i deployment/postgres -- \
    psql -U chutes chutes < "$BACKUP_DIR"/*/postgres-dump.sql

# Restore Gepetto ConfigMap
kubectl --context chutes-miner-cpu-0 -n chutes apply -f "$BACKUP_DIR"/*/gepetto-configmap.yaml

# Restart Gepetto
kubectl --context chutes-miner-cpu-0 -n chutes rollout restart deployment/gepetto

echo "✅ Rollback complete"
```

### get-control-ip.sh

Helper to get control plane IP for environment.

```bash
#!/bin/bash
# Usage: ./get-control-ip.sh <environment>

ENVIRONMENT="${1:-local}"
INVENTORY="$HOME/chutes-deployment/inventory/${ENVIRONMENT}.yml"

if [[ "$ENVIRONMENT" == "local" ]]; then
    echo "localhost"
else
    ansible-inventory -i "$INVENTORY" --host chutes-miner-cpu-0 \
        | jq -r '.ansible_host // .external_ip'
fi
```

### add-node-to-miner.sh

Helper to add GPU node to miner inventory.

```bash
#!/bin/bash
# Usage: ./add-node-to-miner.sh <environment> <node-name>

ENVIRONMENT="${1}"
NODE_NAME="${2}"
INVENTORY="$HOME/chutes-deployment/inventory/${ENVIRONMENT}.yml"

# Extract node details from inventory
NODE_INFO=$(ansible-inventory -i "$INVENTORY" --host "$NODE_NAME")
NODE_IP=$(echo "$NODE_INFO" | jq -r '.ansible_host // .external_ip')
GPU_TYPE=$(echo "$NODE_INFO" | jq -r '.gpu_type // "unknown"')
HOURLY_COST=$(echo "$NODE_INFO" | jq -r '.hourly_cost // "0"')

# Get hotkey path and validator from inventory vars
HOTKEY_PATH=$(ansible-inventory -i "$INVENTORY" --list | jq -r '.all.vars.hotkey_path')
VALIDATOR=$(ansible-inventory -i "$INVENTORY" --list | jq -r '.all.vars.validator // "5Dt7HZ7Zpw4DppPxFM7Ke3Cm7sDAWhsZXmM5ZAmE7dSVJbcQ"')

# Get miner API IP
MINER_API_IP=$(ansible-inventory -i "$INVENTORY" --host chutes-miner-cpu-0 | jq -r '.ansible_host // .external_ip')

echo "Adding node to miner:"
echo "  Node: $NODE_NAME"
echo "  IP: $NODE_IP"
echo "  GPU Type: $GPU_TYPE"
echo "  Hourly Cost: $HOURLY_COST"

chutes-miner add-node \
  --name "$NODE_NAME" \
  --validator "$VALIDATOR" \
  --hourly-cost "$HOURLY_COST" \
  --gpu-short-ref "$GPU_TYPE" \
  --hotkey "$HOTKEY_PATH" \
  --agent-api "http://${NODE_IP}:32000" \
  --miner-api "http://${MINER_API_IP}:32000"
```

---

## Script Organization

```
~/chutes-deployment/scripts/
├── setup-local-k3d.sh       # Create local k3d clusters
├── validate-deployment.sh   # Universal validation (from docs)
├── deploy.sh                # Deploy to any environment
├── backup-state.sh          # Create backups
├── rollback.sh              # Restore from backups
├── get-control-ip.sh        # Get control plane IP
└── add-node-to-miner.sh     # Add GPU node to inventory
```

## Best Practices

1. **Always validate after deployment:**
   ```bash
   ./deploy.sh staging
   ./validate-deployment.sh staging
   ```

2. **Always backup before changes:**
   ```bash
   ./backup-state.sh production
   # Make changes
   # If issues:
   ./rollback.sh production ~/chutes-backups/latest.tar.gz
   ```

3. **Test in local/staging first:**
   ```bash
   ./validate-deployment.sh local     # Should pass
   ./validate-deployment.sh staging   # Should pass
   ./validate-deployment.sh production # Now safe
   ```

4. **Keep scripts versioned:**
   - Store in git repository
   - Document changes
   - Test before using in production

---

**Note:** The validation script (`validate-deployment.sh`) is provided complete in this directory. The other scripts are documented above and in the deployment guides - you should create them as needed.
