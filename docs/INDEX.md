# Documentation Index

Complete documentation for cost-effective, validated chutes-miner deployment.

## 📚 Documentation Created

### Main Documentation

- **[README.md](README.md)** - Documentation overview and navigation

### Deployment Guides (Phase-by-Phase)

1. **[00-overview.md](deployment/00-overview.md)** - Strategy overview, costs, timeline
2. **[01-phase0-local.md](deployment/01-phase0-local.md)** - Local k3d development ($0)
3. **[02-phase1-control-plane.md](deployment/02-phase1-control-plane.md)** - Cloud validation ($5-20)
4. **[03-phase2-gpu-validation.md](deployment/03-phase2-gpu-validation.md)** - GPU testing ($150-500)
5. **[04-phase3-production.md](deployment/04-phase3-production.md)** - Production deployment ($400-2000+/mo)

### Operational Runbooks

- **[update-gepetto.md](runbooks/update-gepetto.md)** - Modify optimization strategy
- **[troubleshooting.md](runbooks/troubleshooting.md)** - Common issues and fixes
- (Create additional runbooks as documented in guides)

### Scripts

- **[validate-deployment.sh](scripts/validate-deployment.sh)** - Universal validation script
- **[README.md](scripts/README.md)** - Script documentation and templates

## 🎯 Quick Navigation

### By Role

**First-Time Miner:**
1. Start: [Deployment Overview](deployment/00-overview.md)
2. Follow: Phase 0 → Phase 1 → Phase 2 → Phase 3 sequentially
3. Reference: [Troubleshooting](runbooks/troubleshooting.md) when needed

**Existing Operator:**
- Update strategy: [Update Gepetto](runbooks/update-gepetto.md)
- Issues: [Troubleshooting](runbooks/troubleshooting.md)
- Scaling: [Phase 3](deployment/04-phase3-production.md)

**DevOps/Infrastructure:**
- Automation: [Scripts README](scripts/README.md)
- Validation: [validate-deployment.sh](scripts/validate-deployment.sh)
- Architecture: [Phase 0](deployment/01-phase0-local.md)

### By Task

**Want to deploy:**
→ [Deployment Overview](deployment/00-overview.md) → Phase 0

**Need to troubleshoot:**
→ [Troubleshooting Runbook](runbooks/troubleshooting.md)

**Optimizing performance:**
→ [Update Gepetto Runbook](runbooks/update-gepetto.md)

**Understanding costs:**
→ [Deployment Overview](deployment/00-overview.md)

**Scaling infrastructure:**
→ [Phase 3: Production](deployment/04-phase3-production.md)

## 💡 Key Concepts

### Four-Phase Strategy

```
Phase 0 (Local)    → $0          → Learn risk-free
Phase 1 (CPU)      → $5-20       → Validate infrastructure
Phase 2 (1 GPU)    → $150-500    → Validate operations
Phase 3 (Prod)     → $400-2000+  → Scale with confidence
```

### Validation Gates

Each phase has strict exit criteria. Cannot proceed without passing all checks.

### Consistency Principle

Same tools, same scripts, same procedures across all environments.

## 📊 Success Metrics

### Phase Completion

- [ ] Phase 0: Local mastery achieved
- [ ] Phase 1: Infrastructure validated
- [ ] Phase 2: Operations practiced
- [ ] Phase 3: Production deployed

### Operational Readiness

- [ ] All runbooks created
- [ ] All operations practiced 5+ times
- [ ] All validation scripts passing
- [ ] Team trained
- [ ] Backup/restore tested

## 🚀 Getting Started

1. Read **[Deployment Overview](deployment/00-overview.md)**
2. Set up local environment per **[Phase 0](deployment/01-phase0-local.md)**
3. Run validation: `./scripts/validate-deployment.sh local`
4. Practice operations until comfortable
5. Proceed to Phase 1 only when Phase 0 exit criteria met

## 📞 Support

- **Technical Issues:** [Chutes GitHub](https://github.com/rayonlabs/chutes-miner/issues)
- **Bittensor Questions:** [Bittensor Discord](https://discord.gg/bittensor)
- **Subnet 64:** #subnet-64 channel

---

## 📝 Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| README.md | ✅ Complete | 2026-01-15 |
| 00-overview.md | ✅ Complete | 2026-01-15 |
| 01-phase0-local.md | ✅ Complete | 2026-01-15 |
| 02-phase1-control-plane.md | ✅ Complete | 2026-01-15 |
| 03-phase2-gpu-validation.md | ✅ Complete | 2026-01-15 |
| 04-phase3-production.md | ✅ Complete | 2026-01-15 |
| update-gepetto.md | ✅ Complete | 2026-01-15 |
| troubleshooting.md | ✅ Complete | 2026-01-15 |
| validate-deployment.sh | ✅ Complete | 2026-01-15 |
| scripts/README.md | ✅ Complete | 2026-01-15 |

## 🔄 Maintenance

This documentation should be updated when:
- Chutes-miner versions change
- New issues discovered
- Better practices identified
- Community feedback received

Keep documentation:
- **Accurate** - Test before documenting
- **Concise** - Remove unnecessary details
- **Practical** - Focus on what works
- **Updated** - Keep in sync with code

---

**Total Investment to Production:**
- Time: 6-8 weeks (recommended pace)
- Cost: ~$155-520 testing before production
- Outcome: Validated, confident, operational miner
