# LLMD (LLMInferenceService) - Complete Architecture & Features Guide

**Document Version:** 1.0  
**Date:** October 13, 2025  
**Source:** KServe v1alpha1 API  
**CRDs:** `LLMInferenceService`, `LLMInferenceServiceConfig`

---

## 📖 Table of Contents

1. [What is LLMD?](#what-is-llmd)
2. [Full Architecture Overview](#full-architecture-overview)
3. [Complete Feature List](#complete-feature-list)
4. [Feature-by-Feature Deep Dive](#feature-by-feature-deep-dive)
5. [Container Structure for Each Feature](#container-structure-for-each-feature)
6. [Request Flow for Each Feature](#request-flow-for-each-feature)
7. [Real-World Deployment Examples](#real-world-deployment-examples)

---

## What is LLMD?

### Definition

**LLMD** (LLM Inference Service) is a Kubernetes Custom Resource Definition (CRD) in KServe v1alpha1 specifically designed for deploying and managing Large Language Models at scale.

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService        # Main CRD
kind: LLMInferenceServiceConfig  # Config template CRD
```

### Key Characteristics

| Aspect | Details |
|--------|---------|
| **API Version** | `serving.kserve.io/v1alpha1` (Alpha - experimental) |
| **Purpose** | LLM-specific deployments with advanced features |
| **Kubernetes Resources** | Creates: Deployments, Services, HTTPRoutes, InferencePool, etc. |
| **Controller** | `LLMISVCReconciler` in `/pkg/controller/v1alpha1/llmisvc/` |
| **Short Name** | `llmisvc` (e.g., `kubectl get llmisvc`) |

### Architecture Philosophy

LLMD follows the **llm-d** (LLM Disaggregated) architecture pattern:
- **Disaggregate** workloads (prefill vs decode)
- **Independent scaling** of components
- **Intelligent routing** with scheduler (EPP)
- **Template-based** configuration inheritance

---

## LLM Inference Phases (Baseline, without LLMD)

### High-level Phases
```
USER PROMPT → [Tokenization] → [Prefill (build KV cache)] → [Decode Loop]
                                   │                           │
                                   ▼                           ▼
                             KV cache in GPU             Sampling, logits,
                             memory for each token       streaming tokens
```

### Step-by-step (Single Pod, Single Container)
```
┌──────────────────────────────────────────────────────────────┐
│                 BASELINE (No Disaggregation)                  │
└──────────────────────────────────────────────────────────────┘

1) Tokenization
   • Convert input text → token IDs

2) Prefill (a.k.a. prompt processing)
   • Run full model over all prompt tokens
   • Build KV cache (keys/values) layer-by-layer
   • Produce first output token logits

3) Decode loop (auto-regressive generation)
   • For each new token:
     - Look up/use KV cache
     - Run model for 1 token step
     - Sample next token (top-p/top-k/temperature)
     - Stream token to client
```

### Observations (Baseline)
- **Prefill** is compute- and bandwidth-heavy but parallel across tokens.
- **Decode** is sequential and memory-bound; KV cache dominates memory.
- Single process does both phases; limited control over scaling/cost.

---

## How LLMD Changes the Phases (Phase-by-Phase)

### High-level Changes
```
USER PROMPT → Gateway → Scheduler (EPP) → Decode Pod (sidecar) →
  ├─ new conversation? YES → Prefill Pod (parallel, fast) → first token + KV →
  └─ NO → reuse KV
Decode Pod (local vLLM) → stream tokens → client
```

### What Changes
- **Routing**: Requests enter via Gateway; Scheduler picks the best pod.
- **Disaggregation**: Prefill and Decode run on different pods (optional).
- **KV Mobility**: KV cache (or metadata) is transferred/attached across pods.
- **Parallelism Tuning**: Prefill prefers high TP (e.g., TP=8); Decode prefers smaller TP and more replicas.

### Step-by-step (Disaggregated)
```
┌──────────────────────────────────────────────────────────────┐
│                    LLMD DISAGGREGATED FLOW                   │
└──────────────────────────────────────────────────────────────┘

1) Gateway → Scheduler (EPP)
   • Chooses decode pod based on load, KV locality, criticality

2) Decode Pod (Routing Sidecar)
   • New conversation?
     - YES → Forward to Prefill Pod
     - NO  → Call local vLLM decode directly with existing KV

3) Prefill Pod (when needed)
   • Process full prompt in parallel (high TP)
   • Return first token + KV metadata

4) Decode Pod (local vLLM)
   • Attach KV
   • Generate sequential tokens; stream to client
```

---

## Full Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LLMD FULL ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL                                   │
│                     (User/Application)                              │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GATEWAY (Envoy)                              │
│                    (Istio / Gateway API)                            │
│                                                                     │
│  • HTTPRoute: Routes to InferencePool                              │
│  • Path: /<namespace>/<llmisvc-name>                               │
└────────────┬────────────────────────────────────────────────────────┘
             │
             │ ExtProc (External Processing)
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   SCHEDULER (EPP - Endpoint Picker)                             │
│                                                                                 │
│  Role: Select optimal pod for request                                           │
│  Component: llm-d-inference-scheduler                                           │
│  Deployment: <llmisvc-name>-kserve-router-scheduler                             │
│                                                                                 │
│  Decision Factors:                                                              │
│  • Pod load                                                                     │
│  • KV cache availability                                                        │
│  • Model criticality                                                            │
│  • Prefix cache match                                                           │
└────────────┬────────────────────────────────────────────────────────┘
             │
             │ Selects pod from InferencePool
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       INFERENCE POOL                                            │
│              (Service Discovery for Model Pods)                                 │
│                                                                                 │
│  Resource: InferencePool (Gateway API Extension)                                │
│  Selector: Labels (llm-d.ai/role=prefill or decode)                             │
│  Pools: Prefill pods + Decode pods                                              │
└─────────────────────────────────────────────────────────────────────┘
             │
             ├──────────────┬──────────────────────┐
             ▼              ▼                      ▼
    ┌────────────┐  ┌────────────┐        ┌────────────┐
    │  PREFILL     │  │  PREFILL     │        │   DECODE      │
    │   POD 1      │  │   POD 2      │        │   POD 1       │
    └────────────┘  └────────────┘        └────────────┘

POD CONTAINER STRUCTURES:

SINGLE NODE MODE:
┌───────────────────────────────┐
│           Main Pod                  │
│                                     │
│  Containers:                        │
│  • vLLM (main)                      │
│                                     │
│  Ports: 8000                        │
│  Label: role=both or decode         │
└───────────────────────────────┘

DISAGGREGATED MODE (Decode Pod):        
┌───────────────────────────────────────────┐
│               Decode Pod                          │
│                                                   │
│  Containers:                                      │
│  • storage-initializer (init)                     │
│  • llm-d-routing-sidecar (init, Always)           │
│  • vLLM (main)                                    │
│                                                   │
│  Ports: 8000 (external), 8001 (internal)          │
│  Label: role=decode                               │
└───────────────────────────────────────────┘

DISAGGREGATED MODE (Prefill Pod):
┌───────────────────────────────────────────┐
│               Prefill Pod                         │
│                                                   │
│  Containers:                                      │
│  • storage-initializer (init)                     │
│  • vLLM (main)                                    │
│                                                   │
│  Port: 8000                                       │
│  Label: role=prefill                              │
└───────────────────────────────────────────┘

MULTI-NODE MODE (with LeaderWorkerSet):
┌─────────────────────────────────────────────────────────────────────┐
│                      LeaderWorkerSet (LWS)                                      │
│                                                                                 │
│  Group:                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐   │
│  │ Leader (rank 0)     │    │ Worker (rank 1)     │    │ Worker (rank 2)   │   │
│  │ • storage-init      │    │ • vLLM              │    │ • vLLM            │   │
│  │ • vLLM              │    │                     │    │                   │   │
│  └──────────────────┘    └──────────────────┘    └────────────────┘   │
│                                                                                 │
│  Discovery: LWS controller wires pods together                                  │
│  Parallelism: Pipeline/Data across leader + workers                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Controller Reconciliation Flow

```
User Creates LLMInferenceService
         │
         ▼
