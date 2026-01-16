#!/bin/bash
# Universal deployment validation script
# Works across local, staging, and production environments

set -e

ENVIRONMENT="${1:-local}"
INVENTORY="${2:-$HOME/chutes-deployment/inventory/${ENVIRONMENT}.yml}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
check_pass=0
check_fail=0
check_warn=0

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

check() {
    local description="$1"
    local test_cmd="$2"
    local critical="${3:-true}"

    echo -n "Checking: $description... "

    if eval "$test_cmd" &>/dev/null; then
        echo -e "${GREEN}✅${NC}"
        ((check_pass++))
        return 0
    else
        if [[ "$critical" == "true" ]]; then
            echo -e "${RED}❌ CRITICAL${NC}"
            ((check_fail++))
            return 1
        else
            echo -e "${YELLOW}⚠️  WARNING${NC}"
            ((check_warn++))
            return 0
        fi
    fi
}

# Parse inventory to get control plane IP
get_control_ip() {
    if [[ "$ENVIRONMENT" == "local" ]]; then
        echo "localhost"
    else
        # Try to get from inventory using ansible-inventory
        if command -v ansible-inventory &> /dev/null && [[ -f "$INVENTORY" ]]; then
            ansible-inventory -i "$INVENTORY" --host chutes-miner-cpu-0 2>/dev/null \
                | jq -r '.ansible_host // .external_ip // empty' || echo ""
        else
            echo ""
        fi
    fi
}

get_gpu_nodes() {
    if [[ "$ENVIRONMENT" == "local" ]]; then
        echo "chutes-miner-gpu-0 chutes-miner-gpu-1"
    else
        if command -v ansible-inventory &> /dev/null && [[ -f "$INVENTORY" ]]; then
            ansible-inventory -i "$INVENTORY" --list 2>/dev/null \
                | jq -r '.workers.hosts[]? // empty' || echo ""
        else
            echo ""
        fi
    fi
}

get_node_ip() {
    local node="$1"
    if [[ "$ENVIRONMENT" == "local" ]]; then
        echo "localhost"
    else
        if command -v ansible-inventory &> /dev/null && [[ -f "$INVENTORY" ]]; then
            ansible-inventory -i "$INVENTORY" --host "$node" 2>/dev/null \
                | jq -r '.ansible_host // .external_ip // empty' || echo ""
        else
            echo ""
        fi
    fi
}

CONTROL_IP=$(get_control_ip)

echo "=========================================="
echo "  Chutes Miner Deployment Validation"
echo "=========================================="
echo "  Environment: $ENVIRONMENT"
echo "  Control IP:  ${CONTROL_IP:-Not Found}"
echo "  Inventory:   $INVENTORY"
echo "=========================================="
echo ""

if [[ -z "$CONTROL_IP" ]]; then
    log_error "Could not determine control plane IP"
    log_info "For local environment, ensure k3d clusters are running"
    log_info "For cloud environments, check inventory file exists: $INVENTORY"
    exit 1
fi

# ==========================================
# Infrastructure Checks
# ==========================================
log_step "=== Infrastructure Checks ==="
echo ""

check "Control plane is reachable" \
    "ping -c 1 -W 2 $CONTROL_IP"

if [[ "$ENVIRONMENT" != "local" ]]; then
    check "SSH access to control plane" \
        "timeout 5 ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no ubuntu@${CONTROL_IP} 'echo ok'" \
        false
fi

check "Kubernetes API is accessible" \
    "kubectl --context chutes-miner-cpu-0 get nodes"

check "Control plane node is Ready" \
    "kubectl --context chutes-miner-cpu-0 get nodes | grep -q Ready"

# ==========================================
# Service Checks
# ==========================================
echo ""
log_step "=== Service Checks ==="
echo ""

if [[ "$ENVIRONMENT" == "local" ]]; then
    MINER_API_URL="http://localhost:32000/health"
else
    MINER_API_URL="http://${CONTROL_IP}:32000/health"
fi

