# Quick Decision Guide: Which LLM Serving Approach?

**Date:** October 13, 2025  
**Purpose:** Help you choose the right approach for your LLM serving needs

---

## 🎯 Quick Decision Tree

```
Do you need to serve LLMs in production?
│
├─ Yes → Are you using RHOAI/OpenShift?
│                                     │
│  ├─ Yes → Use ServingRuntime + InferenceService (v1beta1)
│                                                         │
│                                                         │
│                                                         │
│  └─ No → Do you want controller-managed or Helm-based?
│                                                      │
│     ├─ Controller-managed → ⚠️ Wait for KServe LLMD to reach GA
│                                                               │
│                                                               │
│     └─ Helm-based → ✅ Use llm-d Project
│              📖 https://www.llm-d.ai
│              📖 https://github.com/llm-d/llm-d
│
└─ No (Testing/Learning) → Any approach works
                            Start with llm-d quickstart
```

---

## 📊 Comparison Matrix

| Feature | llm-d Project | KServe LLMD CRD | ServingRuntime + InferenceService |
|---------|---------------|-----------------|-----------------------------------|
| **Production Ready** | ✅ Yes | ❌ No (Alpha) | ✅ Yes (GA) |
| **Status** | v0.3.0 GA | v1alpha1 | v1beta1 |
| **Deployment** | Helm + helmfile | kubectl CRD | kubectl CRD |
| **Management** | Manual (Helm) | Auto (controller) | Auto (controller) |
| **Inference Scheduling** | ✅ Included (IGW) | ⚠️ Gateway API only | ⚠️ Basic |
| **Prefill/Decode Split** | ✅ Full support | ✅ Yes | ❌ No |
| **Multi-GPU** | ✅ Tested | ✅ Yes | ✅ Yes |
| **Multi-Accelerator** | ✅ NVIDIA, AMD, TPU, XPU | ⚠️ Depends | ✅ Yes |
| **Benchmarks** | ✅ Published | ❌ No | ⚠️ Limited |
| **Well-lit Paths** | ✅ 3 guides | ❌ No | ⚠️ Basic |
| **Community Support** | ✅ Active (Slack, etc.) | ⚠️ Limited | ✅ RHOAI support |
| **Learning Curve** | Medium | Medium | Low (RHOAI) |
| **Flexibility** | ✅ High | Medium | Low |
| **KServe Integration** | ❌ No | ✅ Native | ✅ Native |
| **RHOAI Integration** | ❌ No | ⚠️ Limited | ✅ Full |

---

## 🚀 Recommendation by Use Case

### Use Case 1: Production LLM Serving (General)

**Best Choice:** llm-d Project

**Why:**
- Production-tested and benchmarked
- Intelligent inference scheduling included
- Well-documented deployment guides
- Active community support
- Multi-accelerator support

**Getting Started:**
```bash
# Clone the llm-d repo
git clone https://github.com/llm-d/llm-d.git
cd llm-d/guides
# Follow the quickstart
cat QUICKSTART.md
```

**Resources:**
- Website: https://www.llm-d.ai
- Quickstart: `/guides/QUICKSTART.md`
- Inference Scheduling: `/guides/inference-scheduling/`
- Slack: https://llm-d.ai/slack

---

### Use Case 2: Production LLM Serving in RHOAI/OpenShift

**Best Choice:** ServingRuntime + InferenceService

**Why:**
- Officially supported by Red Hat
- Integrated with RHOAI platform
- Stable (v1beta1) API
- UI integration
- Support contracts available

**Example:**
```yaml
apiVersion: serving.kserve.io/v1beta1
kind: ServingRuntime
metadata:
  name: vllm-runtime
spec:
  supportedModelFormats:
  - name: pytorch
    version: "1"
  containers:
  - name: kserve-container
    image: quay.io/opendatahub/vllm:stable
---
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: llama-3-8b
spec:
  predictor:
    model:
      modelFormat:
        name: pytorch
      runtime: vllm-runtime
      storageUri: pvc://my-models-pvc/llama-3-8b
```

**Resources:**
- RHOAI Docs: https://access.redhat.com/documentation/en-us/red_hat_openshift_ai
- This repo: `llmd-DOC/LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md`

---

### Use Case 3: Experimentation / Learning

**Best Choice:** llm-d Project (simplest) or KServe LLMD (to learn CRDs)

**Why:**
- llm-d has excellent quickstart guides
- KServe LLMD is good for learning Kubernetes CRD patterns
- Both are well-documented

**Getting Started with llm-d:**
```bash
cd /home/cloud-user/temp/llm-d-repo/guides
# Follow step-by-step quickstart
less QUICKSTART.md
```

**Getting Started with KServe LLMD:**
```bash
cd /home/cloud-user/temp/kserve/llmd-test-yamls
# Review test YAMLs
ls *.yaml
```

---

### Use Case 4: Very Large Models (70B+) with Disaggregation

**Best Choice:** llm-d Project

**Why:**
- Purpose-built for prefill/decode disaggregation
- Uses NIXL for fast KV cache transfer
- Supports RDMA/InfiniBand/RoCE
- Tested on H200 clusters
- xPyD (heterogeneous P/D ratios) support

**Well-lit Paths:**
1. **Prefill/Decode Disaggregation** - `/guides/pd-disaggregation/`
   - 4 prefill workers + 1 decode worker
   - Llama-3.3-70B-Instruct-FP8
   - 8xH200 with InfiniBand

2. **Wide Expert-Parallelism** - `/guides/wide-ep-lws/`
   - For MoE models like DeepSeek-R1
   - 1 DP=8 Prefill + 2 DP=8 Decode
   - 24xH200 with InfiniBand