┌─────────────────────────────────────────────┐
│   LLMISVC Controller Reconciliation Loop            │
└─────────────────────────────────────────────┘
         │
         ├─► 1. Load & Merge Base Configs (baseRefs)
         │       └─► Combine multiple configs
         │       └─► Apply strategic merge
         │       └─► Substitute template variables
         │
         ├─► 2. Determine Deployment Mode
         │       ├─► Single Node (no prefill, no worker)
         │       ├─► Disaggregated (prefill specified)
         │       └─► Multi-Node (worker specified)
         │
         ├─► 3. Create Workloads
         │       ├─► Main Deployment/LWS
         │       ├─► Prefill Deployment (if disaggregated)
         │       └─► Worker Pods (if multi-node)
         │
         ├─► 4. Create Services
         │       ├─► Main Service
         │       ├─► Prefill Service (if disaggregated)
         │       └─► Scheduler Service (if scheduler enabled)
         │
         ├─► 5. Setup Networking
         │       ├─► HTTPRoute (Gateway API)
         │       ├─► Gateway (or use existing)
         │       └─► Ingress (alternative)
         │
         ├─► 6. Setup Scheduler (if enabled)
         │       ├─► Scheduler Deployment (EPP)
         │       ├─► InferencePool
         │       └─► InferenceModel
         │
         └─► 7. Update Status
                 ├─► HTTPRoutesReady
                 ├─► InferencePoolReady
                 ├─► MainWorkloadReady
                 ├─► PrefillWorkloadReady (if applicable)
                 ├─► RouterReady
                 ├─► SchedulerWorkloadReady (if applicable)
                 └─► Ready (overall)
```

---

## Complete Feature List

### Core Features

| # | Feature | Category | Status | Description |
|---|---------|----------|--------|-------------|
| 1 | **Model Specification** | Core | Stable | Define model URI, name, LoRA adapters |
| 2 | **Replicas** | Core | Stable | Scale inference pods horizontally |
| 3 | **Pod Template** | Core | Stable | Kubernetes PodSpec for containers |
| 4 | **BaseRefs** | Config | ⚠️ Buggy | Inherit from LLMInferenceServiceConfig |
| 5 | **Template Variables** | Config | ⚠️ Buggy | Dynamic substitution ({{.Name}}, etc.) |
| 6 | **Prefill/Decode Split** | Architecture | Stable | Disaggregated serving |
| 7 | **Parallelism** | Scaling | Stable | Tensor, Pipeline, Data, Expert |
| 8 | **Multi-Node (Worker)** | Scaling | Stable | Distributed deployment with LeaderWorkerSet |
| 9 | **Gateway API (HTTPRoute)** | Networking | Stable | Modern routing with Gateway API |
| 10 | **Gateway** | Networking | Stable | Kubernetes Gateway |
| 11 | **Ingress** | Networking | Stable | Traditional Ingress routing |
| 12 | **Scheduler (EPP)** | Routing | Stable | Intelligent request routing |
| 13 | **InferencePool** | Discovery | Stable | Service discovery for pods |
| 14 | **InferenceModel** | Metadata | Stable | Model registration with scheduler |
| 15 | **Routing Sidecar** | Architecture | Stable | Auto-injected in decode pods |
| 16 | **LoRA Adapters** | ML Feature | Experimental | Low-Rank Adaptation support |
| 17 | **Model Criticality** | Scheduling | Experimental | Priority-based scheduling |

---

## Feature-to-Phase Matrix (What runs where and when)

```
| Feature                        | Affects Phase | Prefill Pod Role                 | Decode Pod Role                    | Notes |
|--------------------------------|--------------|----------------------------------|------------------------------------|-------|
| Prefill/Decode Disaggregation  | Prefill,Decode | Prefill only                     | Decode only                        | Split phases to optimize cost/latency |
| Scheduler (EPP)                | Routing       | n/a                              | Sidecar receives routed requests   | Chooses best pod (load, KV, criticality) |
| Tensor Parallelism (TP)        | Prefill,Decode | High TP recommended               | Low/medium TP, more replicas       | TP shards tensors within each layer |
| Pipeline Parallelism (PP)      | Prefill       | Multi-node stages (optional)     | Typically unused for decode        | Use with TP when model is ultra-large |
| Data Parallelism (DP)          | Prefill,Decode | Multiple replicas for throughput  | Multiple replicas for throughput   | Training: sync gradients; Inference: LB |
| Expert Parallelism (MoE)       | Prefill,Decode | Router activates experts          | Router activates experts           | Combine with TP in MoE models |
| Gateway API / Ingress          | Routing       | n/a                              | n/a                                | External exposure and path routing |
| InferencePool                  | Routing       | Discovery for prefill pods        | Discovery for decode pods          | Gateway/Scheduler uses this list |
| Routing Sidecar                | Routing,Decode | n/a                              | Decides prefill vs local decode    | Handles KV metadata and forwarding |
| LoRA Adapters                  | Prefill,Decode | Load adapters                     | Load adapters                      | Model+adapter composition at runtime |
| Model Criticality              | Routing       | n/a                              | n/a                                | Scheduler prioritizes by criticality |
```

---

## Feature-by-Feature Deep Dive

### Feature 1: Model Specification

#### What It Does
Defines the source location and characteristics of the LLM to be deployed.

#### Configuration
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B-Instruct  # Model source
    name: llama-3                              # Model name for API
    criticality: Critical                       # Scheduling priority
    lora:                                       # Optional LoRA adapters
      adapters:
      - uri: hf://user/my-lora-adapter
        name: my-adapter
```

#### How It Works

**Step 1:** Controller reads `spec.model`

**Step 2:** Creates `storage-initializer` init container:
```yaml
initContainers:
- name: storage-initializer
  image: kserve/storage-initializer
  args:
  - --src-uri=hf://meta-llama/Llama-3-8B-Instruct
  - --dest-path=/mnt/models
  volumeMounts:
  - name: model-volume
    mountPath: /mnt/models
```

