# LLMD (LLM Inference Service) Documentation

**Last Updated:** October 13, 2025

This folder contains comprehensive documentation for **KServe LLMInferenceService** (LLMD), a Kubernetes CRD in KServe v1alpha1 for deploying Large Language Models.

## ⚠️ CRITICAL: Two Different Systems!

**There are TWO separate systems with similar names:**

| System | What It Is | Status | Location |
|--------|------------|--------|----------|
| **KServe LLMD** | Kubernetes CRD (`serving.kserve.io/v1alpha1`) | Alpha | **This documentation** |
| **llm-d Project** | Production vLLM serving stack (Helm charts) | v0.3.0 GA | https://www.llm-d.ai |

**👉 READ FIRST:** [00_IMPORTANT_CLARIFICATION.md](./00_IMPORTANT_CLARIFICATION.md) to understand the difference!

---

---

## 📚 Documentation Index

### ⚠️ Start Here

#### 0. [00_IMPORTANT_CLARIFICATION.md](./00_IMPORTANT_CLARIFICATION.md) 🔴 **READ FIRST**
**Critical: Understand KServe LLMD vs. llm-d Project**

- **What it covers:**
  - Two separate systems with similar names
  - KServe LLMInferenceService CRD vs. llm-d open-source project
  - How they relate and differ
  - Which one to use for your needs
  - Why this documentation exists

- **Who should read this:**
  - **EVERYONE - Read this before anything else!**
  - Anyone confused about "LLMD" vs "llm-d"
  - Users deciding between approaches

#### 0b. [QUICK_DECISION_GUIDE.md](./QUICK_DECISION_GUIDE.md) 🎯 **CHOOSING AN APPROACH**
**Quick decision guide for selecting the right LLM serving approach**

- **What it covers:**
  - Decision tree for choosing the right approach
  - Feature-by-feature comparison matrix
  - Recommendations by use case
  - Learning resources for each approach

- **Who should read this:**
  - Users deciding which approach to use
  - DevOps engineers evaluating options
  - Anyone planning production deployments

---

### 🏗️ Architecture & Concepts

#### 1. [KSERVE_LLMD_COMPLETE_IMPLEMENTATION_GUIDE.md](./KSERVE_LLMD_COMPLETE_IMPLEMENTATION_GUIDE.md) 🔧 **IMPLEMENTATION DEEP DIVE**
**Complete guide showing how KServe implements llm-d architecture**

- **What it covers:**
  - How llm-d architecture maps to KServe LLMD
  - Complete controller implementation details
  - How each llm-d component is used in KServe
  - Code examples from the controller
  - Resource creation flow with code
  - Request flow architecture (basic → scheduler → disaggregated)
  - Integration points (Gateway API, vLLM, NIXL)
  - Feature-by-feature implementation guide

- **Who should read this:**
  - **KServe contributors**
  - Developers understanding the codebase
  - Anyone bridging llm-d and KServe knowledge
  - Platform engineers implementing similar patterns

- **Key sections:**
  - llm-d vs KServe LLMD relationship
  - Controller reconciliation with code
  - How disaggregation works in KServe
  - EPP (scheduler) integration
  - Complete request flows with diagrams

---

#### 2. [LLMD_USER_GUIDE_ALL_FEATURES.md](./LLMD_USER_GUIDE_ALL_FEATURES.md) ⭐ **START HERE FOR USERS**
**Practical user guide - All features explained simply**

- **What it covers:**
  - Every feature explained in simple terms
  - Practical "how to deploy" examples
  - What you'll actually see (pods, containers, URLs)
  - How to use each feature
  - When to use each feature
  - Real request/response examples
  - Troubleshooting guide
  - Best practices for small, large, and very large models

- **Who should read this:**
  - **End users deploying LLMs**
  - Developers getting started with LLMD
  - Anyone who wants practical, simple explanations
  - DevOps engineers deploying models