check "Miner API is responding" \
    "curl -sf -m 5 $MINER_API_URL"

check "PostgreSQL pod is Running" \
    "kubectl --context chutes-miner-cpu-0 -n chutes get pod -l app=postgres | grep -q Running"

check "Redis pod is Running" \
    "kubectl --context chutes-miner-cpu-0 -n chutes get pod -l app=redis | grep -q Running"

check "Gepetto pod is Running" \
    "kubectl --context chutes-miner-cpu-0 -n chutes get pod -l app=gepetto | grep -q Running"

check "Gepetto has no CrashLoopBackOff" \
    "! kubectl --context chutes-miner-cpu-0 -n chutes get pod -l app=gepetto | grep -q CrashLoopBackOff"

# ==========================================
# Database Checks
# ==========================================
echo ""
log_step "=== Database Checks ==="
echo ""

check "Can connect to PostgreSQL" \
    "kubectl --context chutes-miner-cpu-0 -n chutes exec deployment/postgres -- psql -U chutes -d chutes -c 'SELECT 1'"

check "Database schema initialized" \
    "kubectl --context chutes-miner-cpu-0 -n chutes exec deployment/postgres -- psql -U chutes -d chutes -c '\dt' | grep -q servers"

check "Servers table has expected columns" \
    "kubectl --context chutes-miner-cpu-0 -n chutes exec deployment/postgres -- psql -U chutes -d chutes -c '\d servers' | grep -q 'name'" \
    false

check "GPUs table exists" \
    "kubectl --context chutes-miner-cpu-0 -n chutes exec deployment/postgres -- psql -U chutes -d chutes -c '\dt' | grep -q gpus" \
    false

# ==========================================
# Configuration Checks
# ==========================================
echo ""
log_step "=== Configuration Checks ==="
echo ""

check "Gepetto ConfigMap exists" \
    "kubectl --context chutes-miner-cpu-0 -n chutes get configmap gepetto-code" \
    false

check "Miner credentials secret exists" \
    "kubectl --context chutes-miner-cpu-0 -n chutes get secret miner-credentials"

check "Validator configuration is set" \
    "kubectl --context chutes-miner-cpu-0 -n chutes get deployment gepetto -o json | jq -e '.spec.template.spec.containers[0].env[] | select(.name==\"VALIDATORS\")'" \
    false

# ==========================================
# GPU Node Checks
# ==========================================
GPU_NODES=$(get_gpu_nodes)

if [[ -n "$GPU_NODES" ]]; then
    echo ""
    log_step "=== GPU Node Checks ==="
    echo ""

    for node in $GPU_NODES; do
        NODE_IP=$(get_node_ip "$node")

        if [[ -z "$NODE_IP" ]]; then
            log_warn "Could not get IP for node: $node"
            continue
        fi

        echo ""
        log_info "Checking node: $node ($NODE_IP)"

        check "GPU node $node is reachable" \
            "ping -c 1 -W 2 $NODE_IP" \
            false

        check "GPU node $node k3s is running" \
            "kubectl --context $node get nodes 2>/dev/null" \
            false

        if [[ "$ENVIRONMENT" == "local" ]]; then
            AGENT_URL="http://localhost:${NODE_IP##*:}/health"
        else
            AGENT_URL="http://${NODE_IP}:32000/health"
        fi

        check "GPU node $node agent is responding" \
            "curl -sf -m 5 $AGENT_URL" \
            false

        if [[ "$ENVIRONMENT" != "local" ]]; then
            check "GPU node $node has NVIDIA GPU" \
                "timeout 10 ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no ubuntu@${NODE_IP} 'nvidia-smi' 2>/dev/null | grep -q GPU" \
                false

            check "GPU node $node GraVal bootstrap responding" \
                "curl -sf -m 5 http://${NODE_IP}:8000/ping | grep -q pong" \
                false
        fi
    done
else
    log_info "No GPU nodes configured (this is OK for Phase 0 and Phase 1)"
fi

