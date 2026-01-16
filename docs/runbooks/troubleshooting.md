# Runbook: Troubleshooting

**Last Updated:** 2026-01-15

## Quick Diagnosis Guide

```
Is Gepetto crashing?               → See "Gepetto CrashLoopBackOff"
Is GPU node not receiving chutes?  → See "GPU Node Idle"
Database errors in logs?           → See "Database Issues"
Can't connect to services?         → See "Networking Issues"
High costs but low performance?    → See "Cost Optimization"
```

## Common Issues

### Issue 1: Gepetto CrashLoopBackOff

**Symptoms:**
- `kubectl get pods` shows Gepetto in CrashLoopBackOff
- No chute deployments happening
- Logs show Python errors

**Investigation:**
```bash
# Check pod status
kubectl get pods -n chutes -l app=gepetto

# Check logs for errors
kubectl logs deployment/gepetto -n chutes --tail=100

# Common error patterns:
# - "IndentationError" → Syntax error in gepetto.py
# - "Can't connect to database" → PostgreSQL issue
# - "Can't connect to Redis" → Redis issue
# - "ImportError" → Missing Python module
```

**Resolution:**

1. **If syntax error in gepetto.py:**
   ```bash
   # Rollback to last working version
   ~/chutes-deployment/scripts/rollback.sh production ~/chutes-backups/latest.tar.gz
   ```

2. **If database connection error:**
   ```bash
   # Check PostgreSQL is running
   kubectl get pods -n chutes -l app=postgres

   # If not running, check logs
   kubectl logs deployment/postgres -n chutes

   # Restart PostgreSQL
   kubectl rollout restart deployment/postgres -n chutes
   ```

3. **If Redis connection error:**
   ```bash
   # Check Redis is running
   kubectl get pods -n chutes -l app=redis

   # Test Redis connectivity
   kubectl exec -it deployment/redis -n chutes -- redis-cli ping

   # Should return "PONG"
   ```

---

### Issue 2: GPU Node Not Receiving Chutes

**Symptoms:**
- GPU node online but idle
- Gepetto logs don't mention the node
- No pods in `chutes-jobs` namespace on GPU node

**Investigation:**
```bash
# 1. Check if node in database
kubectl exec -it deployment/postgres -n chutes -- \
  psql -U chutes -d chutes -c "SELECT * FROM servers WHERE name='chutes-miner-gpu-N';"

# Should return 1 row

# 2. Check GPU status
kubectl exec -it deployment/postgres -n chutes -- \
  psql -U chutes -d chutes -c \
  "SELECT * FROM gpus WHERE server_id=(SELECT id FROM servers WHERE name='chutes-miner-gpu-N');"

# Should return GPUs for this server

# 3. Check GraVal validation
curl http://GPU_IP:8000/ping
# Should return "pong"

curl http://GPU_IP:8000/devices
# Should return GPU device info

# 4. Check Agent API
curl http://GPU_IP:32000/health
# Should return OK

# 5. Check Gepetto logs for server selection
kubectl logs deployment/gepetto -n chutes | grep -A10 "selecting server"
```

**Resolution:**

1. **If node not in database:**
   ```bash
   # Re-add node to miner
   chutes-miner add-node \
     --name chutes-miner-gpu-N \
     --validator <VALIDATOR_HOTKEY> \
     --hourly-cost <COST> \
     --gpu-short-ref <GPU_TYPE> \
     --hotkey ~/.bittensor/wallets/production/hotkeys/production \
     --agent-api http://GPU_IP:32000 \
     --miner-api http://CONTROL_IP:32000
   ```

2. **If GPUs not validated:**
   ```bash
   # Re-verify GPUs
   chutes-miner verify-gpus \
     --server chutes-miner-gpu-N \
     --hotkey ~/.bittensor/wallets/production/hotkeys/production \
     --miner-api http://CONTROL_IP:32000
   ```

3. **If Gepetto not considering server:**
   ```bash
   # Check Gepetto strategy
   # May be filtering out this server due to:
   # - Cost too high
   # - GPU type not needed
   # - Server marked as unhealthy

   # Review gepetto.py selection logic
   # Adjust if needed
   ```

4. **Restart Gepetto to re-evaluate:**
   ```bash
   kubectl rollout restart deployment/gepetto -n chutes
   ```

---

### Issue 3: Database Connection Errors

**Symptoms:**
- Multiple pods showing database errors
- "connection refused" in logs
- "too many connections" errors

**Investigation:**
```bash
# Check PostgreSQL pod
kubectl get pods -n chutes -l app=postgres

# Check PostgreSQL logs
kubectl logs deployment/postgres -n chutes | tail -50

# Check connection count
kubectl exec -it deployment/postgres -n chutes -- \
  psql -U chutes -d chutes -c \
  "SELECT COUNT(*) FROM pg_stat_activity;"

# Check for long-running queries
kubectl exec -it deployment/postgres -n chutes -- \
  psql -U chutes -d chutes -c \
  "SELECT pid, now() - pg_stat_activity.query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'active'
   ORDER BY duration DESC;"
```

**Resolution:**

