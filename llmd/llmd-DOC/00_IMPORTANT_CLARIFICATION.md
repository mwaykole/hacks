# ⚠️ IMPORTANT CLARIFICATION: KServe LLMD vs. llm-d Project

**Date:** October 13, 2025  
**Purpose:** Clarify the relationship between two distinct systems

---

## Two Different Systems

There are **TWO SEPARATE SYSTEMS** with similar names and related concepts:

### 1. KServe LLMInferenceService (This Repo)

**Location:** `/home/cloud-user/temp/kserve/`  
**What it is:** A Kubernetes CRD in the KServe project  
**API Version:** `serving.kserve.io/v1alpha1`  
**Status:** Alpha/Experimental  
**Source Code Reference:**

```go
// From pkg/apis/serving/v1alpha1/llm_inference_service_types.go:
// Prefill configuration for disaggregated serving.
// When this section is included, the controller creates a separate deployment 
// for prompt processing (prefill) in addition to the main 'decode' deployment, 
// inspired by the llm-d architecture.
```

**Key Characteristics:**
- Kubernetes Custom Resource Definition (CRD)
- Controller-based reconciliation
- Creates Deployments, Services, HTTPRoutes automatically
- Configuration inheritance via `baseRefs`
- Template variables (⚠️ currently buggy)
- Manages full lifecycle via Kubernetes controllers

**Example Usage:**
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B
  replicas: 2
  prefill:
    replicas: 1
  router:
    gateway: {}
    route: {}
```

---

### 2. llm-d Project (Separate Repository)

**Location:** `https://github.com/llm-d/llm-d.git`  
**What it is:** A Kubernetes-native distributed inference serving stack  
**Website:** https://www.llm-d.ai  
**Status:** v0.3.0 released (October 2025)

**Key Characteristics:**
- **Not a CRD** - Uses Helm charts + standard Kubernetes resources
- Provides "well-lit paths" (tested deployment recipes)
- Focuses on vLLM + Inference Gateway integration
- Production-ready with benchmarks
- Supports multiple accelerators (NVIDIA, AMD, Google TPU, Intel XPU)
- Community-driven open-source project

**Components:**
1. **Inference Scheduler** (llm-d-inference-scheduler)
   - Built on Kubernetes Gateway API Inference Extension (IGW)
   - Uses Envoy proxy for intelligent load balancing
   - KV-cache-aware routing
   - Predicted latency balancing (experimental)

2. **Model Server** (vLLM)
   - Deployed via Helm charts
   - Supports prefill/decode disaggregation via NIXL
   - Multi-GPU and multi-node configurations

3. **Well-lit Paths:**
   - Intelligent Inference Scheduling
   - Prefill/Decode Disaggregation
   - Wide Expert-Parallelism (for MoE models like DeepSeek-R1)

**Example Deployment:**
```bash
# llm-d uses Helm + helmfile, not CRDs
cd guides/inference-scheduling
helmfile apply -n llm-d-inference-scheduler

# Creates:
# - Envoy-based Inference Gateway
# - vLLM deployments
# - InferencePool resources
# - HTTPRoute for routing
```

---

## Relationship Between the Two

### How They Relate:

```
┌────────────────────────────────────────────────────────────┐
│ llm-d Project (Original)                                   │
│ • Open-source community project                            │
│ • Established patterns for disaggregated serving           │
│ • vLLM + IGW + Envoy architecture                          │
│ • Production-ready Helm charts                             │
└────────────────┬───────────────────────────────────────────┘
                 │
                 │ Inspired ↓
                 │
┌────────────────┴───────────────────────────────────────────┐
│ KServe LLMInferenceService (This Repo)                     │
│ • KServe CRD that adopts llm-d concepts                    │
│ • Controller-managed lifecycle                             │
│ • Declarative Kubernetes-native approach                   │
│ • Integrates with existing KServe ecosystem                │
└────────────────────────────────────────────────────────────┘
```

**Key Differences:**

| Aspect | KServe LLMD CRD | llm-d Project |
|--------|-----------------|---------------|
| **Type** | Kubernetes CRD | Helm charts + standard K8s resources |
| **API** | `serving.kserve.io/v1alpha1` | Uses Gateway API Inference Extension |
| **Lifecycle** | Controller-managed | User-managed via Helm |
| **Status** | Alpha/Experimental | Production-ready (v0.3.0) |
| **Deployment** | `kubectl apply -f llmisvc.yaml` | `helmfile apply` |
| **Scheduler** | Not included (uses Gateway API) | Included (llm-d-inference-scheduler) |
| **Flexibility** | Opinionated (controller decides) | Highly customizable |
| **KServe Integration** | Full | None (standalone) |
| **Production Usage** | Not recommended (alpha) | Recommended |