**Step 3:** Downloads model to shared volume

**Step 4:** Main container mounts `/mnt/models`

#### Containers Created
- **Init Container:** `storage-initializer` (downloads model, then exits)
- **Main Container:** vLLM or other inference runtime (serves model)

#### Request Flow
1. **Before startup:** Init container downloads model
2. **At startup:** Main container loads model from `/mnt/models`
3. **During inference:** Model already in memory, no additional downloads

#### Model URI Schemes Supported
- `hf://` - HuggingFace Hub
- `s3://` - Amazon S3
- `gs://` - Google Cloud Storage
- `pvc://` - Kubernetes PVC
- `file://` - Local filesystem

---

### Feature 2: Replicas (Horizontal Scaling)

#### What It Does
Controls the number of inference pod replicas for load balancing and high availability.

#### Configuration
```yaml
spec:
  replicas: 3  # Creates 3 identical pods
```

#### How It Works

**For Single Node Mode:**
```
LLMInferenceService
      │
      ▼
Deployment: my-llm-kserve
      │
      ├─► Pod 1 (Running)
      ├─► Pod 2 (Running)
      └─► Pod 3 (Running)
```

**For Disaggregated Mode:**
```
LLMInferenceService
      │
      ├─► Prefill Deployment (spec.prefill.replicas)
      │   ├─► Prefill Pod 1
      │   └─► Prefill Pod 2
      │
      └─► Decode Deployment (spec.replicas)
          ├─► Decode Pod 1
          ├─► Decode Pod 2
          └─► Decode Pod 3
```

#### Containers Created
- **Per Pod:** Same as single replica (1 container for single node, 2 for disaggregated decode)
- **Total Pods:** `replicas` count

#### Request Flow

**Without Scheduler:**
```
Gateway → Service (Round-Robin) → Any Pod
```

**With Scheduler (Recommended):**
```
Gateway → EPP (Intelligent Selection) → Optimal Pod
```

The scheduler selects the best pod based on:
- Current load
- KV cache availability
- Model criticality
- Prefix cache match

---

### Feature 3: Pod Template

#### What It Does
Allows full customization of the Kubernetes PodSpec for containers, volumes, env vars, resources, etc.

#### Configuration
```yaml
spec:
  template:
    serviceAccountName: my-sa
    containers:
    - name: main
      image: vllm/vllm-openai:latest
      command: ["vllm", "serve"]
      args:
      - --port=8000
      - --model=/mnt/models
      env:
      - name: CUDA_VISIBLE_DEVICES
        value: "0,1"
      resources:
        requests:
          nvidia.com/gpu: "2"
          cpu: "8"
          memory: "32Gi"
        limits:
          nvidia.com/gpu: "2"
          cpu: "8"
          memory: "32Gi"
      volumeMounts:
      - name: shm
        mountPath: /dev/shm
    volumes:
    - name: shm
      emptyDir:
        medium: Memory
        sizeLimit: 16Gi
```

#### How It Works

**Step 1:** Controller takes your `template` and enhances it:
```yaml
# Your template
template:
  containers:
  - name: main
    image: vllm/vllm-openai:latest

# Controller adds
initContainers:
- name: storage-initializer  # Auto-added for model download

# For disaggregated decode, also adds:
initContainers:
- name: llm-d-routing-sidecar  # Auto-added for routing
  restartPolicy: Always  # Runs as sidecar
```

**Step 2:** Controller applies to Deployment:
```yaml
Deployment:
  spec:
    template:
      spec: <your-template-with-enhancements>
```

#### Containers Created

**Single Node Mode:**
```
Pod: my-llm-kserve-xxxxx
├── Init Containers:
│   └── storage-initializer (downloads model, exits)
└── Containers:
    └── main (your specified container)
```

**Disaggregated Decode Mode:**
```
Decode Pod: my-llm-kserve-xxxxx
├── Init Containers:
│   ├── storage-initializer (downloads model, exits)
│   └── llm-d-routing-sidecar (restartPolicy: Always, runs as sidecar)
└── Containers:
    └── main (your specified container)
```

#### Request Flow
- Requests hit the container you specified in `template.containers[0]`
- For decode pods, routing sidecar intercepts on port 8000, forwards to main on port 8001

---

### Feature 4: BaseRefs (Configuration Inheritance)

#### What It Does
Allows LLMInferenceService to inherit configuration from one or more LLMInferenceServiceConfig templates.

#### Configuration
```yaml
# Base Config 1: Common settings
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: llm-base-config
spec:
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      resources:
        requests:
          cpu: "4"
          memory: "16Gi"

---
# Base Config 2: GPU settings
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: llm-gpu-config
spec:
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "1"

---
# LLMInferenceService: Inherits both
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm
spec:
  baseRefs:
  - name: llm-base-config  # Applied first
  - name: llm-gpu-config   # Applied second (overrides)
  
  model:
    uri: hf://meta-llama/Llama-3-8B
  
  # This overrides everything above
  replicas: 2
```

#### How It Works

**Merge Algorithm (Strategic Merge):**
```
1. Start with empty spec
2. Merge llm-base-config → spec
3. Merge llm-gpu-config → spec (overrides conflicts)
4. Merge LLMInferenceService.spec → spec (final, highest priority)
```

**Resulting Merged Spec:**
```yaml
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B
  replicas: 2
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3    # From base-config
      resources:
        requests:
          cpu: "4"                       # From base-config
          memory: "16Gi"                 # From base-config
          nvidia.com/gpu: "1"            # From gpu-config
```

#### Containers Created
- Same as without baseRefs
- BaseRefs only affect the **configuration**, not the **structure**

#### Request Flow
- No change in request flow
- BaseRefs only affect pod configuration

#### ⚠️ Known Issues
- **Template variables in baseRefs are not substituted properly** (Bug in v1alpha1)
- Workaround: Avoid using `{{.Name}}` or other template variables in configs referenced by baseRefs

---

### Feature 5: Template Variables

#### What It Does
Allows dynamic substitution of values in configuration using Go template syntax.

#### Configuration
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: dynamic-config
spec:
  model:
    name: "{{.Name}}-model"  # Substitutes to: my-llm-model
  
  template:
    containers:
    - name: main
      args:
      - --model-name={{.Spec.Model.Name}}   # Substitutes to actual model name
      - --namespace={{.Namespace}}           # Substitutes to namespace
      env:
      - name: POD_NAME
        value: "{{.Name}}"
      - name: FULL_PATH
        value: "{{.Namespace}}/{{.Name}}"   # Multiple vars in one string
```

#### Available Template Variables
```
{{.Name}}                    # LLMInferenceService metadata.name
{{.Namespace}}               # LLMInferenceService metadata.namespace
{{.Spec.Model.Name}}         # Model name from spec
{{.Spec.Model.URI}}          # Model URI
{{.ObjectMeta.Labels.xyz}}   # Any label
{{.GlobalConfig.xyz}}        # Controller global config
{{ChildName .Name "-suffix"}}  # Helper function: generates child resource name
```

#### How It Works

**Step 1:** Controller loads config with templates:
```yaml
template:
  containers:
  - args: ["--model={{.Name}}"]