- **Key sections:**
  - 14 features with simple, practical explanations
  - Deployment cheat sheet
  - Container count reference
  - Best practices by model size

---

#### 3. [LLMD_COMPLETE_ARCHITECTURE_AND_FEATURES.md](./LLMD_COMPLETE_ARCHITECTURE_AND_FEATURES.md) ⭐ **START HERE FOR ARCHITECTS**
**Complete technical guide to LLMD architecture and all features**

- **What it covers:**
  - Full LLMD architecture from the KServe codebase
  - All 17 features explained in detail
  - How each feature works internally
  - Container structure for EVERY deployment scenario
  - Request flow for EVERY feature
  - Real-world deployment examples
  - What pods/containers you'll see for each feature
  - Step-by-step behavior explanations

- **Who should read this:**
  - Everyone! This is the most comprehensive LLMD document
  - Developers implementing LLMD deployments
  - Architects designing LLM infrastructure
  - Anyone who wants to understand LLMD deeply

- **Key sections:**
  - 17 features with detailed explanations
  - Container structure tables (init, main, sidecar)
  - Request flow diagrams for each feature
  - Real deployment examples with resource counts

---

#### 4. [LLMD_PREFILL_DECODE_ARCHITECTURE.md](./LLMD_PREFILL_DECODE_ARCHITECTURE.md)
**Essential reading for understanding LLMD disaggregated serving**

- **What it covers:**
  - Prefill/Decode architecture overview
  - How request routing works
  - Component explanations (Prefill, Decode, Routing Sidecar, Scheduler/EPP, InferencePool)
  - Detailed request flow with diagrams
  - Configuration examples
  - When to use disaggregated serving

- **Who should read this:**
  - Anyone deploying LLMD for the first time
  - Architects designing LLM serving infrastructure
  - Developers debugging request routing issues

- **Key takeaways:**
  - Prefill processes prompts (fast, parallel)
  - Decode generates tokens (slower, sequential)
  - Scheduler intelligently routes requests
  - Separating workloads allows independent scaling

---

#### 5. [LLMD_MULTI_GPU_PARALLELISM.md](./LLMD_MULTI_GPU_PARALLELISM.md)
**Complete guide to distributing LLMD workloads across multiple GPUs**

- **What it covers:**
  - Tensor Parallelism (split model layers)
  - Pipeline Parallelism (split model stages)
  - Data Parallelism (replicate model)
  - Expert Parallelism (for MoE models)
  - Configuration examples for different GPU counts
  - Best practices for each parallelism type
  - Real-world scenarios (2 GPUs, 4 GPUs, 8 GPUs, 16+ GPUs)

- **Who should read this:**
  - Anyone deploying large models (> 13B parameters)
  - Teams with multi-GPU infrastructure
  - Performance engineers optimizing throughput

- **Key takeaways:**
  - `parallelism.tensor` must match GPU allocation
  - Different strategies for prefill vs decode
  - Larger models need more aggressive parallelism
  - Trade-offs between latency and throughput

---

### 🔬 Testing & Validation

#### 6. [LLMD_E2E_TEST_REPORT.md](./LLMD_E2E_TEST_REPORT.md)
**Complete end-to-end testing results**

- **What it covers:**
  - All E2E test scenarios executed
  - Pod health verification (prefill, decode, scheduler)
  - Inference endpoint testing
  - GPU allocation and utilization
  - Resource QoS validation
  - Performance measurements
  - Issues encountered and resolutions

- **Test results:**
  - ✅ LLMInferenceService: Ready=True
  - ✅ Prefill: 2/2 pods running
  - ✅ Decode: 2/2 pods running
  - ✅ Inference: < 1s latency
  - ✅ GPU: 4 GPUs allocated, NVIDIA H200, 130GB model loaded

- **Who should read this:**
  - QE teams validating LLMD functionality
  - Anyone troubleshooting deployment issues
  - Teams preparing for production deployment

---

