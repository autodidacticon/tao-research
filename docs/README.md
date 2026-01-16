# Chutes Miner Deployment Documentation

This directory contains comprehensive documentation for deploying and operating a Chutes miner on Bittensor subnet 64.

## 📋 Documentation Structure

### Deployment Guides

Step-by-step guides for each deployment phase:

1. **[Overview](deployment/00-overview.md)** - Strategy, costs, and timeline
2. **[Phase 0: Local Mastery](deployment/01-phase0-local.md)** - Local k3d development ($0 cost)
3. **[Phase 1: Control Plane](deployment/02-phase1-control-plane.md)** - Cloud validation ($5-20 cost)
4. **[Phase 2: GPU Validation](deployment/03-phase2-gpu-validation.md)** - Single GPU testing ($150-500 cost)
5. **[Phase 3: Production](deployment/04-phase3-production.md)** - Full production deployment ($400-2000+/mo)

### Operational Runbooks

Day-2 operations procedures:

- **[Update Gepetto Strategy](runbooks/update-gepetto.md)** - Modify optimization logic
- **[Add GPU Node](runbooks/add-gpu-node.md)** - Scale infrastructure
- **[Troubleshooting](runbooks/troubleshooting.md)** - Common issues and fixes
- **[Backup and Restore](runbooks/backup-restore.md)** - Data protection procedures
- **[Monitoring](runbooks/monitoring.md)** - Metrics and alerting

### Scripts and Templates

Automation tools and configuration templates:

- **[Scripts](scripts/)** - Validation, deployment, and backup scripts
- **[Templates](templates/)** - Inventory and values file templates

## 🎯 Quick Start

### For New Deployments

1. Read **[Deployment Overview](deployment/00-overview.md)**
2. Follow **[Phase 0](deployment/01-phase0-local.md)** completely before spending money
3. Validate in **[Phase 1](deployment/02-phase1-control-plane.md)** before adding GPUs
4. Practice operations in **[Phase 2](deployment/03-phase2-gpu-validation.md)**
5. Deploy to **[Phase 3](deployment/04-phase3-production.md)** with confidence

### For Existing Deployments

- Need to update Gepetto? → **[Update Gepetto Runbook](runbooks/update-gepetto.md)**
- Adding capacity? → **[Add GPU Node Runbook](runbooks/add-gpu-node.md)**
- Something broken? → **[Troubleshooting Runbook](runbooks/troubleshooting.md)**

## 💰 Cost Expectations

| Phase | Duration | Cost | Purpose |
|-------|----------|------|---------|
| Phase 0 | 1-2 weeks | **$0** | Learn and practice risk-free |
| Phase 1 | 2-4 days | **$5-20** | Validate infrastructure automation |
| Phase 2 | 1-2 weeks | **$150-500** | Validate GPU operations |
| Phase 3 | Ongoing | **$400-2000+/mo** | Production mining |

**Total testing investment:** ~$155-520 before committing to production

## 🎓 Key Principles

### Progressive Complexity
Start simple, add complexity only when validated at each stage.

### Ruthless Consistency
Same tools, same scripts, same validation across all environments.

### Practice Before Production
Practice every operation 5+ times in lower environments.

### Fail Fast and Cheap
Catch issues in Phase 0 ($0 cost) not Phase 3 ($2000/mo cost).

## 📊 Success Metrics

### Phase 0 Exit Criteria
- All local validations passing
- Gepetto strategy customized
- All runbooks written
- Team practiced 3+ deployments

### Phase 1 Exit Criteria
- Ansible successfully provisions control plane
- All infrastructure validations pass
- Networking confirmed functional

### Phase 2 Exit Criteria
- GPU node deployed via Ansible
- Chutes deploying successfully
- All day-2 operations practiced 5+ times
- Profitability model validated

### Phase 3 Exit Criteria
- Production control plane stable
- GPU nodes receiving chutes
- Monitoring/alerting functional
- Costs tracking to budget

## 🚨 Important Warnings

⚠️ **Do NOT skip phases** - Each phase builds on the previous

⚠️ **Do NOT rush Phase 2** - This is where you learn operations

⚠️ **Do NOT deploy to production** until all exit criteria met

⚠️ **Do NOT use shared/NAT IPs** - Chutes requires dedicated static IPs

⚠️ **Do NOT use container platforms** - Vast.ai, RunPod won't work

## 🔗 External Resources

- [Chutes Miner GitHub](https://github.com/rayonlabs/chutes-miner)
- [Bittensor Subnet 64](https://taostats.io/subnets/64/)
- [Bittensor Discord](https://discord.gg/bittensor)
- [k3s Documentation](https://docs.k3s.io/)
- [Ansible Documentation](https://docs.ansible.com/)

## 📝 Contributing

Found an issue? Learned something new? Update the docs:

1. Make changes to relevant files
2. Test procedures in your environment
3. Submit improvements

Keep documentation:
- **Accurate** - Test before documenting
- **Concise** - Remove unnecessary details
- **Practical** - Focus on what works
- **Updated** - Keep in sync with code changes

## 📞 Support

- **Technical Issues**: [Chutes GitHub Issues](https://github.com/rayonlabs/chutes-miner/issues)
- **Bittensor Questions**: [Bittensor Discord](https://discord.gg/bittensor)
- **Documentation Issues**: Update this repo

---

**Last Updated:** 2026-01-15
**Documentation Version:** 1.0
**Tested Against:** chutes-miner k3s-latest
