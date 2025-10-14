# LLMD Prefill/Decode Disaggregated Serving Architecture

**Date:** October 12, 2025  
**Component:** LLMInferenceService (LLMD) v1alpha1  
**Feature:** Disaggregated Serving (Prefill/Decode Split)

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Why Disaggregated Serving?](#why-disaggregated-serving)
3. [Architecture Diagrams](#architecture-diagrams)
4. [Components Explained](#components-explained)
5. [Request Flow](#request-flow)
6. [Configuration Examples](#configuration-examples)
7. [Scheduler & Routing](#scheduler--routing)
8. [Comparison: Standard vs Disaggregated](#comparison-standard-vs-disaggregated)

---

## Overview

**Disaggregated Serving** (also called **Prefill/Decode** or **P/D** split) is an advanced architecture pattern for LLM inference that separates the two distinct phases of LLM processing into independent deployments:

1. **Prefill Phase** - Processes the input prompt and generates KV cache
2. **Decode Phase** - Generates output tokens one at a time using the KV cache

This architecture, inspired by **llm-d** (LLM disaggregated), allows for:
- **Independent scaling** of prefill and decode workloads
- **Different hardware allocation** (e.g., more GPUs for prefill, fewer for decode)
- **Better resource utilization** (prefill is compute-intensive, decode is memory-intensive)
- **Higher throughput** for long-context scenarios

---

## Why Disaggregated Serving?

### LLM Inference Has Two Distinct Phases

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM INFERENCE PHASES                         │
└─────────────────────────────────────────────────────────────────┘

Phase 1: PREFILL (Prompt Processing)
┌──────────────────────────────────────────┐
│  Input: "Write a story about a robot"    │
│  Process: All tokens processed in        │
│           PARALLEL (matrix operations)   │
│  Output: KV cache for all prompt tokens  │
│  Characteristics:                        │
│    ⚡ Compute-intensive (high FLOPS)      │
│    📊 Batch-friendly                      │
│    ⏱️  Short duration                    │
│    🎯 Benefits from more GPUs             │
└──────────────────────────────────────────┘
                    ↓
Phase 2: DECODE (Token Generation)
┌──────────────────────────────────────────┐
│  Input: KV cache from prefill            │
│  Process: Generate tokens one at a time  │
│           (SEQUENTIAL, autoregressive)   │
│  Output: "Once upon a time, there was    │
│          a robot named Alex who..."      │
│  Characteristics:                        │
│    🧠 Memory-intensive (KV cache)         │
│    🐌 Sequential (can't parallelize)      │
│    ⏳ Long duration (100s of steps)       │
│    💾 Needs KV cache storage              │
└──────────────────────────────────────────┘
```

### Problem with Traditional Serving

In traditional (non-disaggregated) serving, both phases run on the **same deployment**:

```
❌ TRADITIONAL SERVING (Inefficient)

┌────────────────────────────────────────────────┐
│  Single vLLM Deployment (4 GPUs)               │
│                                                │
│  Request 1: [PREFILL ⚡⚡⚡⚡]                     │
│             [DECODE 💤........................] │
│             (3 GPUs idle during decode!)       │
│                                                │
│  Request 2: [wait...] [PREFILL ⚡⚡⚡⚡]           │
│             [DECODE 💤........................] │
└────────────────────────────────────────────────┘

Problems:
  - GPUs idle during sequential decode phase
  - Can't scale prefill and decode independently
  - Resource contention between phases
  - Lower overall throughput
```

### Solution: Disaggregated Serving

Split prefill and decode into **separate deployments**:

```
✅ DISAGGREGATED SERVING (Efficient)

┌────────────────────────────┐  ┌────────────────────────────┐
│  Prefill Deployment                                        │
│  (8 GPUs, 2 replicas)                                      │
│                                                            │
│  Req 1: [PREFILL ⚡⚡⚡⚡]                                     │
│  Req 2: [PREFILL ⚡⚡⚡⚡]                                     │
│  Req 3: [PREFILL ⚡⚡⚡⚡]                                     │
│  Req 4: [PREFILL ⚡⚡⚡⚡]                                     │
└────────────────────────────┘  └────────────────────────────┘
         ↑                              ↑
     High GPU count              Fewer GPUs, more replicas
     Parallel batching            Memory for KV cache

Benefits:
  ✅ All GPUs fully utilized
  ✅ Independent scaling
  ✅ Higher throughput
  ✅ Better cost efficiency
```

---

## Architecture Diagrams

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                      LLMInferenceService (LLMD)                       │
└───────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                         Controller creates
                         Deployments/Routes
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────────┐
│                          CREATED RESOURCES                            │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────┐   ┌───────────────────────────────┐
│     Prefill Deployment        │   │        Decode Deployment       │
│     (<name>-kserve-prefill)   │   │        (<name>-kserve)         │
├───────────────────────────────┤   ├───────────────────────────────┤
│ Pod: Prefill (vLLM, :8000)    │   │ Pod: Routing Sidecar (:8000)  │
│ Service: *-prefill-svc        │   │      → vLLM Decode (:8001)    │
│                                │   │ Service: *-workload-svc       │
└───────────────────────────────┘   └───────────────────────────────┘
```

### Detailed Pod Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         PREFILL POD                                    │
│  Name: my-llm-kserve-prefill-xxxxx                                     │
│  Labels: llm-d.ai/role=prefill                                         │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  Container: main (vLLM Prefill)                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│  │  Volumes:                                                        │ │
│  │    /home           -> emptyDir                                   │ │
│  │    /dev/shm        -> emptyDir (Memory, 1Gi)                     │ │
│  │    /models         -> emptyDir (model cache)                     │ │
│  │    /etc/ssl/certs  -> Secret (TLS certs)                         │ │
│  │                                                                  │ │
│  │  Health Checks:                                                  │ │
│  │    Liveness:  GET https://localhost:8000/health                  │ │
│  │    Readiness: GET https://localhost:8000/health                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└────────────────────────────────────────────────────────────────────────┘


┌────────────────────────────────────────────────────────────────────────┐
│                         DECODE POD                                     │
│  Name: my-llm-kserve-workload-xxxxx                                    │
│  Labels: llm-d.ai/role=decode                                          │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  InitContainer: llm-d-routing-sidecar (restartPolicy: Always)          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│  │    --cert-path=/etc/ssl/certs                                    │ │
│  │    --decoder-use-tls=true       # Decode pods use TLS            │ │
│  │    --prefiller-use-tls=true     # Prefill pods use TLS           │ │
│  │    --enable-ssrf-protection=true                                 │ │
│  │                                                                  │ │
│  │  Environment:                                                    │ │
│  │    INFERENCE_POOL_NAMESPACE=<namespace>                          │ │
│  │                                                                  │ │
│  │  Routing Logic:                                                  │ │
│  │    1. Receive request on :8000                                   │ │
│  │    2. Check if first request (prefill needed)                    │ │
│  │       -> YES: Forward to prefill pod                             │ │
│  │       -> NO:  Forward to local decode (:8001)                    │ │
│  │    3. Manage KV cache transfer                                   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  Container: main (vLLM Decode)                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│                                                                       │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Components Explained

### 1. Prefill Deployment

**Purpose:** Process input prompts and generate KV cache

**Characteristics:**
- Separate Kubernetes Deployment: `<llmisvc-name>-kserve-prefill`
- Label: `llm-d.ai/role=prefill`
- Listens on port **8000**
- No routing sidecar (direct vLLM access)
- Can be scaled independently based on prefill load

**Configuration:**
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm
spec:
  prefill:                    # ← Defines prefill workload
    replicas: 2               # Scale prefill independently
    parallelism:
      tensor: 4               # More GPUs for parallel processing
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        command: ["vllm", "serve", "..."]
        # Prefill-specific vLLM args
```

### 2. Decode Deployment

**Purpose:** Generate output tokens using KV cache from prefill

**Characteristics:**
- Main Kubernetes Deployment: `<llmisvc-name>-kserve-workload`
- Label: `llm-d.ai/role=decode`
- **Two containers:**
  1. **Routing Sidecar** (InitContainer with `restartPolicy: Always`)
     - Listens on port **8000** (external)
     - Routes requests to prefill or local decode
  2. **vLLM Decode** (Main container)
     - Listens on port **8001** (internal)
     - Only accessed via routing sidecar
- Can be scaled independently based on decode load

**Configuration:**
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm
spec:
  # WorkloadSpec at top level = decode configuration
  replicas: 4                 # More replicas for decode
  parallelism:
    tensor: 1                 # Fewer GPUs per decode pod
  template:
    # Decode pod spec (with routing sidecar injected automatically)
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      command: ["vllm", "serve"]
```

### 3. Routing Sidecar

**Purpose:** Intelligent request routing for disaggregated serving

**Key Responsibilities:**

```
┌───────────────────────────────────────────────────────┐
│           ROUTING SIDECAR DECISION LOGIC              │
└───────────────────────────────────────────────────────┘

Incoming Request
      ↓
┌─────────────────────────────────────┐
│ Is this a NEW conversation?         │
│ (first request, no KV cache)        │
└──────────┬─────────────────┬────────┘
│                                     │
          YES               NO
           ↓                 ↓
  ┌────────────────┐  ┌─────────────────┐
│ PREFILL Route                       │
│                                     │
│ 1. Forward to                       │
│    prefill pod                      │
│ 2. Get KV                           │
│    cache                            │
│ 3. Store KV                         │
│ 4. Return                           │
│    response                         │
└─────────────────────────────────────┘
```

**Implementation:**
- Runs as InitContainer with `restartPolicy: Always` (acts like sidecar)
- Uses TLS for secure communication
- Discovers prefill pods via InferencePool
- Manages KV cache transfer between prefill and decode

### 4. Endpoint Picker (EPP) / Scheduler

**Purpose:** Intelligent endpoint selection for load balancing

**Architecture:**

```
┌────────────────────────────────────────────────────────────┐
│                  ENDPOINT PICKER (EPP)                     │
│                  Scheduler Deployment                      │
│  Name: <llmisvc-name>-epp                                  │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Configuration: EndpointPickerConfig                       │
│  ┌──────────────────────────────────────────────────────┐  │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  Scheduling Profiles:                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Scoring Logic:**

```
For Prefill Requests:
  Score = (2.0 × Prefix_Cache_Score) + (1.0 × Load_Aware_Score)
  
  Where:
    - Prefix_Cache_Score: Higher if pod has matching prefix cache
    - Load_Aware_Score: Higher if pod has lower current load
  
  Result: Select prefill pod with best score

For Decode Requests:
  Score = (2.0 × Prefix_Cache_Score) + (1.0 × Load_Aware_Score)
  
  Where:
    - Prefix_Cache_Score: Matches KV cache from prefill
    - Load_Aware_Score: Current decode load
  
  Result: Select decode pod with best score
```

### 5. InferencePool

**Purpose:** Discovery mechanism for prefill and decode pods

```yaml
apiVersion: inference.networking.x-k8s.io/v1alpha2
kind: InferencePool
metadata:
  name: my-llm-inference-pool
spec:
  # Prefill targets
  targets:
  - name: prefill
    selector:
      matchLabels:
        llm-d.ai/role: prefill
        serving.kserve.io/inferenceservice: my-llm
    port: 8000
    
  # Decode targets
  - name: decode
    selector:
      matchLabels:
        llm-d.ai/role: decode
        serving.kserve.io/inferenceservice: my-llm
    port: 8000
```

---

## Request Flow

### Complete Request Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    CLIENT REQUEST FLOW                                   │
└──────────────────────────────────────────────────────────────────────────┘

USER
  │
  │ 1. POST /v1/chat/completions
  │    Body: {"model": "my-llm", "messages": [...]}
  ▼
┌─────────────────────────────┐
│  Gateway / HTTPRoute        │
│  (Public endpoint :80)      │
└──────────┬──────────────────┘
           │
           │ 2. Route to Endpoint Picker (EPP)
           │    for scheduling decision
           ▼
┌─────────────────────────────┐
│  Endpoint Picker (EPP)      │
│  Scheduler                  │
└──────────┬──────────────────┘
           │
           │ 3. EPP analyzes request:
           │    - Is this prefill or decode?
           │    - What pods are available?
           │    - What's the load on each pod?
           │    - Any matching cache?
           │
           │ Decision: Route to DECODE pod
           │           (routing sidecar decides prefill vs decode)
           ▼
┌─────────────────────────────┐
│  Decode Pod                 │
│  ┌───────────────────────┐  │
│                             │
│                             │
│  └───────┬───────────────┘  │
│                             │
│                             │
│                             │
│                             │
│                             │
│          ▼
│  ┌──────────────────────────────────────────────────────┐
│                                                         │
│                                                         │
│                                                         │
│                                                         │
│                                                         │
│  └──────────────────────────────────────────────────────┘
│                                                         │
│                                                         │
│      5a. Local Decode  5b. Forward to Prefill
│          ↓                  ↓
│  ┌───────────────────┐  ┌─────────────────────────────┐
│                                                       │
│                                                       │
│                                                       │
│                                                       │
│                                                       │
│  └───────────────────┘                                │
│                                                       │
│                                                       │
│ └─────────┬───────────────┘                           │
│                                                         │
│ 7. Return KV cache +                                    │
│    first token                                          │
                            └───────────┬─────────────────┘
                                        │
        ┌───────────────────────────────┘
        │
        │ 8. Routing Sidecar stores KV cache
        │    for subsequent decode requests
        ▼
┌─────────────────────────────┐
│  Routing Sidecar            │
│  :8000                      │
│                             │
│  9. For subsequent tokens:  │
│     Forward to local decode │
│     (:8001) with KV cache   │
└──────────┬──────────────────┘
           │
           │ 10. Stream tokens back to client
           ▼
        USER
  "Once upon a time..."
```

### Step-by-Step Flow

#### Initial Request (Prefill Required)

```
Step 1: Client → Gateway
  POST https://my-llm.example.com/v1/chat/completions
  Body: {
    "model": "my-llm",
    "messages": [{"role": "user", "content": "Write a story"}]
  }

Step 2: Gateway → Endpoint Picker (EPP)
  EPP analyzes:
    - Request type: Chat completion
    - Session: NEW (no KV cache)
    - Profile: Use "prefill" or "decode"?
    - Available pods: List from InferencePool
  
  EPP decides:
    Route to: decode-pod-1 (routing sidecar will handle prefill)

Step 3: Gateway → Decode Pod (Routing Sidecar :8000)
  Request arrives at routing sidecar

Step 4: Routing Sidecar Decision
  Check: Is KV cache available for this conversation?
    - NO (first request)
  
  Action: Forward to PREFILL pod

Step 5: Routing Sidecar → Prefill Pod
  POST https://prefill-pod-1:8000/v1/chat/completions
  Body: Same as original request

Step 6: Prefill Pod Processes
  vLLM prefill phase:
    1. Tokenize: "Write a story" → [token_ids]
    2. Forward pass: Process all tokens in parallel
    3. Generate: KV cache for all prompt tokens
    4. Output: First token + KV cache metadata

Step 7: Prefill Pod → Routing Sidecar
  Response: {
    "choices": [{
      "delta": {"content": "Once"},
      "kv_cache_metadata": {...}
    }]
  }

Step 8: Routing Sidecar Stores KV Cache
  Cache stored for conversation_id
  Subsequent requests will use this cache

Step 9: Routing Sidecar → Local Decode (:8001)
  For remaining tokens:
    1. Pass KV cache to local vLLM decode
    2. vLLM generates: " upon" (next token)
    3. vLLM generates: " a" (next token)
    4. ... continues until done

Step 10: Routing Sidecar → Gateway → Client
  Stream response:
    data: {"choices": [{"delta": {"content": "Once"}}]}
    data: {"choices": [{"delta": {"content": " upon"}}]}
    data: {"choices": [{"delta": {"content": " a"}}]}
    ...
```

#### Subsequent Requests (Decode Only)

```
Step 1: Client → Gateway
  POST https://my-llm.example.com/v1/chat/completions
  Body: {
    "model": "my-llm",
    "messages": [
      {"role": "user", "content": "Write a story"},
      {"role": "assistant", "content": "Once upon a time..."},
      {"role": "user", "content": "Continue"}  ← NEW message
    ]
  }

Steps 2-3: Same as before (Gateway → EPP → Decode Pod)

Step 4: Routing Sidecar Decision
  Check: Is KV cache available?
    - YES (from previous request)
  
  Action: Forward to LOCAL DECODE

Step 5: Routing Sidecar → Local vLLM Decode (:8001)
  Request with KV cache attached
  
Step 6: Local vLLM Decode
  1. Load existing KV cache
  2. Process only NEW tokens ("Continue")
  3. Generate response tokens
  
Steps 7-8: Stream response back to client
```

---

## Configuration Examples

### Example 1: Basic Disaggregated Serving

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama2-7b-disaggregated
  namespace: llm-serving
spec:
  model:
    uri: hf://meta-llama/Llama-2-7b-chat-hf
    name: llama2-7b
  
  # Prefill configuration
  prefill:
    replicas: 2                    # 2 prefill pods
    parallelism:
      tensor: 2                    # 2 GPUs per prefill pod
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "2"
          limits:
            nvidia.com/gpu: "2"
  
  # Decode configuration (top-level WorkloadSpec)
  replicas: 4                      # 4 decode pods
  parallelism:
    tensor: 1                      # 1 GPU per decode pod
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          nvidia.com/gpu: "1"
        limits:
          nvidia.com/gpu: "1"
  
  # Router configuration
  router:
    route:
      http: {}                     # Create HTTPRoute
    gateway:
      refs:
      - name: my-gateway
        namespace: istio-system
    scheduler:                     # Enable EPP scheduler
      pool: {}                     # Create InferencePool
```

**Resources Created:**
- 2 Prefill pods (2 GPUs each = 4 GPUs total for prefill)
- 4 Decode pods (1 GPU each = 4 GPUs total for decode)
- Total: 8 GPUs
- 1 Endpoint Picker (EPP) deployment
- 1 InferencePool
- 1 HTTPRoute
- Services for prefill and decode

### Example 2: With LLMInferenceServiceConfig

```yaml
---
# Base config for prefill
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: standard-prefill-config
  namespace: llm-serving
spec:
  prefill:
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        command: ["vllm", "serve", "{{ .Spec.Model.Name }}"]
        args:
          - --served-model-name={{ .Spec.Model.Name }}
          - --port=8000
          - --dtype=float16
        env:
          - name: VLLM_LOGGING_LEVEL
            value: INFO

---
# Base config for decode
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: standard-decode-config
  namespace: llm-serving
spec:
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      command: ["vllm", "serve"]
      args:
        - --served-model-name={{ .Spec.Model.Name }}
        - --port=8001
        - --dtype=float16

---
# LLMInferenceService using configs
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: granite-8b-pd
  namespace: llm-serving
spec:
  baseRefs:
    - name: standard-prefill-config
    - name: standard-decode-config
  
  model:
    uri: hf://ibm-granite/granite-8b-code-instruct
    name: granite-8b
  
  prefill:
    replicas: 3
    parallelism:
      tensor: 4
  
  replicas: 6
  parallelism:
    tensor: 1
  
  router:
    route:
      http: {}
    scheduler:
      pool: {}
```

### Example 3: Multi-Node Disaggregated (Advanced)

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama2-70b-multinode-pd
spec:
  model:
    uri: hf://meta-llama/Llama-2-70b-chat-hf
    name: llama2-70b
  
  # Prefill: Multi-node with pipeline parallelism
  prefill:
    replicas: 1                    # 1 multi-node prefill cluster
    parallelism:
      tensor: 4                    # 4-way tensor parallelism
      pipeline: 2                  # 2-way pipeline parallelism
    template:                      # Head node
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "4"
    worker:                        # Worker nodes
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "4"
  
  # Decode: Standard single-node pods
  replicas: 8
  parallelism:
    tensor: 2
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          nvidia.com/gpu: "2"
  
  router:
    scheduler:
      pool: {}
```

---

## Scheduler & Routing

### Endpoint Picker Config (for Disaggregated P/D)

```yaml
apiVersion: inference.networking.x-k8s.io/v1alpha1
kind: EndpointPickerConfig
plugins:
  - type: pd-profile-handler         # Detects if request needs prefill or decode
    parameters:
      threshold: 100
  - type: prefill-header-handler     # Extracts prefill-specific headers
  - type: prefill-filter             # Filters to only prefill pods
  - type: decode-filter              # Filters to only decode pods
  - type: prefix-cache-scorer        # Scores based on prefix cache match
  - type: load-aware-scorer          # Scores based on current load
  - type: max-score-picker           # Selects pod with highest score

schedulingProfiles:
  - name: prefill
    plugins:
      - pluginRef: prefill-filter
      - pluginRef: prefix-cache-scorer
        weight: 2.0                  # Cache match is important
      - pluginRef: load-aware-scorer
        weight: 1.0
      - pluginRef: max-score-picker
  
  - name: decode
    plugins:
      - pluginRef: decode-filter
      - pluginRef: prefix-cache-scorer
        weight: 2.0                  # KV cache affinity
      - pluginRef: load-aware-scorer
        weight: 1.0
      - pluginRef: max-score-picker
```

---

## Comparison: Standard vs Disaggregated

### Standard Serving

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama2-standard
spec:
  model:
    uri: hf://meta-llama/Llama-2-7b-chat-hf
  
  replicas: 4
  parallelism:
    tensor: 2
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:latest
      resources:
        requests:
          nvidia.com/gpu: "2"
```

**Characteristics:**
- ✅ Simple configuration
- ✅ No routing sidecar needed
- ❌ Can't scale prefill/decode independently
- ❌ GPUs idle during decode phase
- ❌ Lower throughput for long contexts

### Disaggregated Serving

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama2-disaggregated
spec:
  model:
    uri: hf://meta-llama/Llama-2-7b-chat-hf
  
  prefill:                         # Separate prefill deployment
    replicas: 2
    parallelism:
      tensor: 4
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "4"
  
  replicas: 6                      # Separate decode deployment
  parallelism:
    tensor: 1
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          nvidia.com/gpu: "1"
  
  router:
    scheduler:
      pool: {}
```

**Characteristics:**
- ✅ Independent scaling
- ✅ Better GPU utilization
- ✅ Higher throughput for production
- ✅ Optimized resource allocation
- ❌ More complex configuration
- ❌ Requires routing sidecar
- ❌ Additional latency for KV cache transfer

---

## Summary

### When to Use Disaggregated Serving

✅ **USE Disaggregated** when:
- High throughput requirements
- Long input contexts (many prefill tokens)
- Production deployments
- Need independent scaling
- GPU utilization is critical
- Multiple concurrent users

❌ **USE Standard** when:
- Development/testing
- Low traffic
- Simple use cases
- Short contexts
- Single user scenarios
- Simplicity is preferred

### Key Benefits

1. **Independent Scaling**
   - Scale prefill based on new request rate
   - Scale decode based on active conversations

2. **Better Resource Utilization**
   - More GPUs for compute-intensive prefill
   - Fewer GPUs, more replicas for memory-intensive decode

3. **Higher Throughput**
   - Parallel prefill processing
   - Continuous decode without waiting for prefill

4. **Cost Optimization**
   - Right-size GPU allocation
   - Reduce idle GPU time

---

## 🔗 References

- **llm-d Project:** https://github.com/llm-d/llm-d
- **KServe LLMD API:** `pkg/apis/serving/v1alpha1/llm_inference_service_types.go`
- **Controller:** `pkg/controller/v1alpha1/llmisvc/`
- **Config Templates:** `config/llmisvc/config-llm-{prefill,decode}-template.yaml`
- **Inference Gateway:** https://github.com/kubernetes-sigs/gateway-api-inference-extension

---

**Document Version:** 1.0  
**Last Updated:** October 12, 2025