#### 7. [LLMD_PATCH_TEST_RESULTS.md](./LLMD_PATCH_TEST_RESULTS.md)
**Results of testing configuration changes via `oc patch`**

- **What it covers:**
  - Testing parallelism configuration
  - Increasing prefill replicas (HA)
  - Adding readiness probes
  - Setting Guaranteed QoS
  - Issues with rolling updates
  - Lessons learned about parallelism vs GPU allocation

- **Key findings:**
  - ✅ All patches applied successfully
  - ⚠️ Parallelism config ≠ GPU allocation (must update both!)
  - ⚠️ Multiple rapid patches cause rolling update issues
  - ✅ Guaranteed QoS improves stability

- **Who should read this:**
  - Anyone modifying LLMD configurations
  - Teams implementing infrastructure-as-code
  - Anyone debugging patch/update issues

---

#### 8. [LLMD_TESTING_SUMMARY.md](./LLMD_TESTING_SUMMARY.md)
**Executive summary of all LLMD testing**

- **What it covers:**
  - High-level test results
  - Quick reference for test status
  - Links to detailed reports

- **Who should read this:**
  - Management reviewing test coverage
  - Anyone needing a quick status overview

---

### 🔍 Analysis & Comparison

#### 9. [LLMD_DEPLOYMENT_ANALYSIS.md](./LLMD_DEPLOYMENT_ANALYSIS.md)
**Detailed analysis of a specific LLMD deployment**

- **What it covers:**
  - Analysis of `llmd-gpu-deployment` namespace
  - What's correctly configured
  - What's missing or can be improved
  - Specific recommendations for the deployment
  - Resource allocation breakdown

- **Deployment analyzed:**
  - Model: Qwen2.5-7B-Instruct
  - Prefill: 1 pod (analyzed before patches)
  - Decode: 2 pods
  - Total: 3 GPUs

- **Who should read this:**
  - Anyone analyzing an existing LLMD deployment
  - Teams optimizing resource allocation
  - Anyone learning from a real-world example

---

#### 10. [LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md](./LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md)
**Critical comparison: LLMInferenceService vs ServingRuntime approach**

- **What it covers:**
  - Two approaches to deploying LLMs in RHOAI
  - `LLMInferenceService` (v1alpha1, alpha status)
  - `ServingRuntime` + `InferenceService` (v1beta1, stable)
  - Why RHOAI QE uses ServingRuntime
  - Template variable substitution bug in LLMD
  - When to use each approach

- **Key finding:**
  - ⚠️ RHOAI QE uses `ServingRuntime` + `InferenceService`, NOT `LLMInferenceService`
  - ⚠️ `LLMInferenceService` has template substitution bugs
  - ✅ `ServingRuntime` approach is stable and production-ready

- **Who should read this:**
  - **Everyone** deploying LLMs in RHOAI
  - Teams deciding on deployment approach
  - Anyone experiencing LLMD issues

---

## 🎯 Quick Start Guide

### For End Users (Want to Deploy):
1. ⭐ Start with **LLMD_USER_GUIDE_ALL_FEATURES.md** for practical, simple explanations
2. Deploy your first LLM following the examples
3. Read **LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md** to understand alternatives

### For Architects/Engineers (Want to Understand Deeply):
1. ⭐ Start with **LLMD_COMPLETE_ARCHITECTURE_AND_FEATURES.md** for complete technical details
2. Then read **LLMD_PREFILL_DECODE_ARCHITECTURE.md** for disaggregated serving
3. Study **LLMD_MULTI_GPU_PARALLELISM.md** for GPU configuration

### For Troubleshooting:
1. Check **LLMD_E2E_TEST_REPORT.md** for validation steps
2. Review **LLMD_PATCH_TEST_RESULTS.md** for common issues
3. Compare with **LLMD_DEPLOYMENT_ANALYSIS.md** for best practices

