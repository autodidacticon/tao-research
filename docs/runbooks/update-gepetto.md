# Runbook: Update Gepetto Strategy

**Last Updated:** 2026-01-15
**Applies To:** All environments (local, staging, production)

## Overview

Gepetto is the core optimization component that selects which chutes to deploy, scale, or remove. Updating Gepetto strategy is the primary way to improve miner profitability.

## When to Use

- Optimizing chute selection algorithm
- Adjusting cost/performance tradeoffs
- Responding to subnet changes
- Implementing new strategies
- Fixing bugs in selection logic

## Prerequisites

- [ ] Changes tested locally (Phase 0) OR in staging (Phase 2)
- [ ] Backup created
- [ ] Off-peak hours (if production)
- [ ] Syntax validated
- [ ] Team notified (if production)

## Procedure

### Step 1: Create Backup

```bash
# Production
~/chutes-deployment/scripts/backup-state.sh production

# Staging
~/chutes-deployment/scripts/backup-state.sh staging

# Verify backup created
ls -lh ~/chutes-backups/
```

### Step 2: Edit Gepetto Locally

```bash
cd ~/git/tao-research/chutes-miner

# Create copy for editing
cp src/chutes-miner/chutes_miner/gepetto.py ~/gepetto-new.py

# Edit with your preferred editor
vim ~/gepetto-new.py

# Example changes:
# - Adjust selection thresholds
# - Modify cost optimization
# - Add new selection criteria
# - Change scaling behavior
```

### Step 3: Validate Syntax

```bash
# Python syntax check
python3 -m py_compile ~/gepetto-new.py

# If no output, syntax is valid
# If errors, fix and retry
```

### Step 4: Test in Local/Staging First

**Local:**
```bash
kubectl create configmap gepetto-code \
  --context chutes-miner-cpu-0 \
  --from-file=gepetto.py=~/gepetto-new.py \
  -n chutes \
  -o yaml --dry-run=client | kubectl apply -f -

kubectl rollout restart deployment/gepetto \
  --context chutes-miner-cpu-0 \
  -n chutes

# Watch logs for 5-10 minutes
kubectl logs -f deployment/gepetto -n chutes --context chutes-miner-cpu-0
```

**Staging (if you have staging environment):**
```bash
# Get kubeconfig or SSH
ssh ubuntu@STAGING_IP

# Create ConfigMap
sudo kubectl create configmap gepetto-code \
  --from-file=gepetto.py=/path/to/gepetto-new.py \
  -n chutes \
  -o yaml --dry-run=client | sudo kubectl apply -f -

# Restart
sudo kubectl rollout restart deployment/gepetto -n chutes

# Monitor logs
sudo kubectl logs -f deployment/gepetto -n chutes

# Watch for 30 minutes minimum
# Check for:
# - No crashes
# - No errors in logs
# - Expected behavior changes
# - Chutes deploying normally
```

### Step 5: Deploy to Production (If Staging OK)

```bash
# SSH to production control plane
ssh ubuntu@PRODUCTION_CONTROL_IP

# Copy new gepetto.py to server
# (Use scp from local machine first)
exit

# From local machine
scp ~/gepetto-new.py ubuntu@PRODUCTION_CONTROL_IP:~/gepetto.py

# Back to SSH
ssh ubuntu@PRODUCTION_CONTROL_IP

# Create/update ConfigMap
sudo kubectl create configmap gepetto-code \
  --from-file=gepetto.py=~/gepetto.py \
  -n chutes \
  -o yaml --dry-run=client | sudo kubectl apply -f -

# Restart Gepetto
sudo kubectl rollout restart deployment/gepetto -n chutes

# Monitor immediately
sudo kubectl logs -f deployment/gepetto -n chutes
```

### Step 6: Validate Deployment

```bash
# Check pod is running
sudo kubectl get pods -n chutes -l app=gepetto

# Expected output:
# NAME                       READY   STATUS    RESTARTS   AGE
# gepetto-xxxxxxxxxx-xxxxx   1/1     Running   0          30s

# Check logs for errors
sudo kubectl logs deployment/gepetto -n chutes | grep -i error

# Check deployments are happening
sudo kubectl get pods -n chutes-jobs

# Query recent deployments
sudo kubectl exec -it deployment/postgres -n chutes -- \
  psql -U chutes -d chutes -c \
  "SELECT id, chute_id, status, created_at FROM deployments ORDER BY created_at DESC LIMIT 10;"
```