```

**Step 2:** Calls `ReplaceVariables()` function:
```go
// Controller code
config, err := ReplaceVariables(llmSvc, llmSvcCfg, reconcilerConfig)
```

**Step 3:** Template engine substitutes:
```yaml
# Input
args: ["--model={{.Name}}"]

# After substitution
args: ["--model=my-llm"]
```

**Step 4:** Resulting config applied to Deployment

#### Containers Created
- No change in structure
- Only affects **arguments and environment variables** inside containers

#### Request Flow
- No impact on request flow
- Variables are substituted at **deployment time**, not **request time**

#### ⚠️ Known Issues
- **Template substitution is broken in v1alpha1**
- Variables are NOT substituted, pods receive literal strings like `{{.Name}}`
- This causes vLLM and other runtimes to crash
- **Workaround:** Don't use template variables, or use `ServingRuntime` + `InferenceService` instead

---

### Feature 6: Prefill/Decode Split (Disaggregated Serving)

#### What It Does
Separates LLM inference into two independent deployments:
- **Prefill:** Processes prompts (compute-intensive, parallel)
- **Decode:** Generates tokens (memory-intensive, sequential)

This is the most important architectural feature of LLMD.

#### Configuration
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-disaggregated
spec:
  model:
    uri: hf://meta-llama/Llama-3-70B-Instruct
  
  # Prefill configuration
  prefill:
    replicas: 2              # 2 prefill pods
    parallelism:
      tensor: 8              # 8-way tensor parallelism
    template:
      containers:
      - name: main
        env:
        - name: VLLM_PREFILL_MODE
          value: "true"      # Tells vLLM to run in prefill mode
        resources:
          requests:
            nvidia.com/gpu: "8"
  
  # Decode configuration (top-level)
  replicas: 16               # 16 decode pods
  parallelism:
    tensor: 1                # 1 GPU per decode pod
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "1"
  
  # Enable scheduler for routing
  router:
    gateway: {}
    route: {}
    scheduler: {}
```

#### How It Works

**Architecture:**
```
┌────────────────────────────────────────────────────────────┐
│                   DISAGGREGATED SERVING                    │
└────────────────────────────────────────────────────────────┘

USER REQUEST
     │
     ▼
GATEWAY (Envoy)
     │
     ▼
SCHEDULER (EPP)
     │ Route to best decode pod
     ▼
┌───────────────────────────────────────────────┐
│                 DECODE POD                    │
│  ┌───────────────────────────┐  ┌──────────┐ │
│  │ Routing Sidecar (:8000)   │  │ vLLM     │ │
│  │ Decide prefill vs decode  │  │ Decode   │ │
│  └──────────────┬────────────┘  │ (:8001)  │ │
└─────────────────┼───────────────┴──────────┘ │
                  │ Forward to prefill if new   │
                  ▼                             │
┌───────────────────────────────────────────────┐
│                 PREFILL POD                   │
│  ┌───────────────────────────┐                │
│  │ vLLM Prefill (:8000)      │                │
│  │ Process prompt (high TP)  │                │
│  └───────────────────────────┘                │
└───────────────┬───────────────────────────────┘
                │ First token + KV metadata
                ▼
DECODE POD (Sidecar attaches KV) → vLLM Decode (:8001) → Stream tokens
```

#### Containers Created

**Prefill Deployment: `<name>-kserve-prefill`**
```
Prefill Pod:
├── Init Containers:
│   └── storage-initializer
└── Containers:
    └── main (vLLM with VLLM_PREFILL_MODE=true)
        └── Ports: 8000 (HTTPS)
```

**Decode Deployment: `<name>-kserve`**
```
Decode Pod:
├── Init Containers:
│   ├── storage-initializer
│   └── llm-d-routing-sidecar (restartPolicy: Always)
│       └── Ports: 8000 (external, HTTPS)
│       └── Environment:
│           - INFERENCE_POOL_NAME=<name>-inference-pool
│           - CONNECTOR=nixlv2
│           - PREFILL_URL=https://<name>-kserve-prefill-svc:8000
└── Containers:
    └── main (vLLM decode)
        └── Ports: 8001 (internal, HTTPS)
```

**Scheduler Deployment: `<name>-kserve-router-scheduler`**
```
Scheduler Pod:
└── Containers:
    └── main (llm-d-inference-scheduler)
        └── Ports: 9002 (gRPC), 9003 (health), 9090 (metrics)
```

**Total Pods:**
```
Prefill: prefill.replicas (e.g., 2 pods)
Decode: replicas (e.g., 16 pods)
Scheduler: 1 pod
───────────────────────────────
Total: 2 + 16 + 1 = 19 pods
```

#### Request Flow

**First Request (New Conversation):**
```
1. User → Gateway
   POST /my-namespace/llama-disaggregated/v1/chat/completions
   Body: {"messages": [{"role": "user", "content": "Tell me a story"}]}

2. Gateway → Scheduler (EPP)
   "Which pod should handle this?"
   EPP checks:
     - Request has no session_id (new conversation)
     - Need prefill
   EPP responds: "Use decode-pod-1"

3. Gateway → Decode Pod 1 (Routing Sidecar :8000)
   Routing Sidecar receives request

4. Routing Sidecar Decision:
   Check: Do I have KV cache for this conversation?
   Answer: NO (first request)
   Action: Forward to PREFILL

5. Routing Sidecar → Prefill Pod 1 (:8000)
   Forward entire request to prefill

6. Prefill Pod Processing:
   vLLM Prefill:
     - Tokenize prompt: "Tell me a story" → [token_ids]
     - Process all prompt tokens (parallel across sequence)
     - Build KV cache per layer
     - Produce first output token (logits → sample)
   
   Response to Routing Sidecar:
     {
       "choices": [{
         "delta": {"content": "Once"},
         "kv_cache": {...metadata...}
       }]
     }

7. Routing Sidecar:
   - Receives response from prefill
   - Stores KV cache metadata for this conversation
   - Forwards "Once" to local vLLM Decode (:8001)

8. vLLM Decode (:8001):
   - Attaches KV cache
   - Generates next tokens sequentially (auto-regressive)
   - Streams tokens back to sidecar

9. Routing Sidecar → Gateway → User:
   Stream tokens as they're generated:
   "Once upon a time..."
```

**Follow-up Request (Same Conversation):**
```
1. User → Gateway (with session_id)

2. Gateway → Scheduler (EPP)
   EPP checks:
     - Request has session_id
     - KV cache likely exists
   EPP responds: "Use decode-pod-1" (same pod as before)

3. Gateway → Decode Pod 1 (Routing Sidecar)

4. Routing Sidecar Decision:
   Check: Do I have KV cache?
   Answer: YES!
   Action: Forward directly to local decode (:8001)
   NO prefill needed!

5. Routing Sidecar → Local vLLM Decode (:8001)

6. vLLM Decode:
   - Reuses existing KV cache
   - Generates new tokens
   - Streams back

7. Stream to user
```