### For Production Deployment:
1. Review **LLMD_E2E_TEST_REPORT.md** for complete test coverage
2. Study **LLMD_MULTI_GPU_PARALLELISM.md** for resource planning
3. Consider **LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md** for stable alternatives

---

## 📊 Documentation Summary

| Document | Type | Focus | Status |
|----------|------|-------|--------|
| 00_IMPORTANT_CLARIFICATION.md | 🔴 Critical | LLMD vs llm-d | **READ FIRST** |
| QUICK_DECISION_GUIDE.md | 🎯 Decision Guide | Choosing Approach | **READ 2ND** |
| KSERVE_LLMD_COMPLETE_IMPLEMENTATION_GUIDE.md | 🔧 Implementation | llm-d → KServe | **NEW** ⭐ |
| LLMD_USER_GUIDE_ALL_FEATURES.md | ⭐ User Guide | Practical Deployment | Complete |
| LLMD_COMPLETE_ARCHITECTURE_AND_FEATURES.md | ⭐ Technical Guide | All Features + Architecture | Complete |
| LLMD_PREFILL_DECODE_ARCHITECTURE.md | Architecture | Concepts & Design | Complete |
| LLMD_MULTI_GPU_PARALLELISM.md | Configuration | GPU Distribution | Complete |
| LLMD_E2E_TEST_REPORT.md | Testing | End-to-End Validation | Complete ✅ |
| LLMD_PATCH_TEST_RESULTS.md | Testing | Configuration Changes | Complete |
| LLMD_TESTING_SUMMARY.md | Testing | Executive Summary | Complete |
| LLMD_DEPLOYMENT_ANALYSIS.md | Analysis | Real Deployment | Complete |
| LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md | Comparison | Approach Selection | Critical ⚠️ |

---

## ⚠️ Important Notes

### Critical Finding: LLMD Template Bug
The `LLMInferenceService` controller (v1alpha1) has a bug with template variable substitution:
- Variables like `{{.Name}}` and `{{.Spec.Model.Name}}` are not substituted
- This causes vLLM to receive malformed arguments and crash
- **Workaround:** Avoid template variables in LLMD configuration
- **Alternative:** Use stable `ServingRuntime` + `InferenceService` approach

See **LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md** for details.

---

## 🔗 Related Resources

### Internal Documentation:
- `llmd-test-yamls/` - Test YAML manifests used during testing
- `opendatahub-tests/` - RHOAI QE test suite (reference)

### External Resources:
- [KServe Documentation](https://kserve.github.io/website/)
- [vLLM Documentation](https://docs.vllm.ai/)
- [RHOAI Documentation](https://access.redhat.com/documentation/en-us/red_hat_openshift_ai/)

---

## 📝 Testing Status

### ✅ Completed Tests:
- [x] Basic LLMD deployment
- [x] Prefill/decode architecture validation
- [x] GPU allocation verification
- [x] Inference endpoint testing
- [x] Configuration patching
- [x] Resource QoS verification
- [x] High availability (2 prefill replicas)
- [x] Readiness probe configuration
- [x] Performance measurement

### 🎯 Test Results:
- **Overall Status:** ✅ FUNCTIONAL
- **Prefill Pods:** 2/2 Running
- **Decode Pods:** 2/2 Running
- **Scheduler:** 1/1 Running
- **Inference Latency:** < 1 second
- **GPU Utilization:** 130GB/144GB (90.5%)

---

## 📧 Contact

For questions or issues with this documentation:
1. Review the specific document for troubleshooting sections
2. Check the E2E test report for validation steps
3. Compare with the deployment analysis for best practices

---

## 📅 Document History

- **October 13, 2025:** Initial documentation created
  - Completed E2E testing
  - Identified LLMD template bug
  - Validated prefill/decode architecture
  - Tested GPU allocation and parallelism
  - Compared LLMD vs ServingRuntime approaches

---

**Last Updated:** October 13, 2025  
**Documentation Status:** Complete and validated  
**Test Coverage:** Comprehensive (basic to advanced scenarios)