**Resources:**
- P/D Guide: `llm-d-repo/guides/pd-disaggregation/README.md`
- Wide EP Guide: `llm-d-repo/guides/wide-ep-lws/README.md`
- Architecture: This repo's `llmd-DOC/LLMD_PREFILL_DECODE_ARCHITECTURE.md`

---

### Use Case 5: Small Models (< 13B)

**Best Choice:** ServingRuntime + InferenceService (simplest)

**Why:**
- Don't need advanced features
- Simple deployment
- Easy to scale horizontally
- Low operational overhead

**When to consider alternatives:**
- If you need intelligent routing → llm-d
- If you're already using llm-d infrastructure → llm-d

---

## 🔍 Feature-by-Feature Decision

### I need: Intelligent Inference Scheduling

**✅ llm-d Project**
- Full inference scheduler (Endpoint Picker)
- KV-cache-aware routing
- Predicted latency balancing (experimental)
- Load-aware balancing
- Customizable scoring algorithms

**⚠️ KServe LLMD**
- Basic Gateway API routing
- No built-in scheduler
- Can integrate with external schedulers

**❌ ServingRuntime + InferenceService**
- Round-robin by default
- No intelligent routing

---

### I need: Prefill/Decode Disaggregation

**✅ llm-d Project**
- Full P/D support with NIXL
- RDMA/InfiniBand/RoCE support
- xPyD (heterogeneous ratios)
- Selective P/D
- Well-documented guide

**✅ KServe LLMD**
- P/D support via `prefill:` spec
- Controller-managed
- ⚠️ Alpha - may have bugs

**❌ ServingRuntime + InferenceService**
- No P/D support

---

### I need: Multi-Accelerator Support

**✅ llm-d Project**
- NVIDIA GPUs ✅
- AMD GPUs (ROCm) ✅
- Google TPUs ✅
- Intel XPUs ✅
- Tested and maintained

**⚠️ KServe LLMD**
- Depends on runtime image
- Not specifically tested for all

**✅ ServingRuntime + InferenceService**
- NVIDIA GPUs ✅
- AMD GPUs ✅
- Depends on runtime

---

### I need: Production Support

**✅ llm-d Project**
- Community support (Slack, Google Groups)
- Active development
- No commercial support
- Well-tested

**⚠️ KServe LLMD**
- Community support
- Alpha - no production guarantees
- Limited testing

**✅ ServingRuntime + InferenceService**
- Red Hat support (with RHOAI subscription)
- Community support
- GA status

---

## 📚 Learning Resources

### For llm-d Project:

**Official Documentation:**
- Website: https://www.llm-d.ai
- GitHub: https://github.com/llm-d/llm-d
- Quickstart: `/guides/QUICKSTART.md`
- Well-lit Paths: `/guides/README.md`

**Community:**
- Slack: https://llm-d.ai/slack
- Google Groups: https://groups.google.com/g/llm-d-contributors
- Weekly Standup: Wednesdays 12:30 PM ET

**Key Guides:**
```
/guides/inference-scheduling/  # Start here
/guides/pd-disaggregation/     # For large models
/guides/wide-ep-lws/           # For MoE models
/docs/proposals/llm-d.md       # Architecture deep dive
```

### For KServe LLMD CRD:

**This Repository:**
- Clarification: `llmd-DOC/00_IMPORTANT_CLARIFICATION.md`
- User Guide: `llmd-DOC/LLMD_USER_GUIDE_ALL_FEATURES.md`
- Technical: `llmd-DOC/LLMD_COMPLETE_ARCHITECTURE_AND_FEATURES.md`
- Testing: `llmd-DOC/LLMD_E2E_TEST_REPORT.md`

**KServe Docs:**
- GitHub: https://github.com/kserve/kserve
- Website: https://kserve.github.io/website/

### For ServingRuntime + InferenceService:

**RHOAI Documentation:**
- Official Docs: https://access.redhat.com/documentation/en-us/red_hat_openshift_ai
- This repo: `llmd-DOC/LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md`

**Test Examples:**
- `opendatahub-tests/tests/model_serving/model_runtime/vllm/`

---

## 🎓 Summary

### Quick Recommendations:

| Your Situation | Recommended Approach |
|----------------|---------------------|
| **Production + General Kubernetes** | llm-d Project |
| **Production + RHOAI/OpenShift** | ServingRuntime + InferenceService |
| **Large Models (70B+)** | llm-d Project (P/D disaggregation) |
| **MoE Models (DeepSeek-R1)** | llm-d Project (Wide EP) |
| **Small Models (< 13B)** | ServingRuntime + InferenceService |
| **Learning/Experimentation** | llm-d Project (best docs) |
| **Need Commercial Support** | RHOAI (ServingRuntime) |
| **Need Intelligent Scheduling** | llm-d Project |
| **Want Controller-Managed** | Wait for LLMD GA, or use InferenceService |
| **Want Maximum Flexibility** | llm-d Project |

### Key Insight:

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  For most production deployments:                    │
│                                                      │
│  • Use llm-d Project (general Kubernetes)            │
│  • Use ServingRuntime + InferenceService (RHOAI)     │
│                                                      │
│  KServe LLMD CRD is not yet production-ready.        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

**Need Help Deciding?**

1. Read [00_IMPORTANT_CLARIFICATION.md](./00_IMPORTANT_CLARIFICATION.md)
2. Check [LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md](./LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md)
3. Try llm-d quickstart: `llm-d-repo/guides/QUICKSTART.md`

**Still unsure? Start with llm-d Project** - it's production-ready, well-documented, and provides the most flexibility.