#### Labels for Pod Identification

**Prefill Pods:**
```yaml
labels:
  app.kubernetes.io/component: llminferenceservice-workload-prefill
  app.kubernetes.io/name: llama-disaggregated
  llm-d.ai/role: prefill  # ← KEY LABEL
  kserve.io/component: workload
```

**Decode Pods:**
```yaml
labels:
  app.kubernetes.io/component: llminferenceservice-workload
  app.kubernetes.io/name: llama-disaggregated
  llm-d.ai/role: decode  # ← KEY LABEL
  kserve.io/component: workload
```

Find pods:
```bash
# Prefill pods
kubectl get pods -l llm-d.ai/role=prefill

# Decode pods
kubectl get pods -l llm-d.ai/role=decode
```

---

### Feature 7: Parallelism (Multi-GPU Distribution)

#### What It Does
Distributes model computation across multiple GPUs using various parallelism strategies.

#### Configuration
```yaml
spec:
  parallelism:
    tensor: 8         # Tensor parallelism: 8 GPUs (shard tensors within each layer)
    pipeline: 2       # Pipeline parallelism: 2 stages
    data: 4           # Data parallelism: 4 replicas
    dataLocal: 2      # Local data parallelism within a node
    dataRPCPort: 5555 # Port for data parallelism communication
    expert: true      # Expert parallelism for MoE models
```

#### Types of Parallelism

**1. Tensor Parallelism (Most Common)**
```
Model: Llama-3-70B (70 billion parameters)

Without Tensor Parallelism:
┌────────────────────┐
│   Single GPU           │
│   VRAM: 140GB          │
└────────────────────┘

With Tensor Parallelism (tensor: 8):
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ GPU 0         │ │ GPU 1         │ │ GPU 2         │ │ GPU 3         │
│ Shard of       │ │ Shard of       │ │ Shard of       │ │ Shard of       │
│ every layer    │ │ every layer    │ │ every layer    │ │ every layer    │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ GPU 4         │ │ GPU 5         │ │ GPU 6         │ │ GPU 7         │
│ Shard of       │ │ Shard of       │ │ Shard of       │ │ Shard of       │
│ every layer    │ │ every layer    │ │ every layer    │ │ every layer    │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

Per-GPU weights (FP16/BF16) ≈ 140GB ÷ 8 ≈ 17.5GB.
Additional memory needed: KV cache + activations (plan ≥24GB/GPU for 70B).
```

**2. Pipeline Parallelism**
```
Model stages split across GPUs:

GPU 0: Embedding + Layers 1-20
  │
  ▼ Pass hidden states
GPU 1: Layers 21-40
  │
  ▼ Pass hidden states
GPU 2: Layers 41-60
  │
  ▼ Pass hidden states
GPU 3: Layers 61-80 + Output head
```

**3. Data Parallelism**
```
Same model replicated across GPUs:

Request 1 → GPU 0 (full model)
Request 2 → GPU 1 (full model)
Request 3 → GPU 2 (full model)
Request 4 → GPU 3 (full model)

All GPUs sync gradients during training.
For inference: Load balancing across replicas.
```

**4. Expert Parallelism (MoE Models)**
```
Mixture of Experts model:

GPU 0: Expert 1, Expert 2
GPU 1: Expert 3, Expert 4
GPU 2: Expert 5, Expert 6
GPU 3: Expert 7, Expert 8

Router decides which experts to use per token.
```

#### How It Works

**Step 1:** Controller reads `parallelism` config

**Step 2:** Determines if using built-in configs:
```go
// Controller logic
if parallelism.tensor > 1 || parallelism.pipeline > 1 {
    // Use appropriate built-in config template
    if prefill != nil && worker != nil && parallelism.isPipelineParallel() {
        baseRefs = append(baseRefs, "kserve-config-llm-prefill-worker-pipeline-parallel")
    } else if parallelism.isTensorParallel() {
        // Use tensor parallelism config
    }
}
```

**Step 3:** Generates vLLM arguments:
```yaml
# For tensor=8
containers:
- name: main
  args:
  - --tensor-parallel-size=8
  resources:
    requests:
      nvidia.com/gpu: "8"  # MUST match tensor size!
```

**Step 4:** Applies to deployment

#### Containers Created

**Single-Node with Tensor Parallelism:**
```
Pod:
├── Init: storage-initializer
└── Container: main
    └── Resources:
        nvidia.com/gpu: "8"  # Requests 8 GPUs
    └── Args:
        --tensor-parallel-size=8
```

**Multi-Node with Pipeline Parallelism:**
```
LeaderWorkerSet:
├── Leader Pod:
│   └── Container: main (GPU 0-3, stages 1-2)
│       └── Args: --pipeline-parallel-size=2
└── Worker Pods (×1):
    └── Container: main (GPU 4-7, stages 3-4)
        └── Args: --pipeline-parallel-size=2
```

#### Request Flow

**Tensor Parallelism:**
```
Request arrives
  │
  ▼
For each layer (0–79):
  ├─► All GPUs compute their shard of the layer
  ├─► Collective ops (all-reduce/all-gather) to exchange partial results
  └─► Proceed to next layer
  │
  ▼
Final layer output → Response
```

**Pipeline Parallelism:**
```
Request arrives at Leader Pod
  │
  ▼
GPU 0-1: Process stages 1-2
  │ Send hidden states to Worker
  ▼
Worker Pod
GPU 2-3: Process stages 3-4
  │ Send results back to Leader
  ▼
Leader: Generate response
```

#### ⚠️ Critical Requirement
```yaml
# Parallelism config MUST match GPU allocation!
parallelism:
  tensor: 8              # vLLM will use 8 GPUs

resources:
  requests:
    nvidia.com/gpu: "8"  # Kubernetes must allocate 8 GPUs

# If mismatch: vLLM will crash or fall back to fewer GPUs
```

---

### Feature 8: Multi-Node (Worker) - Distributed Deployment

#### What It Does
Enables multi-node distributed deployment using LeaderWorkerSet (LWS) for very large models or high parallelism.

#### Configuration
```yaml
spec:
  # Leader (head) pod configuration
  replicas: 2          # 2 leader-worker groups
  parallelism:
    pipeline: 4        # 4-stage pipeline
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "4"
  
  # Worker pod configuration
  worker:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "4"
```

#### How It Works

**Architecture:**
```
┌──────────────────────────────────────────────────────────┐
│            LeaderWorkerSet (LWS)                                    │
│                                                                     │
│  Group 1:                                                           │
│  ┌──────────────────┐    ┌──────────────────┐                │ 
│  │ Leader (4 GPUs)     │    │ Worker (4 GPUs)     │                │
│  └──────────────────┘    └──────────────────┘               │
│                                                                    │
│  Group 2:                                                          │
│  ┌──────────────────┐    ┌──────────────────┐               │ 
│  │ Leader (4 GPUs)     │    │ Worker (4 GPUs)     │               │
│  └──────────────────┘    └──────────────────┘               │
│                                                                    │
│  Total: 16 GPUs (4 pods × 4 GPUs/pod)                              │
└──────────────────────────────────────────────────────────┘
```

