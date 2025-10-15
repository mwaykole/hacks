# LLMD & KServe Complete Textbook
## The Definitive Guide to Large Language Model Serving on Kubernetes

**Version:** 1.0  
**Last Updated:** October 14, 2025  
**Authors:** Community Contributors  
**Target Audience:** Newcomers to LLM serving, ML Engineers, DevOps Engineers, Platform Engineers

---

## Table of Contents

### Part I: Foundations
1. [Introduction](#chapter-1-introduction)
2. [LLM Inference Fundamentals](#chapter-2-llm-inference-fundamentals)
3. [Why Kubernetes for LLMs](#chapter-3-why-kubernetes-for-llms)
4. [The Problem Space](#chapter-4-the-problem-space)

### Part II: Core Concepts
5. [Understanding KServe](#chapter-5-understanding-kserve)
6. [The llm-d Project](#chapter-6-the-llm-d-project)
7. [LLMD (LLMInferenceService) Deep Dive](#chapter-7-llmd-deep-dive)
8. [Prefill vs Decode Architecture](#chapter-8-prefill-vs-decode-architecture)

### Part III: The Components
9. [Envoy and Gateway API](#chapter-9-envoy-and-gateway-api)
10. [The Scheduler (EPP)](#chapter-10-the-scheduler-epp)
11. [Routing Sidecar](#chapter-11-routing-sidecar)
12. [vLLM Model Server](#chapter-12-vllm-model-server)
13. [InferencePool and InferenceModel](#chapter-13-inferencepool-and-inferencemodel)

### Part IV: Advanced Topics
14. [GPU Parallelism Strategies](#chapter-14-gpu-parallelism-strategies)
15. [Multi-Node Deployments](#chapter-15-multi-node-deployments)
16. [KV Cache Management](#chapter-16-kv-cache-management)
17. [Performance Tuning](#chapter-17-performance-tuning)

### Part V: Hands-On Labs
18. [Lab 1: Your First LLMD Service](#chapter-18-lab-1)
19. [Lab 2: Disaggregated Prefill/Decode](#chapter-19-lab-2)
20. [Lab 3: Production Deployment](#chapter-20-lab-3)
21. [Lab 4: Multi-Node Setup](#chapter-21-lab-4)

### Part VI: Operations
22. [Monitoring and Observability](#chapter-22-monitoring)
23. [Troubleshooting Guide](#chapter-23-troubleshooting)
24. [Capacity Planning](#chapter-24-capacity-planning)
25. [Security Best Practices](#chapter-25-security)

### Part VII: Integration
26. [ODH and RHOAI Integration](#chapter-26-odh-rhoai)
27. [ServingRuntime vs LLMD](#chapter-27-servingruntime-vs-llmd)
28. [Migration Strategies](#chapter-28-migration)

### Appendices
- [Appendix A: CRD Reference](#appendix-a-crd-reference)
- [Appendix B: Command Reference](#appendix-b-command-reference)
- [Appendix C: Glossary](#appendix-c-glossary)
- [Appendix D: Resources](#appendix-d-resources)

---

# Part I: Foundations

---

## Chapter 1: Introduction

### Welcome to the Future of LLM Serving

If you're reading this, you've probably heard about Large Language Models (LLMs) like GPT, Llama, or Mistral. You might even be tasked with deploying one in your organization. This book will take you from zero knowledge to confidently running production LLM workloads on Kubernetes.

### What You'll Learn

By the end of this textbook, you will:
- Understand how LLM inference works at a fundamental level
- Know why serving LLMs is different from traditional ML models
- Master the KServe LLMD architecture and all its components
- Deploy, tune, and troubleshoot production LLM services
- Make informed decisions about architecture patterns
- Understand the trade-offs between different deployment strategies

### Who This Book Is For

This book assumes:
- Basic understanding of Kubernetes (pods, services, deployments)
- Familiarity with containers and Docker
- Some exposure to machine learning concepts
- No prior experience with LLM serving required

### How to Use This Book

- **Read sequentially** for complete understanding
- **Skip to labs** if you learn by doing
- **Use as reference** for specific components
- **Bookmark troubleshooting** for production issues

### The Two "LLMDs" (Important Clarification)

There are two related but distinct things with similar names:

**1. KServe LLMD (LLMInferenceService)**
- A Kubernetes Custom Resource Definition (CRD)
- Part of KServe (serving.kserve.io/v1alpha1)
- Lets you declare an entire LLM deployment as one YAML
- Currently in alpha status
- **This is what most of this book focuses on**

**2. The llm-d Project**
- A broader Kubernetes-native framework
- Collection of components, guides, and Helm charts
- Provides "well-lit paths" for production LLM serving
- Includes inference scheduler, model service, routing components
- **KServe LLMD implements many llm-d concepts**

Think of it this way:
- **llm-d** is the architecture philosophy and toolkit
- **KServe LLMD** is one implementation of that philosophy

Both are valuable, and understanding one helps you understand the other.

---

## Chapter 2: LLM Inference Fundamentals

### What Happens When You Query an LLM?

Let's start with the basics. When you send a prompt like "Write me a story about a robot," here's what happens inside:

```
YOU: "Write me a story about a robot"
     ↓
[1. TOKENIZATION]
     "Write" → 5838
     "me" → 502
     "a" → 64
     "story" → 3364
     ...
     ↓
[2. PREFILL PHASE]
     Process ALL tokens in parallel
     Build KV cache for every token
     Generate first output token: "Once"
     ↓
[3. DECODE PHASE]
     Generate token 2: "upon" (using KV from prefill)
     Generate token 3: "a" (using KV from prefill + previous tokens)
     Generate token 4: "time" (using KV from all previous)
     ...continue until done or max tokens
     ↓
RESPONSE: "Once upon a time, there was a robot named..."
```

### The Two Phases Explained

#### Phase 1: Prefill (a.k.a. Prompt Processing)

**What it does:** Processes your entire prompt to understand context

**Characteristics:**
- **Parallel:** All prompt tokens processed simultaneously
- **Compute-intensive:** Matrix multiplications across all layers
- **Fast but expensive:** Uses lots of GPU compute
- **One-time:** Only runs once per conversation

**Visual Analogy:**
```
Think of reading a book before answering questions about it:
┌─────────────────────────────────────┐
│  "Once upon a time in a galaxy..." │  ← Your prompt (100 tokens)
└─────────────────────────────────────┘
         ↓
    [PREFILL]
         ↓
┌─────────────────────────────────────┐
│   Mental Index (KV Cache)           │  ← Stores understanding of every token
│   Token 1: context about "Once"     │
│   Token 2: context about "upon"     │
│   ...                               │
│   Token 100: context about galaxy   │
└─────────────────────────────────────┘
```

**GPU Perspective:**
```
During prefill, your GPU is working HARD:
┌────────────────────────────┐
│ GPU 0: [██████████████] 95%│  All GPUs computing in parallel
│ GPU 1: [██████████████] 93%│  Processing attention for all
│ GPU 2: [██████████████] 94%│  prompt tokens simultaneously
│ GPU 3: [██████████████] 96%│
└────────────────────────────┘
Time: ~100ms for 100 tokens
```

#### Phase 2: Decode (a.k.a. Token Generation)

**What it does:** Generates response tokens one at a time

**Characteristics:**
- **Sequential:** Must wait for token N before generating N+1
- **Memory-intensive:** Constantly accessing KV cache
- **Slow per token:** Each token needs full model forward pass
- **Long-running:** Continues until complete sentence/paragraph

**Visual Analogy:**
```
Think of answering questions one word at a time:
┌─────────────────────────┐
│  KV Cache (your notes)  │
└────────┬────────────────┘
         │
         ▼
    [DECODE]
         │
         ├─→ Generate token 1: "The"     (50ms)
         ├─→ Generate token 2: "robot"   (50ms)
         ├─→ Generate token 3: "was"     (50ms)
         ├─→ Generate token 4: "named"   (50ms)
         └─→ ... (repeat 100+ times)
```

**GPU Perspective:**
```
During decode, GPU is memory-bound:
┌────────────────────────────┐
│ GPU 0: [████░░░░░░] 35%    │  Lower utilization but
│ GPU 1: [███░░░░░░░] 28%    │  constantly reading KV cache
│ GPU 2: [████░░░░░░] 32%    │  Sequential, can't parallelize
│ GPU 3: [███░░░░░░░] 30%    │  across tokens
└────────────────────────────┘
Time: ~50ms × 200 tokens = 10 seconds
```

### The Key Insight

**Prefill and decode have completely different resource profiles:**

| Aspect | Prefill | Decode |
|--------|---------|--------|
| Parallelism | HIGH (all tokens at once) | LOW (one token at time) |
| GPU Compute | HIGH (matrix ops) | MEDIUM (lighter ops) |
| Memory Bandwidth | MEDIUM | HIGH (constant KV reads) |
| Duration | Short (100ms) | Long (10s) |
| GPU Utilization | 90-95% | 30-40% |

**This is why disaggregation helps:** You can optimize each phase separately!

### What is KV Cache?

KV cache is the "memory" of the conversation. Here's what it contains:

```
For each transformer layer (say 80 layers in Llama-70B):
  For each token in the prompt:
    Store Key vector (size: 8192 floats)
    Store Value vector (size: 8192 floats)

Example: 100-token prompt × 80 layers × 8192×2 floats
       = ~100 million floats
       = ~400 MB (in FP16)

For a 2000-token context: ~8 GB just for KV cache!
```

**Why KV cache matters:**
- **Without it:** You'd recompute attention for all previous tokens every time (exponential cost)
- **With it:** You only compute new tokens (linear cost)
- **Trade-off:** Uses lots of GPU memory (VRAM)

---

## Chapter 3: Why Kubernetes for LLMs

### The Challenge

Serving LLMs in production means:
- Models are 10-100+ GB in size
- Need expensive GPUs ($10-40k each)
- Want high availability and auto-scaling
- Must handle variable load (spikes, valleys)
- Need efficient resource sharing
- Want gradual rollouts and A/B testing

### What Kubernetes Provides

**1. Resource Orchestration**
```yaml
resources:
  requests:
    nvidia.com/gpu: "8"  # K8s assigns 8 GPUs to your pod
    memory: "256Gi"      # K8s reserves memory
  limits:
    nvidia.com/gpu: "8"  # K8s enforces limits
```

**2. High Availability**
```yaml
replicas: 4  # K8s maintains 4 pods, auto-restarts failures
```

**3. Service Discovery & Load Balancing**
```yaml
kind: Service  # K8s creates stable endpoint, balances traffic
```

**4. Declarative Configuration**
```yaml
kind: LLMInferenceService  # Declare desired state,
# K8s makes it happen
```

**5. Scaling**
```yaml
kubectl scale llmisvc/my-model --replicas=10  # Easy scaling
```

### Why Not Just Run Docker?

You could, but you'd need to:
- Manually assign GPUs to containers
- Write your own health checking
- Implement load balancing
- Handle container crashes
- Manage networking between containers
- Implement rolling updates
- Monitor resource usage
- **Kubernetes does all this for you**

### The KServe Layer

KServe adds ML-specific features on top of Kubernetes:
- **Model serving abstractions:** Don't think "containers," think "models"
- **Intelligent routing:** Not just round-robin
- **Model versioning:** Canary, blue/green deployments
- **Explainability & monitoring:** ML-aware observability
- **Standardized APIs:** OpenAI-compatible endpoints

---

## Chapter 4: The Problem Space

### Problem 1: GPU Underutilization

**Traditional serving (one pod does everything):**
```
┌────────────────────────────────────────────┐
│  Single Pod (8 GPUs)                       │
│                                            │
│  Request comes in:                         │
│  [PREFILL: 100ms]  ████████████ (all GPUs)│  95% utilization
│  [DECODE: 10s]     ███░░░░░░░░ (all GPUs)│  30% utilization
│                                            │
│  Average utilization: ~35%                 │
│  You're wasting 65% of $80k in GPUs! 😱   │
└────────────────────────────────────────────┘
```

**Solution: Disaggregate**
```
┌──────────────────────────┐  ┌──────────────────────────┐
│  Prefill Pod (8 GPUs)    │  │  Decode Pods (1 GPU each)│
│  ████████████ 95%        │  │  Pod 1: ███ 30%          │
│                          │  │  Pod 2: ███ 30%          │
│  Runs only prefill       │  │  Pod 3: ███ 30%          │
│  Optimized for parallel  │  │  ... (16 decode pods)    │
│  processing              │  │                          │
└──────────────────────────┘  └──────────────────────────┘
  2 pods × 8 GPUs = 16 GPUs     16 pods × 1 GPU = 16 GPUs
  Total: 32 GPUs, much better utilization!
```

### Problem 2: Unpredictable Latency

**Without intelligent routing:**
```
3 pods, all equally loaded:
Request A → Pod 1 (busy, 2s queue)
Request B → Pod 2 (idle, 0s queue)   ← should go here!
Request C → Pod 3 (busy, 1s queue)

Round-robin doesn't see the queue depth!
```

**Solution: Scheduler**
```
Scheduler checks:
Pod 1: Load=80%, Queue=5 requests  ← skip
Pod 2: Load=20%, Queue=0 requests  ← PICK THIS
Pod 3: Load=60%, Queue=2 requests  ← skip

Route to Pod 2 → Minimal latency!
```

### Problem 3: KV Cache Locality

**Without affinity:**
```
User sends message 1 → Pod A (builds KV)
User sends message 2 → Pod B (no KV, must rebuild! 💥)
User sends message 3 → Pod C (no KV, must rebuild! 💥)

Every follow-up pays prefill cost again!
```

**Solution: Session Affinity**
```
Scheduler remembers:
Session ABC123 → Pod A has the KV

User sends message 2 → Route to Pod A ✅
User sends message 3 → Route to Pod A ✅

Only first message pays prefill cost!
```

### Problem 4: Model Size Exceeds Single Host

**Large models don't fit on one machine:**
```
Llama-405B requires ~810 GB (FP16)
One H100 GPU: 80 GB
Need: 11+ GPUs minimum

But one host might only have 8 GPUs!
```

**Solution: Multi-Node**
```
Host 1: 8 GPUs (Part 1 of model)
   ↓
Host 2: 8 GPUs (Part 2 of model)

Pipeline parallelism distributes model across hosts
```

---

# Part II: Core Concepts

---

## Chapter 5: Understanding KServe

### What is KServe?

KServe is a Kubernetes-native model serving platform that provides:
- Standardized APIs for model inference
- Autoscaling (including scale-to-zero)
- Traffic management (canary, blue/green)
- Explainability and monitoring
- Support for multiple ML frameworks

**History:**
- Started as KFServing (part of Kubeflow)
- Rebranded to KServe in 2021
- Now a standalone CNCF project
- Used in production by many organizations

### KServe Architecture (High-Level)

```
┌─────────────────────────────────────────────────────┐
│                   KServe Platform                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐│
│  │ InferenceServ│  │ServingRuntime│  │LLMInferenc││
│  │ice (v1beta1) │  │  (v1beta1)   │  │eService   ││
│  │              │  │              │  │(v1alpha1) ││
│  └──────────────┘  └──────────────┘  └───────────┘│
│         ↓                 ↓                ↓        │
│  ┌──────────────────────────────────────────────┐  │
│  │        KServe Controller                     │  │
│  │  • Watches CRDs                              │  │
│  │  • Creates K8s resources                     │  │
│  │  • Manages lifecycle                         │  │
│  └──────────────────────────────────────────────┘  │
│         ↓                                           │
│  ┌──────────────────────────────────────────────┐  │
│  │     Kubernetes Resources                     │  │
│  │  • Deployments                               │  │
│  │  • Services                                  │  │
│  │  • Routes                                    │  │
│  │  • Autoscalers                               │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### KServe APIs

**1. InferenceService (v1beta1) - Stable, Production-Ready**
```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: my-model
spec:
  predictor:
    model:
      modelFormat:
        name: pytorch
      storageUri: s3://bucket/model
```

**Use for:**
- Traditional ML models
- Stable production workloads
- Multi-framework support (TF, PyTorch, ONNX, etc.)

**2. ServingRuntime (v1beta1) - Stable**
```yaml
apiVersion: serving.kserve.io/v1beta1
kind: ServingRuntime
metadata:
  name: vllm-runtime
spec:
  supportedModelFormats:
    - name: vllm
      version: "1"
  containers:
    - name: kserve-container
      image: vllm/vllm-openai:latest
```

**Use for:**
- Custom runtime configurations
- Template for multiple InferenceServices
- Production LLM serving (current ODH/RHOAI standard)

**3. LLMInferenceService (v1alpha1) - Alpha, Experimental**
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B
  prefill: {...}
  replicas: 4
  router:
    scheduler: {}
```

**Use for:**
- LLM-specific features
- Prefill/decode disaggregation
- Intelligent routing with scheduler
- **This is our focus in this book**

---

## Chapter 6: The llm-d Project

### What is llm-d?

llm-d (LLM Disaggregated) is an open-source, Kubernetes-native framework for high-performance distributed LLM inference. It's not a single product but a collection of:
- **Architecture patterns** (how to structure LLM serving)
- **Components** (scheduler, routing sidecar, model service)
- **Guides** (well-lit paths for common scenarios)
- **Helm charts** (for easy deployment)
- **Best practices** (from production deployments)

**Website:** https://llm-d.ai  
**GitHub:** https://github.com/llm-d/llm-d

### llm-d Philosophy

```
┌────────────────────────────────────────────────┐
│  "Well-Lit Paths" Philosophy                   │
├────────────────────────────────────────────────┤
│                                                │
│  Instead of giving you a black box:            │
│  • Show you tested patterns                    │
│  • Explain trade-offs                          │
│  • Provide benchmarks                          │
│  • Let you customize                           │
│                                                │
│  Goal: Fastest path to SOTA performance        │
└────────────────────────────────────────────────┘
```

### llm-d Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      llm-d Architecture                          │
└─────────────────────────────────────────────────────────────────┘

                         ┌─────────────┐
                         │   Client    │
                         └──────┬──────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Inference Gateway    │ ← Envoy-based
                    │  (Gateway API)        │
                    └───────┬───────────────┘
                            │
                            ▼
                    ┌───────────────────────┐
                    │  Inference Scheduler  │ ← Smart routing
                    │  (EPP)                │
                    └───────┬───────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │  Prefill Pods    │        │  Decode Pods     │
    │  (vLLM)          │        │  (vLLM + Sidecar)│
    └──────────────────┘        └──────────────────┘
```

### llm-d Components

**1. Inference Gateway (IGW)**
- Based on Kubernetes Gateway API
- Uses Envoy proxy
- Handles external requests
- Integrates with scheduler via ExtProc

**2. Inference Scheduler**
- Makes routing decisions
- Considers load, cache, priority
- Pluggable scoring algorithms
- Exposes metrics for monitoring

**3. Model Service (Helm Charts)**
- Deploys vLLM with best practices
- Supports disaggregation
- Configurable parallelism
- Easy customization

**4. Routing Sidecar**
- Sits next to decode pods
- Routes to prefill when needed
- Manages KV cache transfer
- Transparent to client

### llm-d Well-Lit Paths

llm-d provides three main paths:

**1. Intelligent Inference Scheduling**
```
Best for: Any production deployment
Benefit: Better latency, higher throughput
Components: Gateway + Scheduler + vLLM
```

**2. Prefill/Decode Disaggregation**
```
Best for: Long prompts, high throughput
Benefit: Better GPU utilization
Components: Gateway + Scheduler + Prefill + Decode + Sidecar
```

**3. Wide Expert Parallelism**
```
Best for: Large MoE models (DeepSeek, Mixtral)
Benefit: Scale out expert-parallel serving
Components: All of the above + EP configuration
```

### llm-d vs KServe LLMD

**llm-d (the project):**
- Broader scope (entire serving stack)
- Can be used standalone
- Helm charts for all components
- Supports multiple deployment tools

**KServe LLMD (the CRD):**
- Narrower scope (model deployment)
- Integrates with KServe ecosystem
- Single YAML for deployment
- Implements llm-d patterns

**Relationship:**
```
llm-d provides:     KServe LLMD uses:
┌──────────────┐    ┌──────────────┐
│ Architecture │ ──>│ Same patterns│
│ patterns     │    │              │
├──────────────┤    ├──────────────┤
│ Scheduler    │ ──>│ Same binary  │
│ binary       │    │              │
├──────────────┤    ├──────────────┤
│ Routing      │ ──>│ Same sidecar │
│ sidecar      │    │              │
├──────────────┤    ├──────────────┤
│ Helm charts  │    │ Similar      │
│              │    │ config       │
└──────────────┘    └──────────────┘

Different deployment methods, same underlying tech!
```

---

## Chapter 7: LLMD (LLMInferenceService) Deep Dive

### What is LLMD?

LLMD (LLMInferenceService) is a Kubernetes Custom Resource Definition (CRD) that lets you deploy LLMs with a single YAML file. It handles:
- Model downloading and caching
- Pod creation (prefill, decode, or both)
- Service and routing setup
- Optional scheduler deployment
- Multi-node coordination (via LeaderWorkerSet)

**API Group:** `serving.kserve.io/v1alpha1`  
**Kind:** `LLMInferenceService`  
**Short Name:** `llmisvc`

### LLMD Lifecycle

```
┌────────────────────────────────────────────────────────┐
│        You Create LLMInferenceService YAML             │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│      KServe Controller Watches API Server              │
│      Detects new LLMInferenceService                   │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│      Controller Reconciliation Loop                    │
│                                                         │
│  1. Load spec.baseRefs (config templates)              │
│  2. Merge configs (strategic merge patch)              │
│  3. Substitute template variables ({{.Name}}, etc.)    │
│  4. Determine deployment mode:                         │
│     • Simple (no prefill/worker)                       │
│     • Disaggregated (prefill specified)                │
│     • Multi-node (worker specified)                    │
│  5. Create workloads:                                  │
│     • Main Deployment or LeaderWorkerSet               │
│     • Prefill Deployment (if disaggregated)            │
│  6. Create services:                                   │
│     • Main service                                     │
│     • Prefill service (if disaggregated)               │
│     • Scheduler service (if enabled)                   │
│  7. Setup networking:                                  │
│     • Gateway (if specified)                           │
│     • HTTPRoute (if specified)                         │
│  8. Setup scheduler (if enabled):                      │
│     • Scheduler Deployment                             │
│     • InferencePool                                    │
│     • InferenceModel                                   │
│  9. Update status conditions                           │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│         Kubernetes Creates Resources                   │
│                                                         │
│  Deployments → ReplicaSets → Pods                      │
│  Services get endpoints                                │
│  HTTPRoute gets attached to Gateway                    │
│  InferencePool discovers pods                          │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│         Pods Start and Become Ready                    │
│                                                         │
│  Init containers run (storage-initializer)             │
│  Main containers start (vLLM)                          │
│  Sidecar containers run (routing-sidecar)              │
│  Readiness probes pass                                 │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│      Controller Updates Status: Ready=True             │
│      Your LLMInferenceService is LIVE!                 │
└────────────────────────────────────────────────────────┘
```

### LLMD CRD Structure

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm           # Your service name
  namespace: default     # K8s namespace
spec:
  # Model configuration
  model:
    uri: hf://org/model  # Where to get model
    name: model-name     # Model identifier
    criticality: Normal  # Priority level
    lora:                # Optional LoRA adapters
      adapters: []

  # Base configuration templates
  baseRefs:              # Inherit from configs
    - name: common-config

  # Main workload (decode in P/D mode)
  replicas: 4            # Number of pods
  parallelism:           # GPU distribution
    tensor: 2            # Tensor parallel size
    pipeline: 1          # Pipeline stages
    data: 1              # Data parallel
    expert: false        # Expert parallel (MoE)
  template:              # Pod template
    containers: []

  # Prefill workload (optional)
  prefill:               # Enables P/D disaggregation
    replicas: 2
    parallelism:
      tensor: 8
    template:
      containers: []

  # Multi-node worker (optional)
  worker:                # Enables multi-node
    containers: []

  # Networking and routing
  router:
    gateway:             # Gateway configuration
      refs: []           # Use existing Gateway
    route:               # HTTPRoute configuration
      http: {}           # Route rules
    ingress:             # Alternative to Gateway
      refs: []
    scheduler:           # Enable smart routing
      pool: {}           # InferencePool config
      template: {}       # Scheduler pod config

status:
  # Controller populates these
  conditions:
    - type: Ready
      status: "True"
    - type: HTTPRoutesReady
    - type: InferencePoolReady
    - type: MainWorkloadReady
    - type: PrefillWorkloadReady
    - type: SchedulerWorkloadReady
  url: https://gateway/ns/my-llm  # Service endpoint
```

### Deployment Modes

LLMD supports three deployment modes, automatically detected by the controller:

**Mode 1: Simple (Single-Node)**
```yaml
spec:
  replicas: 2
  template:
    containers: [...]
  # No prefill, no worker
```

**Created Resources:**
```
Deployment: my-llm-kserve (2 pods)
  └─ Each pod:
     ├─ Init: storage-initializer
     └─ Container: main (vLLM)

Service: my-llm-kserve-svc
HTTPRoute: my-llm-kserve-route (optional)
```

**Mode 2: Disaggregated (Prefill + Decode)**
```yaml
spec:
  prefill:              # ← Triggers P/D mode
    replicas: 2
    template: [...]
  replicas: 4           # Decode pods
  template: [...]
  router:
    scheduler: {}       # Recommended
```

**Created Resources:**
```
Deployment: my-llm-kserve-prefill (2 pods)
  └─ Each prefill pod:
     ├─ Init: storage-initializer
     └─ Container: main (vLLM prefill)

Deployment: my-llm-kserve (4 pods)
  └─ Each decode pod:
     ├─ Init: storage-initializer
     ├─ Init: llm-d-routing-sidecar (restartPolicy: Always)
     └─ Container: main (vLLM decode)

Service: my-llm-kserve-prefill-svc
Service: my-llm-kserve-svc
InferencePool: my-llm-inference-pool
Scheduler: my-llm-kserve-router-scheduler (1 pod)
HTTPRoute: my-llm-kserve-route
```

**Mode 3: Multi-Node (Leader + Workers)**
```yaml
spec:
  replicas: 2           # Number of leader/worker groups
  template: [...]       # Leader pod spec
  worker:               # ← Triggers multi-node
    containers: [...]   # Worker pod spec
  parallelism:
    pipeline: 4         # Usually with pipeline parallel
```

**Created Resources:**
```
LeaderWorkerSet: my-llm-kserve-mn (2 groups)
  ├─ Group 0:
  │  ├─ Leader: my-llm-kserve-mn-0
  │  │  ├─ Init: storage-initializer
  │  │  └─ Container: main (vLLM leader)
  │  └─ Worker: my-llm-kserve-mn-0-worker-1
  │     └─ Container: main (vLLM worker)
  │
  └─ Group 1:
     ├─ Leader: my-llm-kserve-mn-1
     └─ Worker: my-llm-kserve-mn-1-worker-1

Service: my-llm-kserve-svc (targets leaders)
HTTPRoute: my-llm-kserve-route
```

---

## Chapter 8: Prefill vs Decode Architecture

### The Motivation (Why Split?)

Imagine a restaurant with two types of tasks:
- **Food prep** (chopping vegetables): Can be done in parallel by many cooks
- **Plating and serving** (one dish at a time): Must be sequential

If the same cook does both, they're idle during slow tasks. Better to have:
- **Prep team:** Many hands, parallel work
- **Serving team:** Sequential work, but many servers handling different tables

This is exactly prefill vs decode!

### Prefill Deep Dive

**What happens during prefill:**

```
Input: "Once upon a time in a distant galaxy"
       (tokenized to 8 tokens)

Layer 0 (Embedding):
  Token 0: [embedding vector]
  Token 1: [embedding vector]
  ...all 8 tokens embedded in parallel

Layer 1 (Attention):
  For each token position:
    Compute Q (query)
    Compute K (key)    ← Stored in KV cache!
    Compute V (value)  ← Stored in KV cache!
    Compute attention scores with all previous tokens
  All 8 tokens process in parallel

Layer 2-79 (same process):
  ...repeat for all layers

Output Layer:
  Generate logits for position 8 (the "next" token)
  Sample: "there" ← First generated token
```

**Resource profile:**
```
┌─────────────────────────────────────┐
│  Prefill Resource Usage             │
├─────────────────────────────────────┤
│  Compute: ████████████████ 95%      │  Matrix multiplications
│  Memory BW: ████████░░░░░░ 60%      │  Reading model weights
│  VRAM: ███████████████░░░ 85%       │  Model + activations
│  Duration: 100-500ms                │  Fast!
└─────────────────────────────────────┘
```

**Why prefill loves GPUs:**
- Massive matrix operations (GEMM)
- Highly parallelizable across tokens
- Benefits from tensor cores
- More GPUs = faster prefill

### Decode Deep Dive

**What happens during decode:**

```
Input: KV cache (from prefill) + last token "there"

Layer 1 (Attention):
  Compute Q for new token only
  Load K, V from cache (don't recompute!) ← This is the win!
  Compute attention with all previous tokens' K/V
  Update cache with new K, V

Layers 2-79 (same):
  ...repeat for all layers

Output Layer:
  Generate logits for next token position
  Sample: "was" ← Next token

Repeat: Feed "was" back in, generate another token
        Continue until:
          • End-of-sequence token
          • Max length reached
          • User stops
```

**Resource profile:**
```
┌─────────────────────────────────────┐
│  Decode Resource Usage              │
├─────────────────────────────────────┤
│  Compute: ████░░░░░░░░░░░ 30%       │  Less computation
│  Memory BW: ██████████████ 90%      │  Reading KV cache!
│  VRAM: ███████████████████ 95%      │  KV cache grows
│  Duration per token: 30-100ms       │  Sequential
│  Total: 30-100ms × 200 = 6-20s      │  Long!
└─────────────────────────────────────┘
```

**Why decode is different:**
- Sequential (can't parallelize tokens)
- Memory-bound (reading KV cache)
- Lower compute intensity
- More replicas > more GPUs per replica

### The Disaggregation Pattern

```
┌───────────────────────────────────────────────────────┐
│  Traditional (Combined)                               │
├───────────────────────────────────────────────────────┤
│                                                       │
│  Pod with 8 GPUs:                                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │ [PREFILL] ████████████████ 95%  (100ms)         │ │
│  │ [DECODE]  ████░░░░░░░░░░░░ 30%  (10s)           │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  Problems:                                            │
│  • GPUs idle 70% of decode time                      │
│  • Can't scale prefill/decode independently          │
│  • One pod blocked during long decode                │
│  • Poor throughput                                   │
└───────────────────────────────────────────────────────┘

         ↓ ↓ ↓  DISAGGREGATE  ↓ ↓ ↓

┌───────────────────────────────────────────────────────┐
│  Disaggregated (Prefill + Decode Split)               │
├───────────────────────────────────────────────────────┤
│                                                       │
│  Prefill Pods (2 pods × 8 GPUs each):                │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Pod 1: [PREFILL] ████████████████ 95%           │ │
│  │ Pod 2: [PREFILL] ████████████████ 95%           │ │
│  └─────────────────────────────────────────────────┘ │
│  Optimized: High TP, batch multiple prompts         │
│                                                       │
│  Decode Pods (16 pods × 1 GPU each):                 │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Pod 1-16: [DECODE] ████░░░░░░░░░ 30% each       │ │
│  └─────────────────────────────────────────────────┘ │
│  Optimized: Many replicas, each serving tokens      │
│                                                       │
│  Total GPUs: Same (32), but better utilization!      │
│                                                       │
│  Benefits:                                            │
│  ✅ Prefill pods fully utilized                       │
│  ✅ Scale prefill and decode independently            │
│  ✅ More decode pods = more concurrent requests       │
│  ✅ 3-5x higher throughput in practice                │
└───────────────────────────────────────────────────────┘
```

### Request Flow in Disaggregated Mode

**First message in conversation:**

```
┌─────────────────────────────────────────────────────┐
│  Step 1: Client Request                             │
└─────────────────────────────────────────────────────┘
POST /v1/chat/completions
Body: {"messages": [{"role": "user", "content": "Hi"}]}

         ↓

┌─────────────────────────────────────────────────────┐
│  Step 2: Gateway + Scheduler                        │
└─────────────────────────────────────────────────────┘
Gateway asks Scheduler: "Which pod?"
Scheduler picks: decode-pod-7 (least loaded)

         ↓

┌─────────────────────────────────────────────────────┐
│  Step 3: Decode Pod (Routing Sidecar)               │
└─────────────────────────────────────────────────────┘
Routing sidecar receives request
Checks: "Do I have KV for this conversation?"
Answer: NO (first message)
Decision: Forward to PREFILL

         ↓

┌─────────────────────────────────────────────────────┐
│  Step 4: Prefill Pod                                │
└─────────────────────────────────────────────────────┘
Prefill pod:
  • Tokenizes "Hi"
  • Runs prefill (builds KV cache)
  • Generates first token: "Hello"
  • Returns: token + KV metadata

         ↓

┌─────────────────────────────────────────────────────┐
│  Step 5: Back to Decode Pod                         │
└─────────────────────────────────────────────────────┘
Routing sidecar:
  • Stores KV cache for session
  • Forwards to local vLLM decode (port 8001)

vLLM decode:
  • Generates token 2: "!"
  • Generates token 3: " How"
  • ... continues generating

         ↓

┌─────────────────────────────────────────────────────┐
│  Step 6: Stream to Client                           │
└─────────────────────────────────────────────────────┘
Response streams: "Hello! How can I help you today?"
```

**Follow-up message (same conversation):**

```
┌─────────────────────────────────────────────────────┐
│  Step 1: Client Request                             │
└─────────────────────────────────────────────────────┘
POST /v1/chat/completions
Body: {
  "messages": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How..."},
    {"role": "user", "content": "Tell me a joke"}
  ]
}

         ↓

┌─────────────────────────────────────────────────────┐
│  Step 2: Gateway + Scheduler                        │
└─────────────────────────────────────────────────────┘
Scheduler recognizes session ID
Routes to: decode-pod-7 (has the KV!)

         ↓

┌─────────────────────────────────────────────────────┐
│  Step 3: Decode Pod (Routing Sidecar)               │
└─────────────────────────────────────────────────────┘
Routing sidecar checks: "Do I have KV?"
Answer: YES!
Decision: Go directly to local decode
(NO prefill needed! ✅)

         ↓

┌─────────────────────────────────────────────────────┐
│  Step 4: Local vLLM Decode                          │
└─────────────────────────────────────────────────────┘
vLLM decode:
  • Loads KV from cache (first message + response)
  • Processes only NEW tokens: "Tell me a joke"
  • Generates response tokens

         ↓

┌─────────────────────────────────────────────────────┐
│  Step 5: Stream to Client                           │
└─────────────────────────────────────────────────────┘
Response streams: "Why did the chicken cross the road?..."

MUCH FASTER! No prefill overhead.
```

### When to Use Disaggregation

✅ **USE Disaggregated (Prefill/Decode)** when:
- Long input prompts (>512 tokens)
- High throughput requirements
- Production workloads
- Multi-turn conversations
- Need independent scaling
- GPU cost is a concern

❌ **USE Simple Mode** when:
- Development/testing
- Small models (<13B)
- Short prompts
- Low request rate
- Simplicity > optimization

---

*This is part 1 of the textbook. Due to length, I'll continue with remaining chapters...*