### Step 7: Monitor for 1-2 Hours

**What to watch:**

1. **Pod Status**
   ```bash
   watch sudo kubectl get pods -n chutes -l app=gepetto
   ```
   Should stay Running, no CrashLoopBackOff

2. **Error Logs**
   ```bash
   sudo kubectl logs -f deployment/gepetto -n chutes 2>&1 | grep -i error
   ```
   Should see no errors

3. **Deployment Rate**
   ```bash
   watch -n 30 'sudo kubectl get pods -n chutes-jobs | wc -l'
   ```
   Should be similar to before (unless strategy intentionally changes this)

4. **Grafana Dashboards**
   - Open http://CONTROL_IP:30080
   - Check chute deployment rate
   - Check GPU utilization
   - Look for anomalies

## Rollback Procedure

If issues detected:

```bash
# Option A: Restore from backup (safest)
~/chutes-deployment/scripts/rollback.sh production ~/chutes-backups/production-TIMESTAMP.tar.gz

# Option B: Revert ConfigMap manually
ssh ubuntu@PRODUCTION_CONTROL_IP

# Get previous version
sudo kubectl get configmap gepetto-code -n chutes -o yaml > gepetto-backup.yaml

# Restore previous version (if you saved it)
sudo kubectl apply -f gepetto-previous.yaml

# Restart
sudo kubectl rollout restart deployment/gepetto -n chutes
```

## Success Criteria

- [ ] Gepetto pod Running without CrashLoopBackOff
- [ ] No errors in logs for 1+ hours
- [ ] Chutes deploying within expected timeframes
- [ ] GPU utilization within normal ranges
- [ ] No unexpected cost increases
- [ ] Expected behavior changes visible

## Common Issues

### Issue: CrashLoopBackOff

**Cause:** Syntax error or import error

**Solution:**
```bash
# Check logs for Python traceback
sudo kubectl logs deployment/gepetto -n chutes | tail -50

# Common errors:
# - IndentationError: Fix indentation
# - NameError: Check variable names
# - ImportError: Missing import statement

# Fix locally, re-test, re-deploy
```

### Issue: No Chute Deployments

**Cause:** Logic error in selection algorithm

**Solution:**
```bash
# Check Gepetto logs for selection logic
sudo kubectl logs deployment/gepetto -n chutes | grep -i "selecting\|choosing\|deciding"

# Review your changes to selection criteria
# May be too restrictive
# Rollback and adjust
```

### Issue: Excessive Deployments

**Cause:** Too aggressive strategy

**Solution:**
```bash
# Check deployment rate
sudo kubectl exec -it deployment/postgres -n chutes -- \
  psql -U chutes -d chutes -c \
  "SELECT COUNT(*) FROM deployments WHERE created_at > NOW() - INTERVAL '1 hour';"

# If abnormally high, rollback immediately
# Adjust thresholds
# Re-deploy
```

## Best Practices

1. **Always test locally first**
2. **Then test in staging**
3. **Make small, incremental changes**
4. **Document what you changed and why**
5. **Monitor for several hours after deployment**
6. **Keep backups of working versions**
7. **Update Gepetto during off-peak hours**
8. **Have rollback plan ready**

## Example: Adding Logging

```python
# Before
def select_chute(self, available_chutes):
    # Selection logic
    return selected_chute

# After (with logging)
def select_chute(self, available_chutes):
    logger.info(f"Selecting from {len(available_chutes)} available chutes")

    # Selection logic
    selected = selected_chute

    if selected:
        logger.info(f"Selected chute {selected.id} with cost {selected.cost}")
    else:
        logger.warning("No suitable chute found")

    return selected
```

## Example: Adjusting Thresholds

```python
# Before
MIN_PROFIT_MARGIN = 0.1  # 10% minimum profit

# After (more aggressive)
MIN_PROFIT_MARGIN = 0.05  # 5% minimum profit

# This will deploy more chutes, potentially lower value
# Monitor profitability impact!
```

## Notes

- Gepetto updates are **non-destructive** - existing chutes continue running
- Changes take effect on next selection cycle (typically within minutes)
- Can update multiple times per day if needed
- Keep a log of all changes for analysis

## Related Runbooks

- [Troubleshooting](troubleshooting.md)
- [Backup and Restore](backup-restore.md)

---

**Time Required:** 15-30 minutes
**Risk Level:** Medium (rollback available)
**Frequency:** As needed for optimization
