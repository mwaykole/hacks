# LLMD & KServe Complete Learning Path

This document provides navigation guidance for the comprehensive LLMD textbook covering deployment of Large Language Models on Kubernetes using LLMD (KServe) and the llm-d architecture.

---

## Overview

A complete textbook split into 4 parts with 185+ pages covering:
- **Fundamentals:** LLM inference theory and concepts
- **Components:** Detailed explanation of all stack components
- **Hands-on Labs:** 3 progressive labs from simple to production
- **Operations:** Monitoring, troubleshooting, capacity planning
- **Reference:** CRD specifications, commands, glossary

**Estimated time investment:** 8-12 hours for complete coverage

---

## Learning Paths

### Path A: Beginners - New to LLM Serving
**Start here:** Part 1, Chapter 1  
**Next:** Read sequentially through Part 1 (Chapters 1-8)  
**Then:** Do Lab 1 (Chapter 18 in Part 4)  
**Finally:** Continue with Parts 2-4 as needed

**Files to read in order:**
1. `LLMD_COMPLETE_TEXTBOOK.md` (Part 1)
2. `LLMD_COMPLETE_TEXTBOOK_PART4_FINAL.md` (Just Lab 1)
3. Come back for Parts 2-3 when you need deeper understanding

---

### Path B: Experienced Users - Kubernetes Background
**Start here:** Part 1, Chapters 7-8  
**Next:** Part 2 (All components)  
**Then:** Lab 2 & Lab 3 (Part 4)  
**Reference:** Part 4 Appendices as needed

**Files to read:**
1. `LLMD_COMPLETE_TEXTBOOK.md` (Chapters 7-8)
2. `LLMD_COMPLETE_TEXTBOOK_PART2.md` (All)
3. `LLMD_COMPLETE_TEXTBOOK_PART4_FINAL.md` (Labs 2-3)

---

### Path C: Production Deployment - Immediate Needs
**Start here:** Lab 3 (Chapter 20 in Part 4)  
**Reference:** Troubleshooting (Chapter 23) & Commands (Appendix B)  
**Deep dive:** Come back to Parts 1-3 to understand how it works

**Files you need:**
1. `LLMD_COMPLETE_TEXTBOOK_PART4_FINAL.md`
   - Lab 3: Production Deployment
   - Chapter 22: Monitoring
   - Chapter 23: Troubleshooting
   - Chapter 24: Capacity Planning
   - Appendix B: Commands

**Note:** This path provides immediate deployment guidance. Review fundamentals sections for comprehensive understanding.

---

### Path D: Troubleshooting - Issue Resolution
**Start here:** Chapter 23 (Troubleshooting Guide in Part 4)  
**Keep open:** Appendix B (Command Reference)  
**Deep dive:** Relevant component chapter based on issue

**Files you need:**
1. `LLMD_COMPLETE_TEXTBOOK_PART4_FINAL.md` (Chapter 23)
2. Relevant chapters from Part 2 for component details

---

## File Guide

### Main Textbook Files

| File | What's Inside | Size | When to Read |
|------|---------------|------|--------------|
| **README_TEXTBOOK.md** | Master index & guide | 5 min | First! (You are here) |
| **START_HERE.md** | Quick pathways | 5 min | Right now! |
| **LLMD_COMPLETE_TEXTBOOK.md** | Part 1: Foundations (Ch 1-8) | ~2 hrs | Beginning or reference |
| **LLMD_COMPLETE_TEXTBOOK_PART2.md** | Part 2: Components (Ch 9-13) | ~1.5 hrs | Deep dive |
| **LLMD_COMPLETE_TEXTBOOK_PART3.md** | Part 3: Advanced (Ch 14-15) | ~1 hr | Multi-GPU setups |
| **LLMD_COMPLETE_TEXTBOOK_PART4_FINAL.md** | Part 4: Labs & Ops (Ch 18-28 + Appendices) | ~3 hrs | Hands-on practice |

### Old Documentation (In llmd-DOC/)
These exist from previous work. The new textbook consolidates and expands on these:
- Various architecture docs
- Feature guides
- Test reports

**Note:** Use the new textbook files above. The old documentation is retained for reference purposes.

---

## Learning Objectives

After completing this textbook, you will be able to:

**Beginner Level (After Part 1 + Lab 1):**
- [ ] Explain how LLM inference works (prefill vs decode)
- [ ] Deploy a simple LLMD service
- [ ] Test inference with curl
- [ ] Check pod status and logs

**Intermediate Level (After Parts 2-3 + Lab 2):**
- [ ] Deploy disaggregated prefill/decode services
- [ ] Understand how Scheduler routes requests
- [ ] Configure GPU parallelism (TP, PP, DP)
- [ ] Monitor metrics with Prometheus

**Advanced Level (After Part 4 + Lab 3):**
- [ ] Deploy production-ready LLM services
- [ ] Implement monitoring and alerting
- [ ] Troubleshoot common issues
- [ ] Plan capacity and optimize costs
- [ ] Configure high availability

---

## Key Concepts Summary

### The Big Insight (Chapter 2 & 8)

