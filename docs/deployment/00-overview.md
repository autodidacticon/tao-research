# Deployment Strategy Overview

## 🎯 Goal

Deploy production-ready chutes-miner with **maximum confidence** and **minimum waste**, ensuring test/production consistency.

## 🔑 Key Insight

Chutes-miner requires **bare metal or VM** with **dedicated static IPs**. This eliminates cheap container providers (Vast.ai, RunPod) and fundamentally changes the cost/testing strategy.

You **cannot avoid GPU costs** for testing since cheap GPU providers don't work. The strategy must minimize **TIME** spent on expensive resources, not eliminate them entirely.

## 📊 Four-Phase Strategy

### Phase 0: Local Mastery (1-2 weeks, $0)

**Objective:** Achieve 100% confidence in tooling, configs, and business logic **before** touching cloud infrastructure.

**Environment:** k3d (k3s in Docker) on your laptop

**What You'll Build:**
- Multi-cluster k3d setup mimicking production
- Full Helm chart deployment with mock mode
- Gepetto strategy development
- Complete runbooks for all operations

**Exit Criteria:**
- All validation scripts pass
- Can deploy/update/rollback Gepetto
- Team practiced operations 3+ times
- Written documentation complete

**Cost:** $0
**Time:** 1-2 weeks
**Risk:** None - completely safe sandbox

---

### Phase 1: Cloud Control Plane (2-4 days, $5-20)

**Objective:** Validate Ansible automation, networking, and infrastructure on real cloud **WITHOUT** expensive GPU nodes.

**Environment:** 1x CPU-only cloud server (hourly billing)

**What You'll Validate:**
- Ansible playbook execution
- k3s installation
- PostgreSQL persistence
- Networking/firewall configuration
- Helm chart deployment

**Exit Criteria:**
- Ansible successfully provisions server
- k3s installed and healthy
- All infrastructure services running
- No networking issues
- Can SSH and manage remotely

**Cost:** $5-20 (48-96 hours @ hourly rates)
**Time:** 2-4 days
**Risk:** Low - cheap validation

**DESTROY SERVER AFTER VALIDATION** to stop costs

---

### Phase 2: Single GPU Validation (1-2 weeks, $150-500)

**Objective:** Validate full end-to-end flow with ONE cheapest GPU node before scaling.

**Environment:** 1x CPU node + 1x GPU node (cheapest available)

**What You'll Validate:**
- GPU detection and drivers
- GraVal validation
- Chute deployments
- Registry authentication
- Day-2 operations (practiced 5-10 times)
- Profitability model

**Exit Criteria:**
- GPU node deployed via Ansible
- Chutes deploying successfully
- All day-2 operations practiced
- Monitoring functional
- Backup/restore tested
- Runbooks validated

**Cost:** $150-500 (1-2 weeks @ $10-25/day)
**Time:** 1-2 weeks
**Risk:** Medium - first real GPU spend

**Keep running for full 1-2 weeks** to practice operations

---

### Phase 3: Production (Ongoing, $400-2000+/mo)

**Objective:** Scale to production with full confidence.

**Environment:** 1x CPU node + Nx GPU nodes (diverse types)

**What You'll Deploy:**
- Production control plane
- Multiple GPU nodes (start small, scale based on data)
- Production monitoring/alerting
- Automated backups

**Exit Criteria:**
- All production services stable
- Receiving and deploying chutes
- Profitability validated
- Cost tracking implemented

**Cost:** $400-2000+/mo (depends on scale)
**Time:** Ongoing
**Risk:** Managed - validated in previous phases

---

## 💰 Cost Breakdown

### Testing Investment

| Item | Cost | Purpose |
|------|------|---------|
| Phase 0 (Local) | $0 | Learn everything risk-free |
| Phase 1 (CPU) | $5-20 | Validate infrastructure |
| Phase 2 (1 GPU) | $150-500 | Validate operations |
| **Total Testing** | **$155-520** | Complete validation before production |

### Production Minimum

| Item | Monthly Cost | Notes |
|------|-------------|-------|
| CPU Node (4 cores, 32GB) | $50-100 | Control plane |
| GPU Node (T4) | $350-550 | Cheapest compatible option |
| **Production Minimum** | **$400-650/mo** | 1 GPU minimum viable miner |

### Production Scaling

| Configuration | Monthly Cost | Use Case |
|---------------|-------------|----------|
| 1x CPU + 1x T4 | $400-650 | Testing/learning |
| 1x CPU + 3x T4 | $1,150-1,750 | Small-scale mining |
| 1x CPU + 2x L40S + 1x A100 | $1,900-2,500 | Diverse portfolio |
| 1x CPU + 5x A100 | $3,500-5,000+ | High-performance mining |

## 🎯 Strategic Principles

### 1. Progressive Complexity

```
Local (k3d)        Staging (Cloud)      Production (Cloud)
    ↓                   ↓                      ↓
    └──────────── Same Ansible Playbooks ─────────┘
    └──────────── Same Helm Charts ──────────────┘
    └──────────── Same Scripts ───────────────────┘
    └──────────── Same Validation ────────────────┘
```