1. **If PostgreSQL pod not running:**
   ```bash
   # Check persistent volume
   kubectl get pv,pvc -n chutes

   # Restart PostgreSQL
   kubectl rollout restart deployment/postgres -n chutes

   # Wait for Ready
   kubectl wait --for=condition=ready pod -l app=postgres -n chutes --timeout=300s
   ```

2. **If too many connections:**
   ```bash
   # Kill idle connections
   kubectl exec -it deployment/postgres -n chutes -- \
     psql -U chutes -d chutes -c \
     "SELECT pg_terminate_backend(pid)
      FROM pg_stat_activity
      WHERE state = 'idle' AND now() - state_change > interval '5 minutes';"

   # Restart services to reconnect
   kubectl rollout restart deployment/gepetto -n chutes
   kubectl rollout restart deployment/miner-api -n chutes
   ```

3. **If database corrupted:**
   ```bash
   # Restore from backup
   ~/chutes-deployment/scripts/rollback.sh production ~/chutes-backups/latest.tar.gz
   ```

---

### Issue 4: High Costs, Low Performance

**Symptoms:**
- Daily costs higher than expected
- Low chute deployment rate
- Low GPU utilization

**Investigation:**
```bash
# 1. Check actual deployment count
kubectl exec -it deployment/postgres -n chutes -- \
  psql -U chutes -d chutes -c \
  "SELECT COUNT(*) as total_deployments,
          COUNT(CASE WHEN status='running' THEN 1 END) as running,
          COUNT(CASE WHEN status='failed' THEN 1 END) as failed
   FROM deployments
   WHERE created_at > NOW() - INTERVAL '24 hours';"

# 2. Check GPU utilization
ssh GPU_NODE 'nvidia-smi'

# 3. Check cost per deployment
# Compare:
# - Daily infrastructure cost (from provider billing)
# - Number of successful deployments
# - Compute hours provided

# 4. Review Gepetto selection logic
kubectl logs deployment/gepetto -n chutes | grep -i "selecting\|rejecting"
```

**Resolution:**

1. **If deployment rate too low:**
   - Review Gepetto strategy
   - May be too conservative
   - Adjust selection thresholds

2. **If high failure rate:**
   - Check failure reasons in logs
   - Common causes:
     - Image pull errors → Registry auth issue
     - OOMKilled → Increase memory limits
     - GPU allocation fails → GraVal issue

3. **If GPU underutilized:**
   - Not enough chutes available
   - Strategy too selective
   - Adjust to deploy more aggressively

4. **If infrastructure oversized:**
   - Consider smaller/cheaper GPU type
   - Remove underutilized GPU nodes
   - Optimize resource requests

---

### Issue 5: Networking/Connectivity

**Symptoms:**
- Can't access services via NodePort
- Pod-to-pod communication fails
- Registry authentication fails

**Investigation:**
```bash
# 1. Check node networking
kubectl get nodes -o wide

# 2. Check service endpoints
kubectl get svc -n chutes
kubectl get endpoints -n chutes

# 3. Test NodePort accessibility
curl http://CONTROL_IP:32000/health
curl http://GPU_IP:32000/health
curl http://GPU_IP:30500/v2/

# 4. Check firewall rules (provider console)

# 5. Check k3s networking
kubectl get pods -n kube-system
```

**Resolution:**

1. **If NodePort not accessible:**
   - Check firewall allows port
   - Check service is type NodePort
   - Check pod is running and ready

2. **If pod-to-pod fails:**
   - Check k3s networking pods running
   - Check CoreDNS working:
     ```bash
     kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup kubernetes.default
     ```

3. **If registry authentication fails:**
   - Check miner-credentials secret exists
   - Check registry-proxy pod running
   - Check logs:
     ```bash
     kubectl logs daemonset/registry-proxy -n chutes
     ```

---

## Emergency Procedures

### Complete System Failure

```bash
# 1. Assess damage
kubectl get pods --all-namespaces

# 2. Check persistent data
kubectl get pv,pvc --all-namespaces

# 3. Restore from backup
~/chutes-deployment/scripts/rollback.sh production ~/chutes-backups/latest.tar.gz

# 4. If backup fails, redeploy
~/chutes-deployment/scripts/deploy.sh production

# 5. Verify
~/chutes-deployment/scripts/validate-deployment.sh production
```

### Data Loss

```bash
# 1. Stop all write operations
kubectl scale deployment/gepetto --replicas=0 -n chutes

# 2. Assess what's lost
kubectl exec -it deployment/postgres -n chutes -- \
  psql -U chutes -d chutes -c "\dt"

# 3. Restore database from backup
cat ~/chutes-backups/latest.sql | \
  kubectl exec -i deployment/postgres -n chutes -- \
  psql -U chutes chutes

# 4. Restart services
kubectl scale deployment/gepetto --replicas=1 -n chutes
```

## Prevention

1. **Automated backups** - Daily database dumps
2. **Monitoring** - Set up alerts for anomalies
3. **Testing** - Always test changes in staging first
4. **Documentation** - Keep runbooks updated
5. **Capacity planning** - Monitor growth trends

## Related Runbooks

- [Update Gepetto](update-gepetto.md)
- [Backup and Restore](backup-restore.md)
- [Add GPU Node](add-gpu-node.md)

---

**Keep Calm and Debug On** 🐛🔍