**LeaderWorkerSet Controller:**
- Creates groups of pods (1 leader + N workers)
- Manages pod-to-pod discovery
- Injects environment variables for communication:
  - `LWS_LEADER_ADDRESS` - Leader pod IP
  - `LWS_WORKER_INDEX` - Worker index (0, 1, 2, ...)
  - Pod labels for discovery

#### Containers Created

**Leader Pod:**
```
Leader Pod: <name>-kserve-mn-0
├── Init: storage-initializer
└── Container: main
    └── Environment:
        - LWS_LEADER_ADDRESS=<leader-pod-ip>
        - LWS_WORKER_INDEX=0
    └── Args:
        - vllm serve /mnt/models
        - --pipeline-parallel-size=4
        - --distributed-executor-backend=ray
    └── Ports:
        - 8000 (HTTP)
        - 6379 (Ray head)
```

**Worker Pod:**
```
Worker Pod: <name>-kserve-mn-0-worker-1
└── Container: main
    └── Environment:
        - LWS_LEADER_ADDRESS=<leader-pod-ip>
        - LWS_WORKER_INDEX=1
        - RAY_ADDRESS=$(LWS_LEADER_ADDRESS):6379
    └── Args:
        - vllm serve /mnt/models
        - --pipeline-parallel-size=4
        - --distributed-executor-backend=ray
```

#### Request Flow

```
Request
  │
  ▼
Leader Pod (receives request)
  │
  ├─► Stage 1-2: Process on leader GPUs
│                                     │
  │   ▼ Send hidden states via Ray
  │
  └─► Worker Pod
      │
      ├─► Stage 3-4: Process on worker GPUs
      │
      ▼ Send results back via Ray
      │
Leader Pod (generates response)
  │
  ▼
Stream to client
```

---

### Feature 9-11: Networking (Gateway API / Ingress)

#### What It Does
Exposes the LLM service externally using Kubernetes Gateway API (modern) or Ingress (traditional).

#### Configuration Options

**Option 1: Managed Gateway API (Recommended)**
```yaml
spec:
  router:
    gateway: {}      # Use default gateway
    route: {}        # Controller creates HTTPRoute
```

**Option 2: Bring Your Own Gateway**
```yaml
spec:
  router:
    gateway:
      refs:
      - name: istio-gateway
        namespace: istio-system
    route:
      http:
        spec:
          rules:
          - matches:
            - path:
                type: PathPrefix
                value: /my-custom-path
```

**Option 3: Ingress (Traditional)**
```yaml
spec:
  router:
    ingress:
      refs:
      - name: my-ingress
        namespace: default
```

#### How It Works

**Gateway API Mode (Default):**
```
1. Controller creates HTTPRoute:
   Name: <llmisvc-name>-kserve-route
   Namespace: <llmisvc-namespace>
   
   Spec:
     parentRefs:
     - name: <gateway-name>
       namespace: <gateway-namespace>
     
     rules:
     - matches:
       - path:
           type: PathPrefix
           value: /<namespace>/<llmisvc-name>
       backendRefs:
       - group: inference.networking.x-k8s.io
         kind: InferencePool
         name: <llmisvc-name>-inference-pool
         port: 8000
       filters:
       - type: URLRewrite
         urlRewrite:
           path:
             type: ReplacePrefixMatch
             replacePrefixMatch: /

2. Gateway (Envoy) processes request:
   - Matches path: /my-namespace/my-llm/*
   - Rewrites to: /*
   - Forwards to InferencePool

3. InferencePool:
   - Lists pods matching selector
   - Provides pod IPs to Gateway

4. Gateway forwards to pod
```

#### Containers Created
- **No additional containers** for networking
- Gateway and HTTPRoute are external Kubernetes resources

#### Request Flow

**With Scheduler:**
```
User
  │
  ▼
Gateway (Envoy)
  │ Match HTTPRoute
  ▼
Scheduler (EPP) via ExtProc
  │ Select optimal pod
  ▼
Gateway forwards to specific pod
  │
  ▼
Decode Pod (or Prefill Pod)
```

**Without Scheduler:**
```
User
  │
  ▼
Gateway (Envoy)
  │ Match HTTPRoute
  ▼
InferencePool (Service Discovery)
  │ List available pods
  ▼
Gateway load-balances to pod
  │
  ▼
Random Pod
```

---

### Feature 12: Scheduler (EPP - Endpoint Picker)

#### What It Does
Intelligent request routing that selects the optimal pod to handle each request based on load, KV cache availability, and model criticality.

#### Configuration
```yaml
spec:
  router:
    scheduler:
      pool:
        spec:
          selector: {}            # Auto-populated with pod labels
          targetPortNumber: 8000
      template:
        containers:
        - name: main
          image: ghcr.io/llm-d/llm-d-inference-scheduler:v0.2.0
          ports:
          - containerPort: 9002
            name: grpc
          - containerPort: 9090
            name: metrics
          args:
          - --poolName=<llmisvc-name>-inference-pool
          - --poolNamespace=<namespace>
          - --grpcPort=9002
```

#### How It Works

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│              SCHEDULER (EPP) ARCHITECTURE                         │
└─────────────────────────────────────────────────────────┘

Gateway (Envoy)
     │
     │ ExtProc (External Processing Protocol)
     ▼
┌─────────────────────────┐
│   Scheduler (EPP)           │
│                             │
│  1. Query InferencePool     │
│     └─ Prefill pods         │
│     └─ Decode pods          │
│                             │
│  2. Check pod metrics       │
│                             │
│  3. Apply scoring:          │
│     - KV cache match        │
│     - Pod load              │
│     - Model criticality     │
│     - Round-robin           │
│                             │
│  4. Select optimal pod      │
└─────────────────────────┘
     │
     │ Response: "Use pod X at IP Y"
     ▼
Gateway forwards request to pod X
```

**Scoring Algorithm:**
```go
// Simplified algorithm
for each pod in InferencePool {
    score = 0
    
    // Prefix cache match (highest priority)
    if pod.hasKVCache(request.sessionID) {
        score += 1000
    }
    
    // Pod load (lower is better)
    score -= pod.currentLoad * 10
    
    // Model criticality
    if request.modelCriticality == "Critical" {
        score += 100
    }
    
    // Fairness (round-robin component)
    score += pod.timeSinceLastRequest / 1000
}

return podWithHighestScore
```

#### Containers Created

**Scheduler Deployment: `<name>-kserve-router-scheduler`**
```
Scheduler Pod:
└── Container: main (llm-d-inference-scheduler)
    └── Ports:
        - 9002: gRPC (ExtProc)
        - 9003: Health check
        - 9090: Prometheus metrics
    └── Environment:
        - POOL_NAME=<llmisvc-name>-inference-pool
        - POOL_NAMESPACE=<namespace>
