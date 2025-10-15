# LLMD & KServe Complete Textbook
## Comprehensive Guide for Large Language Model Serving on Kubernetes

**Version:** 1.0  
**Last Updated:** October 14, 2025  
**Total Pages:** 4 comprehensive parts  
**Target Audience:** Beginners to production engineers

---

## Description

This comprehensive textbook provides complete coverage from fundamentals to production deployment and operations of LLM services using LLMD (KServe's LLMInferenceService) and the llm-d architecture.

Key features:
- Comprehensive concept explanation from fundamentals
- Practical analogies and real-world examples
- Detailed architecture diagrams
- Hands-on labs with executable commands
- Production best practices and troubleshooting
- Detailed rationale for architectural decisions

---

## Textbook Structure

### Part 1: Foundations & Core Concepts
**File:** `LLMD_COMPLETE_TEXTBOOK.md`  
**Chapters:** 1-8  
**Pages:** ~50

**What's inside:**
- Chapter 1: Introduction (What you'll learn, two LLMDs clarified)
- Chapter 2: LLM Inference Fundamentals (Prefill vs Decode explained like you're 5)
- Chapter 3: Why Kubernetes for LLMs
- Chapter 4: The Problem Space (GPU underutilization, unpredictable latency, etc.)
- Chapter 5: Understanding KServe (v1beta1 vs v1alpha1 APIs)
- Chapter 6: The llm-d Project (Philosophy, architecture, well-lit paths)
- Chapter 7: LLMD (LLMInferenceService) Deep Dive (Lifecycle, CRD structure, modes)
- Chapter 8: Prefill vs Decode Architecture (Complete diagrams and flow)

**Recommended for:** Readers new to LLM serving or seeking fundamental understanding

---

### Part 2: The Components Deep Dive
**File:** `LLMD_COMPLETE_TEXTBOOK_PART2.md`  
**Chapters:** 9-13  
**Pages:** ~40

**What's inside:**
- Chapter 9: Envoy and Gateway API (Why Envoy, Gateway resources, ExtProc protocol)
- Chapter 10: The Scheduler (EPP) (Architecture, scoring algorithm, metrics)
- Chapter 11: Routing Sidecar (Decision tree, request flow, session management)
- Chapter 12: vLLM Model Server (PagedAttention, configuration, API, metrics)
- Chapter 13: InferencePool and InferenceModel (CRDs, integration, why not Service?)

**Recommended for:** Understanding internal component implementation

---

### Part 3: Advanced Topics
**File:** `LLMD_COMPLETE_TEXTBOOK_PART3.md`  
**Chapters:** 14-17  
**Pages:** ~35

**What's inside:**
- Chapter 14: GPU Parallelism Strategies (TP, PP, DP, EP explained with diagrams)
- Chapter 15: Multi-Node Deployments (LeaderWorkerSet, architecture, configuration)
- Chapter 16: KV Cache Management *(Covered in vLLM chapter)*
- Chapter 17: Performance Tuning *(Covered in Part 4)*

**Recommended for:** Large model deployments or multi-GPU configurations

---

### Part 4: Hands-On Labs & Operations (FINAL)
**File:** `LLMD_COMPLETE_TEXTBOOK_PART4_FINAL.md`  
**Chapters:** 18-28 + Appendices  
**Pages:** ~60

**What's inside:**

**Part V: Hands-On Labs**
- Lab 1: Your First LLMD Service (Simple deployment, 30 min)
- Lab 2: Disaggregated Prefill/Decode (Production-style, 45 min)
- Lab 3: Production Deployment (Full stack with monitoring, 60 min)
- Lab 4: Multi-Node Setup *(Covered in Chapter 15)*

**Part VI: Operations**
- Chapter 22: Monitoring and Observability (Metrics, dashboards, logging, tracing)
- Chapter 23: Troubleshooting Guide (Common issues, debugging checklist)
- Chapter 24: Capacity Planning (Sizing, throughput estimation, cost optimization)
- Chapter 25: Security Best Practices *(Covered in Lab 3)*

**Part VII: Integration**
- Chapter 26: ODH and RHOAI Integration *(Throughout textbook)*
- Chapter 27: ServingRuntime vs LLMD *(Covered in Chapter 5 & 7)*
- Chapter 28: Migration Strategies *(Implicit in labs)*

**Appendices:**
- Appendix A: CRD Reference (Complete API specs)
- Appendix B: Command Reference (kubectl cheatsheet)
- Appendix C: Glossary (All terms defined)
- Appendix D: Resources (Links, community, papers)

**Recommended for:** Hands-on practice, production deployment, and troubleshooting

---

## Quick Start Guide

### For Complete Beginners
1. Read Part 1 (Chapters 1-4) to understand the "why"
2. Read Chapter 8 (Prefill/Decode) carefully - this is the key insight
3. Do Lab 1 (Chapter 18) - get your hands dirty
4. Come back and read Part 2 & 3 for deeper understanding

### For Experienced Kubernetes Users
1. Skim Part 1 (you probably know this)
2. Focus on Chapters 7-8 (LLMD specifics)
3. Read Part 2 (Components) thoroughly
4. Do Labs 2 & 3 (production deployments)

### For Production Deployment
1. Read Chapter 7 (LLMD Deep Dive)
2. Read Chapter 8 (Prefill/Decode)
3. **Do Lab 3** (Production Deployment) - this is gold
4. Read Chapter 22-24 (Monitoring, Troubleshooting, Capacity Planning)
5. Keep Appendix B (Commands) bookmarked

### For Troubleshooting
1. Go straight to Chapter 23 (Troubleshooting Guide)
2. Use Appendix B (Command Reference)
3. Check relevant component chapter for deep dive

---

## Learning Objectives

By the end of this textbook, you will:

**Fundamentals:**
- Understand how LLM inference works (prefill vs decode phases)
- Know why disaggregated serving improves GPU utilization
- Understand KV cache and PagedAttention
- Know when to use simple vs disaggregated vs multi-node

**Components:**
- Master Envoy/Gateway API and ExtProc protocol
- Understand how the Scheduler (EPP) makes routing decisions
- Know how the routing sidecar orchestrates prefill/decode
- Understand vLLM configuration and tuning
- Use InferencePool and InferenceModel CRDs

**Operations:**
- Deploy LLMs from simple to production-grade
- Monitor with Prometheus and Grafana
- Troubleshoot common issues
- Plan capacity and optimize costs
- Secure your deployments with RBAC and TLS

**Advanced:**
- Configure tensor, pipeline, data, and expert parallelism
- Deploy multi-node LLMs with LeaderWorkerSet
- Scale horizontally with HPA
- Implement high availability and disaster recovery

---

## Key Concepts Overview

### The Big Idea (Chapter 2 & 8)

**LLM inference has two phases with different resource needs:**

```
PREFILL (prompt processing)
├─ Parallel across tokens
├─ Compute-intensive (95% GPU utilization)
├─ Short duration (100-500ms)
└─ Loves many GPUs

DECODE (token generation)
├─ Sequential (one token at a time)
├─ Memory-intensive (30% GPU utilization)
├─ Long duration (10+ seconds)
└─ Loves many replicas
```

**Disaggregation = Run prefill and decode on separate pods**

**Result:**
- 3-5x higher throughput
- Better GPU utilization (more value per dollar)
- Lower tail latency (scheduler picks best pod)

### The Architecture (Chapter 7-11)

```
Client
  ↓
Gateway (Envoy) ← Your doorman
  ↓
Scheduler (EPP) ← The smart friend who picks the best pod
  ↓
Decode Pod (Routing Sidecar) ← The concierge
  ├─ New? → Prefill Pod ← The scanning desk
  └─ Follow-up? → Local Decode ← The answer desk
```

### The Stack (Part II)

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Entry** | Gateway (Envoy) | TLS, routing, observability |
| **Routing** | Scheduler (EPP) | Intelligent pod selection |
| **Discovery** | InferencePool | Service discovery |
| **Orchestration** | Routing Sidecar | Prefill/decode decisions |
| **Inference** | vLLM | Model serving engine |
| **Multi-Node** | LeaderWorkerSet | Coordinate pod groups |

---

## Target Audience

### Ideal Readers:
- ML Engineers new to production serving
- DevOps Engineers deploying LLMs
- Platform Engineers building ML infrastructure
- Students learning about LLM serving
- Anyone tasked with "deploy an LLM on Kubernetes"

### Prerequisites:
- Basic Kubernetes knowledge (pods, services, deployments)
- Basic understanding of containers and Docker
- Some exposure to machine learning concepts
- No prior LLM serving experience required!

### Not Applicable For:
- LLM training (this is about inference/serving)
- Non-Kubernetes deployments
- Traditional ML models (scikit-learn, XGBoost, etc.)

---

## Lab Requirements

To run the hands-on labs, you need:

**Minimum (Lab 1):**
- Kubernetes cluster (1.28+)
- 1 GPU node (NVIDIA, AMD, or Intel)
- kubectl configured
- KServe installed

**Recommended (Labs 2-3):**
- Kubernetes cluster (1.29+)
- 4+ GPU nodes
- Gateway API installed
- Prometheus & Grafana (for monitoring)
- 50+ GB storage for models

**Cloud Options:**
- GKE with GPU node pools
- EKS with GPU instances
- AKS with GPU VMs
- OpenShift on AWS/Azure/GCP

---

## Reading Guidance

### Linear Reading (Recommended for beginners)
Start with Part 1, Chapter 1, and read straight through. Everything builds on previous chapters.

### Topic-Based Reading
Use the table of contents to jump to specific topics. Each chapter is relatively self-contained.

### Lab-First Reading (For hands-on learners)
1. Read Chapters 1-2 (fundamentals)
2. Jump to Lab 1 (Chapter 18)
3. When stuck, go back and read relevant component chapters
4. Continue with Labs 2-3

### Reference Reading (For experienced users)
Bookmark and use as needed:
- Appendix A (CRD specs)
- Appendix B (Commands)
- Chapter 23 (Troubleshooting)
- Chapter 24 (Capacity planning)

---

## Special Features

### ASCII Art Diagrams
Every architecture is visualized with detailed ASCII diagrams showing:
- Request flows
- Component interactions
- Pod structures
- Decision trees

### Real Examples
Every concept includes real-world examples with:
- Complete YAML manifests
- Actual kubectl commands
- Expected outputs
- Common pitfalls

### Human Analogies
Complex concepts explained with everyday analogies:
- Envoy = Doorman
- Scheduler = Smart friend
- Routing Sidecar = Concierge
- Prefill = Scanning desk
- Decode = Answer desk

### Production Ready
All examples follow best practices:
- Security (RBAC, TLS, least privilege)
- Observability (metrics, logs, traces)
- Reliability (health checks, QoS)
- Scalability (HPA, anti-affinity)

---

## Contributing

Found an error? Have a suggestion? Want to add a chapter?

This textbook lives in: `/home/cloud-user/temp/hacks/llmd/`

Files:
- `LLMD_COMPLETE_TEXTBOOK.md` (Part 1)
- `LLMD_COMPLETE_TEXTBOOK_PART2.md` (Part 2)
- `LLMD_COMPLETE_TEXTBOOK_PART3.md` (Part 3)
- `LLMD_COMPLETE_TEXTBOOK_PART4_FINAL.md` (Part 4)
- `README_TEXTBOOK.md` (This file)

---

## Additional Resources

### Official Docs
- **llm-d:** https://llm-d.ai
- **KServe:** https://kserve.github.io/kserve/
- **vLLM:** https://docs.vllm.ai
- **Gateway API:** https://gateway-api.sigs.k8s.io/

### Community
- **llm-d Slack:** https://llm-d.ai/slack
- **llm-d Calendar:** https://red.ht/llm-d-public-calendar
- **KServe Slack:** https://kserve.slack.com

### GitHub
- **llm-d:** https://github.com/llm-d/llm-d
- **KServe (ODH fork):** https://github.com/opendatahub-io/kserve
- **ODH Model Controller:** https://github.com/opendatahub-io/odh-model-controller

---

## Version History

**v1.0 (October 14, 2025)**
- Initial release
- 4 parts, 28 chapters, 4 appendices
- 3 complete hands-on labs
- ~185 pages total
- Comprehensive coverage from fundamentals to production

---

## Completion Status

Upon completing the following milestones:
- Read all 4 parts
- Completed Labs 1, 2, and 3
- Deployed a production LLM service
- Monitored and troubleshot issues

You will have gained:
- Deep understanding of LLM serving architecture
- Hands-on experience with LLMD and KServe
- Production-ready deployment skills
- Troubleshooting and operations expertise

---

## Feedback

Contributions and feedback are welcome:
- Documentation clarity improvements
- Example effectiveness
- Content gaps
- Expansion suggestions

Your input helps improve this resource for all users.

---

## Getting Started

Begin with **Part 1: LLMD_COMPLETE_TEXTBOOK.md**

Alternatively, proceed directly to **Lab 1: Chapter 18** for hands-on learning.

---

*The Definitive LLMD & KServe Textbook*  
*Version 1.0 - October 14, 2025*