---

## Which One Should You Use?

### Use KServe LLMInferenceService IF:

✅ You're already using KServe ecosystem  
✅ You want fully automated lifecycle management  
✅ You prefer declarative CRD-based approach  
✅ You're okay with alpha/experimental features  
⚠️ **BUT NOTE:** Template variables are buggy, production use not recommended

### Use llm-d Project IF:

✅ You need production-ready LLM serving  
✅ You want tested, benchmarked configurations  
✅ You need intelligent inference scheduling  
✅ You want to use vLLM optimally  
✅ You need multi-accelerator support  
✅ You want community-supported well-lit paths  
🎯 **RECOMMENDED** for production deployments

### Use Standard ServingRuntime + InferenceService IF:

✅ You're in RHOAI/OpenShift  
✅ You want stable, GA features  
✅ You don't need disaggregated serving  
✅ Simpler deployments (< 13B models)  
🎯 **RECOMMENDED** for RHOAI users (see LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md)

---

## Documentation in This Folder

### What These Docs Cover:

All documentation in this `llmd-DOC/` folder describes the **KServe LLMInferenceService CRD**, NOT the llm-d project.

|-----------------------------------------------------------------------------------------|
| Document | What It Covers                                                               |
|----------|------------------------------------------------------------------------------|
| `LLMD_USER_GUIDE_ALL_FEATURES.md` | KServe LLMD CRD features (user perspective)         |
| `LLMD_COMPLETE_ARCHITECTURE_AND_FEATURES.md` | KServe LLMD CRD architecture (technical) |
| `LLMD_PREFILL_DECODE_ARCHITECTURE.md` | How prefill/decode works in KServe LLMD         |
| `LLMD_MULTI_GPU_PARALLELISM.md` | Multi-GPU config in KServe LLMD                       |
| `LLMD_*_TEST_REPORT.md` | Testing results for KServe LLMD                               |
|-----------------------------------------------------------------------------------------|
### For llm-d Project Documentation:

**Official Sources:**
- **Website:** https://www.llm-d.ai
- **GitHub:** https://github.com/llm-d/llm-d
- **Slack:** https://llm-d.ai/slack
- **Google Groups:** https://groups.google.com/g/llm-d-contributors

**Key Docs in llm-d Repo:**
- `/guides/README.md` - Well-lit paths overview
- `/guides/QUICKSTART.md` - Step-by-step tutorial
- `/guides/inference-scheduling/` - Intelligent scheduling guide
- `/guides/pd-disaggregation/` - Prefill/decode guide
- `/guides/wide-ep-lws/` - Expert parallelism guide
- `/docs/proposals/llm-d.md` - Project proposal and design

---

## Code References Showing the Relationship

**From KServe codebase:**
```go
// pkg/apis/serving/v1alpha1/llm_inference_service_types.go

// Prefill configuration for disaggregated serving.
// When this section is included, the controller creates a separate deployment 
// for prompt processing (prefill) in addition to the main 'decode' deployment, 
// inspired by the llm-d architecture.
// This allows for independent scaling and hardware allocation for prefill and decode steps.
Prefill *WorkloadSpec `json:"prefill,omitempty"`
```

**From KServe ROADMAP.md:**
```markdown
## Objective: "Support GenAI inference"
- LLM Serving Runtimes
   * Support Speculative Decoding with vLLM runtime
   * Support LoRA adapters
   * Support multi-host, multi-GPU inference runtime

- LLM Gateway
   * Support multiple LLM providers
   * Support token based rate limiting
   * Support LLM router with traffic shaping, fallback, load balancing
   * LLM Gateway observability for metrics and cost reporting
```

This shows KServe is adopting llm-d concepts, but they remain separate projects.

---

## Summary

🔑 **Key Takeaway:**
- **KServe LLMInferenceService** = A Kubernetes CRD that adopted llm-d concepts
- **llm-d Project** = The original open-source project providing production-ready vLLM serving

📚 **This Documentation:**
- Covers the **KServe LLMInferenceService CRD** (v1alpha1)
- Located in the KServe repository
- Focus on testing, understanding, and using the CRD

🚀 **For Production:**
- Consider **llm-d project** for production-ready serving
- Or use **ServingRuntime + InferenceService** in RHOAI
- KServe LLMD is alpha - use with caution

---

**References:**
- KServe Repo: https://github.com/kserve/kserve
- llm-d Repo: https://github.com/llm-d/llm-d
- llm-d Website: https://www.llm-d.ai
- Gateway API Inference Extension: https://github.com/kubernetes-sigs/gateway-api-inference-extension
- vLLM: https://docs.vllm.ai