```

#### Request Flow

```
Request arrives at Gateway
  │
  ├─► WITHOUT Scheduler:
  │   └─► Gateway → Random pod (round-robin)
  │
  └─► WITH Scheduler:
      │
      1. Gateway calls Scheduler (gRPC ExtProc)
         │
      2. Scheduler queries InferencePool
         └─► Lists all pods (prefill + decode)
         │
      3. Scheduler checks metrics for each pod:
         - Current load (requests/sec)
         - KV cache availability
         - Model criticality
         │
      4. Scheduler scores pods
         │
      5. Scheduler returns: "Use decode-pod-3"
         │
      6. Gateway forwards request to decode-pod-3
         │
      7. If decode-pod-3 routing sidecar needs prefill:
         └─► Sidecar forwards to prefill pod
         │
      8. Response flows back through sidecar → Gateway → User
```

---

### Feature 13: InferencePool (Service Discovery)

#### What It Does
Provides dynamic service discovery for inference pods, allowing Gateway and Scheduler to discover available pods.

#### Configuration
```yaml
# Created automatically by controller
apiVersion: inference.networking.x-k8s.io/v1alpha2
kind: InferencePool
metadata:
  name: my-llm-inference-pool
spec:
  selector:
    app.kubernetes.io/name: my-llm
    kserve.io/component: workload
  targetPortNumber: 8000
  extensionRef:
    kind: Service
    name: my-llm-epp-service
    failureMode: FailOpen
```

#### How It Works

**Service Discovery:**
```
InferencePool watches pods with matching labels
  │
  ├─► Prefill pods (llm-d.ai/role=prefill)
  └─► Decode pods (llm-d.ai/role=decode)
  │
  ▼
Maintains list of pod IPs + metadata:
  - Pod IP: 10.0.1.5
  - Pod name: my-llm-kserve-xxxxx
  - Role: decode
  - Status: Ready
  - Ports: 8000
  │
  ▼
Gateway/Scheduler query InferencePool:
  "Give me all available pods"
  │
  ▼
InferencePool returns list of pod IPs
```

#### Containers Created
- **None** - InferencePool is a CRD resource, not a pod

#### Request Flow
- InferencePool is **queried** by Gateway and Scheduler
- Does not handle requests directly
- Provides pod discovery information

---

### Feature 14: InferenceModel (Model Metadata)

#### What It Does
Registers the model with the Inference Gateway scheduler, providing metadata for intelligent routing decisions.

#### Configuration
```yaml
# Created automatically by controller
apiVersion: inference.networking.x-k8s.io/v1alpha2
kind: InferenceModel
metadata:
  name: my-llm
spec:
  modelName: llama-3-8b
  poolRef:
    group: inference.networking.x-k8s.io
    kind: InferencePool
    name: my-llm-inference-pool
  criticality: Critical  # or: Sheddable, Normal
```

#### How It Works

**Model Registration:**
```
Scheduler reads InferenceModel
  │
  ├─► Model name: llama-3-8b
  ├─► Criticality: Critical
  └─► Pool: my-llm-inference-pool
  │
  ▼
When request arrives:
  "model": "llama-3-8b"
  │
  ▼
Scheduler matches:
  - Request model → InferenceModel
  - InferenceModel → InferencePool
  - InferencePool → Available pods
  │
  ▼
Applies criticality:
  - Critical: Higher priority
  - Normal: Standard priority
  - Sheddable: Lower priority, can be preempted
```

#### Containers Created
- **None** - InferenceModel is a CRD resource

---

### Feature 15: Routing Sidecar (Auto-Injected)

#### What It Does
Automatically injected sidecar in decode pods that intelligently routes requests between prefill and decode.

#### Configuration
```yaml
# Auto-injected by controller, cannot be customized directly
initContainers:
- name: llm-d-routing-sidecar
  image: ghcr.io/llm-d/llm-d:v0.2.0
  command: ["/llm-d-routing-sidecar"]
  args:
  - --prefill-url=https://<llmisvc-name>-kserve-prefill-svc:8000
  - --decode-url=https://localhost:8001
  - --connector=nixlv2
  - --port=8000
  env:
  - name: INFERENCE_POOL_NAME
    value: <llmisvc-name>-inference-pool
  ports:
  - containerPort: 8000
    protocol: TCP
  restartPolicy: Always  # Runs as sidecar, not init container
```

#### How It Works

**Sidecar Logic:**
```
Request arrives at Decode Pod port 8000
  │
  ▼
Routing Sidecar intercepts
  │
  ├─► Check: Is this a new conversation?
  │   └─► YES: KV cache doesn't exist
  │                                   │
  │       ├─► Forward to PREFILL
  │                              │
  │                              │
  │       ▼
  │       Prefill processes prompt
  │                              │
  │       ▼
  │       Prefill returns: first token + KV cache metadata
  │                              │
  │       ▼
  │       Sidecar stores KV cache for session
  │       │
  │       └─► Forward remaining generation to local decode
  │           https://localhost:8001
  │
  └─► NO: KV cache exists
      │
      └─► Forward directly to local decode
          https://localhost:8001
          (no prefill needed)
```

#### Containers Created

**In Decode Pods:**
```
Decode Pod:
├── Init Containers:
│   ├── storage-initializer
│   └── llm-d-routing-sidecar  # ← THIS
│       restartPolicy: Always   # Actually runs as sidecar
│       └── Ports: 8000 (external)
└── Containers:
    └── main (vLLM decode)
        └── Ports: 8001 (internal)
```

#### Request Flow
See Feature 6 (Prefill/Decode) for detailed request flow.

---

### Feature 16: LoRA Adapters

#### What It Does
Supports deploying Low-Rank Adaptation (LoRA) adapters alongside base models for efficient fine-tuning.

#### Configuration
```yaml
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B
    lora:
      adapters:
      - uri: hf://user/sql-lora
        name: sql-adapter
      - uri: hf://user/math-lora
        name: math-adapter
```

#### How It Works

**Model + Adapters:**
```
Pod:
├── Init: storage-initializer
│   └── Downloads:
│       ├── Base model → /mnt/models
│       ├── sql-lora → /mnt/models/adapters/sql-adapter
│       └── math-lora → /mnt/models/adapters/math-adapter
└── Container: main (vLLM)
    └── Args:
        --model=/mnt/models
        --enable-lora
        --lora-modules sql-adapter=/mnt/models/adapters/sql-adapter
        --lora-modules math-adapter=/mnt/models/adapters/math-adapter
```

#### Containers Created
- Same as base model
- Init container downloads additional adapters

#### Request Flow
```
Request with adapter:
{
  "model": "sql-adapter",  # Specify adapter name
  "messages": [{"role": "user", "content": "Generate SQL query"}]
}
  │
  ▼
vLLM loads:
  Base model + sql-adapter LoRA weights
  │
  ▼
Generate response with adapter
```

---

### Feature 17: Model Criticality

#### What It Does
Assigns priority levels to models for scheduler-based request prioritization.

#### Configuration
```yaml
spec:
  model:
    name: important-model
    uri: hf://...
    criticality: Critical  # or: Normal, Sheddable