```
LLM Inference = Two Different Jobs

PREFILL (Reading the book)
├─ Fast (100ms)
├─ Parallel
├─ Compute-heavy
└─ Needs many GPUs

DECODE (Answering questions)
├─ Slow (10s)
├─ Sequential
├─ Memory-heavy
└─ Needs many replicas

Solution: Split them!
├─ Prefill pods: Few pods, many GPUs each
└─ Decode pods: Many pods, fewer GPUs each
Result: 3-5x better throughput!
```

### The Stack (Chapters 9-13)

```
Your Request
    ↓
[Gateway] ← Entry point
    ↓
[Scheduler] ← Picks best pod
    ↓
[Routing Sidecar] ← Decides prefill vs decode
    ↓
[vLLM] ← Does the work
```

---

## Prerequisites

**To understand the textbook:**
- Basic Kubernetes knowledge (pods, services, deployments)
- Familiarity with YAML
- Basic command line skills

**To run the labs:**
- Kubernetes cluster (1.28+)
- GPU nodes (NVIDIA/AMD/Intel)
- kubectl configured
- KServe installed
- 50+ GB storage

**Don't have a cluster?**
- Use GKE, EKS, or AKS with GPU nodes
- Try Minikube with GPU passthrough (limited)
- Use OpenShift with GPU operators

---

## Recommended Reading Order

### For Complete Beginners (Full Path)
**Total time:** 8-12 hours

1. **Day 1 (2-3 hours):**
   - Read Part 1: Chapters 1-4 (Fundamentals)
   - Understand the problem space

2. **Day 2 (2-3 hours):**
   - Read Part 1: Chapters 5-8 (KServe & LLMD)
   - Do Lab 1 (Simple deployment)

3. **Day 3 (2-3 hours):**
   - Read Part 2: Chapters 9-11 (Gateway, Scheduler, Sidecar)
   - Do Lab 2 (Disaggregated deployment)

4. **Day 4 (2-3 hours):**
   - Read Part 2: Chapters 12-13 (vLLM, InferencePool)
   - Read Part 3: Chapters 14-15 (Parallelism, Multi-node)

5. **Day 5 (3-4 hours):**
   - Do Lab 3 (Production deployment)
   - Read Part 4: Chapters 22-24 (Ops)

---

### For Experienced Engineers (Fast Path)
**Total time:** 4-6 hours

1. **Session 1 (1.5 hours):**
   - Skim Part 1: Focus on Chapters 7-8
   - Understand LLMD CRD and P/D architecture

2. **Session 2 (1.5 hours):**
   - Read Part 2: All components
   - Quick Lab 1 validation

3. **Session 3 (2 hours):**
   - Do Lab 2 (Disaggregated)
   - Do Lab 3 (Production)

4. **As Needed:**
   - Part 3 for multi-GPU
   - Part 4 for troubleshooting

---

## Quick Reference

### Want to deploy something in 30 minutes?
→ Go to **Lab 1** (Chapter 18 in Part 4)

### Need production best practices?
→ Go to **Lab 3** (Chapter 20 in Part 4)

### Something broken?
→ Go to **Troubleshooting** (Chapter 23 in Part 4)

### Need a kubectl command?
→ Go to **Appendix B** in Part 4

### What does this term mean?
→ Go to **Glossary** (Appendix C in Part 4)

---

## Frequently Asked Questions

**Q: What's the difference between LLMD and llm-d?**  
A: LLMD (LLMInferenceService) is a KServe CRD. llm-d is the broader project/framework. See Chapter 1 for full clarification.

**Q: Should I use LLMD or ServingRuntime?**  
A: LLMD is alpha (experimental), ServingRuntime is stable. Use ServingRuntime for production today, evaluate LLMD for its advanced features. See Chapters 5 & 7.

**Q: Do I need the Scheduler?**  
A: Not required, but strongly recommended for production. It gives you 2-3x better tail latency. See Chapter 10.

**Q: How many GPUs do I need?**  
A: Depends on model size. See Chapter 24 (Capacity Planning) for sizing guide.

**Q: Can I use this without GPUs?**  
A: Technically yes (CPU inference), but it's very slow. This textbook assumes GPU deployment.

---

## Getting Started

### Choose your learning path above, then:

**Beginners:** Open `LLMD_COMPLETE_TEXTBOOK.md` and start with Chapter 1

**Experienced Users:** Jump to the relevant chapter or lab

**Production Deployment:** Proceed directly to Lab 3

---

## Support

**Conceptual Questions:**
- Re-read the relevant chapter
- Consult the Glossary (Appendix C)
- Review the architecture diagrams

**Lab Issues:**
- Check Troubleshooting (Chapter 23)
- Verify prerequisites (kubectl, GPUs, KServe)
- Check pod logs: `kubectl logs <pod> -c main`

**Contributions:**
- Documentation location: `/home/cloud-user/temp/hacks/llmd/`
- Community: llm-d Slack at https://llm-d.ai/slack

---

## Expected Outcomes

Upon completion, you will be able to:
- Deploy production LLM services confidently
- Troubleshoot issues independently
- Optimize for cost and performance
- Contribute to llm-d and KServe projects

---

## Next Steps

1. Select your learning path from the options above
2. Open the first file listed for your path
3. Begin reading or working through labs
4. Bookmark this file for quick reference

---

*The LLMD & KServe Complete Textbook*  
*Definitive guide to LLM serving on Kubernetes*  
*Version 1.0 - October 14, 2025*