**Benefit:** No surprises when promoting to production

### 2. Ruthless Consistency

Every environment uses:
- Same Ansible playbooks (just different inventory)
- Same Helm charts (just different values)
- Same validation scripts (just different context)
- Same backup/restore procedures

**Benefit:** Confidence from repeated validation

### 3. Validation Gates

Cannot proceed to next phase without passing ALL exit criteria.

```
Phase 0 ──[Gate]──> Phase 1 ──[Gate]──> Phase 2 ──[Gate]──> Phase 3
  ↓                    ↓                    ↓                    ↓
All tests pass    Infra valid.       Ops practiced        Production
```

**Benefit:** Fail fast and cheap, not slow and expensive

### 4. Operational Practice

Practice every operation 5-10 times BEFORE production:
- Update Gepetto strategy
- Add/remove GPU nodes
- Handle failures
- Backup/restore
- Troubleshoot issues

**Benefit:** Muscle memory prevents production panic

### 5. Cost Optimization

- Minimize GPU time during learning phase
- Use hourly billing to test then destroy
- Only keep GPU nodes when validated and profitable
- Scale incrementally based on data

**Benefit:** ~$500 testing vs $5000+ blind production

## 📅 Timeline

### Recommended Pace (6-8 weeks)

```
Week 1-2:  Phase 0 (Local development)
           - Setup k3d
           - Deploy charts locally
           - Customize Gepetto
           - Write runbooks
           - Practice operations

Week 3:    Phase 1 (Cloud control plane)
           - Rent CPU node
           - Run Ansible
           - Validate infrastructure
           - Destroy node
           - Document lessons learned

Week 4-5:  Phase 2 Prep
           - Register on subnet 64
           - Setup production wallets
           - Configure monitoring/alerting
           - Review Gepetto strategy

Week 5-6:  Phase 2 (GPU validation)
           - Rent CPU + 1 GPU
           - Full end-to-end testing
           - Practice all day-2 operations
           - Validate profitability model

Week 7:    Phase 2 → 3 Transition
           - Final validation
           - Production planning
           - Cost modeling
           - Scale planning

Week 8:    Phase 3 (Production)
           - Deploy production control plane
           - Add GPU nodes incrementally
           - Monitor closely
           - Scale based on data
```

### Aggressive Pace (3-4 weeks)

Experienced operators with prior Kubernetes/Ansible experience.

### Conservative Pace (10-12 weeks)

First-time miners, learning Kubernetes and Bittensor concurrently.

## 🎯 Risk Mitigation

| Risk | Without Strategy | With This Strategy |
|------|-----------------|-------------------|
| **Ansible failures** | 🔴 High (untested) | 🟢 Low (Phase 1) |
| **GPU config issues** | 🔴 High (first time) | 🟢 Low (Phase 2) |
| **Day-2 operations** | 🔴 High (no practice) | 🟢 Low (practiced 10x) |
| **Wasted GPU spend** | 🔴 High ($1000s) | 🟢 Low (<$200) |
| **Production downtime** | 🔴 High (no rollback) | 🟢 Low (tested rollback) |
| **Unknown unknowns** | 🔴 High (YOLO deploy) | 🟢 Low (3 gates) |

## 🚀 Success Factors

### What Makes This Strategy Effective

1. **Fail Fast and Cheap**
   - Catch issues in Phase 0 ($0) not Phase 3 ($2000/mo)
   - Each phase is a safety gate

2. **Build Confidence Incrementally**
   - Phase 0: Learn tools
   - Phase 1: Validate infrastructure
   - Phase 2: Validate operations
   - Phase 3: Execute with confidence

3. **Practice Prevents Panic**
   - Practiced Gepetto updates 5+ times
   - Practiced node additions 3+ times
   - Practiced troubleshooting 10+ times
   - Muscle memory for day-2 operations

4. **Consistency Eliminates Surprises**
   - Same tools across all phases
   - Validated configurations
   - Tested procedures
   - Known behavior

5. **Cost-Effective Learning**
   - $500 testing investment
   - Prevents $5000+ production mistakes
   - ROI: 10x cost avoidance

## 🚨 Critical Warnings

⚠️ **DO NOT skip Phase 0** - Everything builds on local validation

⚠️ **DO NOT skip Phase 2** - This is where you learn operations

⚠️ **DO NOT use shared/dynamic IPs** - Chutes requires dedicated static IPs

⚠️ **DO NOT use container platforms** - Vast.ai, RunPod won't work

⚠️ **DO NOT register multiple UIDs** - Compete with yourself (wasteful)

⚠️ **DO NOT skimp on RAM** - Need >= VRAM per GPU (e.g., 4x A40 @ 48GB = 192GB RAM)

## 📚 Next Steps

1. Read **[Phase 0: Local Mastery](01-phase0-local.md)**
2. Setup your development environment
3. Follow each phase sequentially
4. Do NOT skip validation gates

---

**Ready to begin?** → Start with **[Phase 0](01-phase0-local.md)**