```

#### Criticality Levels

| Level | Priority | Behavior |
|-------|----------|----------|
| **Critical** | Highest | Always served, never preempted |
| **Normal** | Medium | Standard priority |
| **Sheddable** | Lowest | Can be preempted under load |

#### How It Works

**Scheduler Scoring:**
```
Request for Critical model:
  Base score: 100
  + Criticality bonus: +100
  = 200

Request for Normal model:
  Base score: 100
  + Criticality bonus: 0
  = 100

Request for Sheddable model:
  Base score: 100
  + Criticality bonus: -50
  = 50

Under high load:
  - Critical requests get priority
  - Sheddable requests may be rejected (503)
```

---

## Container Structure for Each Feature

### Summary Table

| Deployment Mode | Init Containers | Main Containers | Sidecar | Total Containers |
|-----------------|-----------------|-----------------|---------|------------------|
| **Single Node** | 1 (storage-init) | 1 (main) | No | 2 |
| **Disaggregated Prefill** | 1 (storage-init) | 1 (main) | No | 2 |
| **Disaggregated Decode** | 2 (storage-init, routing-sidecar*) | 1 (main) | Yes* | 3 total, 2 running |
| **Multi-Node Leader** | 1 (storage-init) | 1 (main) | No | 2 |
| **Multi-Node Worker** | 0 | 1 (main) | No | 1 |
| **Scheduler** | 0 | 1 (main) | No | 1 |

*routing-sidecar has `restartPolicy: Always`, so it runs continuously like a sidecar

---

## Real-World Deployment Examples

### Example 1: Simple Single-Node Deployment

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-8b-simple
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B-Instruct
  
  replicas: 2
  
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:latest
      resources:
        requests:
          nvidia.com/gpu: "1"
          cpu: "4"
          memory: "16Gi"
  
  router:
    gateway: {}
    route: {}
```

**Deployed Resources:**
```
Deployments:
├── llama-8b-simple-kserve (2 replicas)
│   └── Pod structure:
│       ├── Init: storage-initializer
│       └── Container: main (vLLM)

Services:
└── llama-8b-simple-kserve-svc (ClusterIP)

HTTPRoute:
└── llama-8b-simple-kserve-route

Total Pods: 2
Total Containers: 2 init + 2 main = 4
```

**URL:** `http://<gateway>/<namespace>/llama-8b-simple`

---

### Example 2: Disaggregated Prefill/Decode

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-70b-disagg
spec:
  model:
    uri: hf://meta-llama/Llama-3-70B-Instruct
  
  # Prefill
  prefill:
    replicas: 2
    parallelism:
      tensor: 8
    template:
      containers:
      - name: main
        env:
        - name: VLLM_PREFILL_MODE
          value: "true"
        resources:
          requests:
            nvidia.com/gpu: "8"
            cpu: "32"
            memory: "256Gi"
  
  # Decode
  replicas: 8
  parallelism:
    tensor: 2
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "2"
          cpu: "16"
          memory: "64Gi"
  
  # Networking + Scheduler
  router:
    gateway: {}
    route: {}
    scheduler: {}
```

**Deployed Resources:**
```
Deployments:
├── llama-70b-disagg-kserve-prefill (2 replicas)
│   └── Pod structure:
│       ├── Init: storage-initializer
│       └── Container: main (vLLM prefill)
│           └── GPUs: 8 per pod
│
├── llama-70b-disagg-kserve (8 replicas)
│   └── Pod structure:
│       ├── Init: storage-initializer
│       ├── Init: llm-d-routing-sidecar (restartPolicy: Always)
│       └── Container: main (vLLM decode)
│           └── GPUs: 2 per pod
│
└── llama-70b-disagg-kserve-router-scheduler (1 replica)
    └── Pod structure:
        └── Container: main (EPP)

Services:
├── llama-70b-disagg-kserve-prefill-svc
├── llama-70b-disagg-kserve-svc
└── llama-70b-disagg-epp-service

InferencePool:
└── llama-70b-disagg-inference-pool
    └── Selects: Prefill (2) + Decode (8) = 10 pods

HTTPRoute:
└── llama-70b-disagg-kserve-route

Total Pods: 2 + 8 + 1 = 11
Total GPUs: (2×8) + (8×2) = 16 + 16 = 32 GPUs
Total Containers Running: 2 + (8×2) + 1 = 19
```

**Request Flow:**
```
User → Gateway → Scheduler (EPP) → Decode Pod
                                    └─► Routing Sidecar
                                        ├─► Prefill Pod (first request)
                                        └─► Local Decode (subsequent tokens)
```

---

### Example 3: Multi-Node with Pipeline Parallelism

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-405b-multinode
spec:
  model:
    uri: hf://meta-llama/Llama-3-405B
  
  replicas: 4  # 4 leader-worker groups
  parallelism:
    pipeline: 4  # 4-stage pipeline
  
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "8"
  
  worker:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "8"
  
  router:
    gateway: {}
    route: {}
```

**Deployed Resources:**
```
LeaderWorkerSets:
└── llama-405b-multinode-kserve-mn (4 groups)
    ├── Group 1:
    │   ├── Leader Pod (8 GPUs)
    │   └── Worker Pod (8 GPUs)
    │
    ├── Group 2:
    │   ├── Leader Pod (8 GPUs)
    │   └── Worker Pod (8 GPUs)
    │
    ├── Group 3:
    │   ├── Leader Pod (8 GPUs)
    │   └── Worker Pod (8 GPUs)
    │
    └── Group 4:
        ├── Leader Pod (8 GPUs)
        └── Worker Pod (8 GPUs)

Total Pods: 4 leaders + 4 workers = 8
Total GPUs: 8 × 8 = 64 GPUs
Pipeline: Each group processes 4 stages across 2 pods
```

---

## Conclusion

### Key Takeaways

1. **LLMD** is a comprehensive CRD for LLM deployments with advanced features
2. **Disaggregated serving** (prefill/decode) is the standout architecture feature
3. **Container structure** varies based on deployment mode:
   - Simple: 1 main container
   - Disaggregated decode: 2 containers (routing sidecar + main)
   - Multi-node: Multiple pods with discovery
4. **Request routing** is intelligent with Scheduler (EPP) and InferencePool
5. **Parallelism** enables large model distribution across GPUs
6. **Template variables** and **baseRefs** have bugs in v1alpha1

### Production Recommendations

⚠️ **Critical:** LLMD v1alpha1 has known bugs (template substitution). For production:
1. Use `ServingRuntime` + `InferenceService` (v1beta1) instead
2. If using LLMD, avoid template variables
3. Test thoroughly before production deployment
4. Monitor for controller reconciliation issues

### Next Steps

- Review specific features you need
- Start with simple single-node deployment
- Gradually add features (parallelism, disaggregation, scheduler)
- Monitor pod structure and resource usage
- Test end-to-end request flow

---

**Document End**  
**Version:** 1.0  
**Last Updated:** October 13, 2025