# ==========================================
# Monitoring Checks
# ==========================================
echo ""
log_step "=== Monitoring Checks ==="
echo ""

if [[ "$ENVIRONMENT" == "local" ]]; then
    GRAFANA_URL="http://localhost:30080/login"
    PROMETHEUS_URL="http://localhost:30090/api/v1/targets"
else
    GRAFANA_URL="http://${CONTROL_IP}:30080/login"
    PROMETHEUS_URL="http://${CONTROL_IP}:30090/api/v1/targets"
fi

check "Grafana is accessible" \
    "curl -sf -m 5 $GRAFANA_URL" \
    false

check "Prometheus is accessible" \
    "curl -sf -m 5 $PROMETHEUS_URL" \
    false

check "Prometheus is scraping targets" \
    "curl -sf -m 5 $PROMETHEUS_URL | jq -e '.data.activeTargets | length > 0'" \
    false

# ==========================================
# Deployment Health Checks (if GPU nodes exist)
# ==========================================
if [[ -n "$GPU_NODES" && "$ENVIRONMENT" != "local" ]]; then
    echo ""
    log_step "=== Deployment Health Checks ==="
    echo ""

    check "Recent deployments exist" \
        "kubectl --context chutes-miner-cpu-0 -n chutes exec deployment/postgres -- \
        psql -U chutes -d chutes -t -c \
        \"SELECT COUNT(*) FROM deployments WHERE created_at > NOW() - INTERVAL '24 hours';\" \
        | tr -d ' ' | grep -qE '^[0-9]+$'" \
        false

    check "Deployment success rate > 50%" \
        "kubectl --context chutes-miner-cpu-0 -n chutes exec deployment/postgres -- \
        psql -U chutes -d chutes -t -c \
        \"SELECT CASE WHEN COUNT(*) = 0 THEN 1
                     WHEN SUM(CASE WHEN status='running' THEN 1 ELSE 0 END)::float / COUNT(*) > 0.5 THEN 1
                     ELSE 0 END
         FROM deployments WHERE created_at > NOW() - INTERVAL '24 hours';\" \
        | tr -d ' ' | grep -q 1" \
        false
fi

# ==========================================
# Summary
# ==========================================
echo ""
echo "=========================================="
echo "  Validation Summary"
echo "=========================================="
echo -e "Passed:   ${GREEN}$check_pass${NC}"
echo -e "Warnings: ${YELLOW}$check_warn${NC}"
echo -e "Failed:   ${RED}$check_fail${NC}"
echo ""

if [[ $check_fail -gt 0 ]]; then
    log_error "Validation FAILED - $check_fail critical checks failed"
    echo ""
    echo "Common fixes:"
    echo "  - Ensure k3d/k3s is running"
    echo "  - Check firewall rules allow required ports"
    echo "  - Verify inventory file is correct"
    echo "  - Check pods are Running: kubectl get pods -n chutes --all-namespaces"
    echo "  - Review logs: kubectl logs deployment/<pod> -n chutes"
    echo ""
    exit 1
else
    log_info "Validation PASSED - All critical checks passed!"

    if [[ $check_warn -gt 0 ]]; then
        log_warn "$check_warn non-critical warnings found"
        echo "  Review warnings above and address if needed"
    fi

    echo ""
    echo "Next steps:"
    if [[ "$ENVIRONMENT" == "local" ]]; then
        echo "  - Customize Gepetto strategy"
        echo "  - Practice day-2 operations"
        echo "  - Write runbooks"
        echo "  - Proceed to Phase 1 when ready"
    elif [[ -z "$GPU_NODES" ]]; then
        echo "  - Add GPU nodes to inventory"
        echo "  - Deploy GPU nodes with Ansible"
        echo "  - Run validation again"
    else
        echo "  - Monitor Gepetto logs: kubectl logs -f deployment/gepetto -n chutes"
        echo "  - Check Grafana: http://${CONTROL_IP}:30080"
        echo "  - Watch for chute deployments"
    fi
    echo ""
    exit 0
fi
