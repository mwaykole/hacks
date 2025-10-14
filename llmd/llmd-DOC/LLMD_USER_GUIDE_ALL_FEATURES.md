# LLMD User Guide - All Features Explained

**Audience:** End Users, Developers, DevOps Engineers  
**Focus:** Practical usage, what you'll see, how to deploy  
**Date:** October 13, 2025

---

## 📖 Introduction

This guide explains **every feature** of LLMInferenceService (LLMD) from a **user perspective**. For each feature, you'll learn:

✅ **What it does** (in simple terms)  
✅ **When to use it**  
✅ **How to deploy it** (simple YAML)  
✅ **What you'll see** (pods, containers, URLs)  
✅ **How requests work** (user perspective)  
✅ **Common use cases**

---

## Table of Contents

### Basic Features
1. [Deploying a Simple LLM](#feature-1-deploying-a-simple-llm)
2. [Scaling Your LLM (Replicas)](#feature-2-scaling-your-llm-replicas)
3. [Customizing Your Container](#feature-3-customizing-your-container)

### Configuration Features
4. [Reusing Configurations (BaseRefs)](#feature-4-reusing-configurations-baserefs)
5. [Dynamic Configuration (Template Variables)](#feature-5-dynamic-configuration-template-variables)

### Advanced Serving
6. [Separating Prefill and Decode](#feature-6-separating-prefill-and-decode)
7. [Using Multiple GPUs (Parallelism)](#feature-7-using-multiple-gpus-parallelism)
8. [Multi-Node Deployment](#feature-8-multi-node-deployment)

### Networking
9. [Exposing Your LLM (Gateway API)](#feature-9-exposing-your-llm-gateway-api)
10. [Using Custom Gateways](#feature-10-using-custom-gateways)
11. [Traditional Ingress](#feature-11-traditional-ingress)

### Intelligent Routing
12. [Smart Request Routing (Scheduler)](#feature-12-smart-request-routing-scheduler)

### Advanced ML Features
13. [LoRA Adapters](#feature-13-lora-adapters)
14. [Model Priority](#feature-14-model-priority)

---

## Feature 1: Deploying a Simple LLM

### What It Does
Deploys a Large Language Model from HuggingFace, S3, or other sources.

### When to Use
- Your first LLM deployment
- Small to medium models (up to ~13B parameters)
- Single GPU is enough
- You don't need advanced features

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-first-llm
  namespace: my-namespace
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B-Instruct
  
  replicas: 1
  
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:latest
      resources:
        requests:
          nvidia.com/gpu: "1"
          cpu: "4"
          memory: "16Gi"
        limits:
          nvidia.com/gpu: "1"
          cpu: "4"
          memory: "16Gi"
  
  router:
    gateway: {}
    route: {}
```

### What You'll See

**After applying the YAML:**

```bash
# Check the LLMInferenceService
$ kubectl get llmisvc my-first-llm -n my-namespace

NAME            URL                                                READY   AGE
my-first-llm    http://gateway.example.com/my-namespace/my-first-llm   True    5m

# Check pods
$ kubectl get pods -n my-namespace

NAME                                  READY   STATUS    RESTARTS   AGE
my-first-llm-kserve-xxxxx-yyyyy       1/1     Running   0          5m
```

**Pod Details:**
```
Pod: my-first-llm-kserve-xxxxx-yyyyy
├─ Init Container: storage-initializer
│  └─ Downloads model from HuggingFace
│  └─ Status: Completed (exits after download)
│
└─ Container: main
   └─ vLLM server running on port 8000
   └─ Status: Running
   └─ GPU: 1 NVIDIA GPU allocated
```

**Total Containers You'll See:**
- **1 pod**
- **1 running container** (main)
- **1 completed init container** (storage-initializer)

### How to Use

**Get the URL:**
```bash
kubectl get llmisvc my-first-llm -n my-namespace -o jsonpath='{.status.url}'
```

**Send a request:**
```bash
curl -X POST http://gateway.example.com/my-namespace/my-first-llm/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-first-llm",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

**Response:**
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    }
  }],
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 8,
    "total_tokens": 13
  }
}
```

### Request Flow

```
You → Gateway → my-first-llm pod → vLLM → Response back to you
```

Simple! One pod handles everything.

---

## Feature 2: Scaling Your LLM (Replicas)

### What It Does
Creates multiple copies of your LLM for:
- Higher throughput (handle more users)
- High availability (if one pod fails, others continue)
- Load balancing

### When to Use
- Many concurrent users
- Need high availability
- Want better performance

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: scaled-llm
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B-Instruct
  
  replicas: 3  # ← 3 pods instead of 1
  
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:latest
      resources:
        requests:
          nvidia.com/gpu: "1"
  
  router:
    gateway: {}
    route: {}
```

### What You'll See

```bash
$ kubectl get pods -n my-namespace

NAME                              READY   STATUS    RESTARTS   AGE
scaled-llm-kserve-xxxxx-aaaaa     1/1     Running   0          2m
scaled-llm-kserve-xxxxx-bbbbb     1/1     Running   0          2m
scaled-llm-kserve-xxxxx-ccccc     1/1     Running   0          2m
```

**Total Resources:**
- **3 pods**
- **3 running containers** (1 per pod)
- **3 GPUs** (1 per pod)

### How Requests Work

```
User 1 → Gateway → Pod 1
User 2 → Gateway → Pod 2
User 3 → Gateway → Pod 3
User 4 → Gateway → Pod 1 (round-robin back to first pod)
```

Gateway automatically load-balances requests across all 3 pods.

### Benefits

| Scenario | With 1 Replica | With 3 Replicas |
|----------|----------------|-----------------|
| **Throughput** | 10 requests/sec | ~30 requests/sec |
| **Pod failure** | Service down | 2 pods still work |
| **Maintenance** | Must stop service | Can drain 1 pod at a time |

---

## Feature 3: Customizing Your Container

### What It Does
Lets you fully customize:
- Container image
- Environment variables
- Resource limits
- Volumes
- Anything in a Kubernetes PodSpec

### When to Use
- Need specific vLLM version
- Want to set environment variables
- Need custom volumes (shared memory, etc.)
- Want to control CPU/memory/GPU precisely

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: custom-llm
spec:
  model:
    uri: s3://my-bucket/my-model/
  
  template:
    serviceAccountName: my-service-account  # Custom service account
    
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3  # Specific version
      
      command: ["vllm", "serve"]
      args:
      - /mnt/models
      - --port=8000
      - --max-model-len=4096
      - --dtype=float16
      - --trust-remote-code
      
      env:
      - name: CUDA_VISIBLE_DEVICES
        value: "0"
      - name: VLLM_LOGGING_LEVEL
        value: "INFO"
      - name: HF_TOKEN
        valueFrom:
          secretKeyRef:
            name: hf-secret
            key: token
      
      resources:
        requests:
          nvidia.com/gpu: "1"
          cpu: "8"
          memory: "32Gi"
        limits:
          nvidia.com/gpu: "1"
          cpu: "8"
          memory: "32Gi"
      
      volumeMounts:
      - name: shm
        mountPath: /dev/shm
      - name: cache
        mountPath: /tmp/cache
    
    volumes:
    - name: shm
      emptyDir:
        medium: Memory
        sizeLimit: 16Gi
    - name: cache
      emptyDir: {}
  
  router:
    gateway: {}
    route: {}
```

### What You'll See

```bash
$ kubectl describe pod custom-llm-kserve-xxxxx

Containers:
  main:
    Image: vllm/vllm-openai:v0.6.3
    Command: vllm serve
    Args: /mnt/models --port=8000 --max-model-len=4096 ...
    Environment:
      CUDA_VISIBLE_DEVICES: 0
      VLLM_LOGGING_LEVEL: INFO
      HF_TOKEN: <from secret>
    Resources:
      Limits: cpu: 8, memory: 32Gi, nvidia.com/gpu: 1
      Requests: cpu: 8, memory: 32Gi, nvidia.com/gpu: 1
    Mounts:
      /dev/shm from shm
      /tmp/cache from cache
```

Same **1 pod, 1 container**, but fully customized!

---

## Feature 4: Reusing Configurations (BaseRefs)

### What It Does
Lets you create **configuration templates** that multiple LLMs can inherit from.

### When to Use
- Deploying multiple similar LLMs
- Want to share common settings (image, resources, etc.)
- Easy to update many LLMs at once

### How to Deploy

**Step 1: Create a base configuration**
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: standard-llm-config
  namespace: my-namespace
spec:
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      resources:
        requests:
          cpu: "4"
          memory: "16Gi"
          nvidia.com/gpu: "1"
        limits:
          cpu: "4"
          memory: "16Gi"
          nvidia.com/gpu: "1"
```

**Step 2: Create LLMs that use it**
```yaml
# LLM 1
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-8b
spec:
  baseRefs:
  - name: standard-llm-config  # ← Inherit base config
  
  model:
    uri: hf://meta-llama/Llama-3-8B
  
  replicas: 2

---
# LLM 2
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: mistral-7b
spec:
  baseRefs:
  - name: standard-llm-config  # ← Same base config
  
  model:
    uri: hf://mistralai/Mistral-7B-Instruct-v0.2
  
  replicas: 3
```

### What You'll See

```bash
$ kubectl get llmisvc -n my-namespace

NAME          URL                                           READY
llama-8b      http://gateway.../my-namespace/llama-8b      True
mistral-7b    http://gateway.../my-namespace/mistral-7b    True

$ kubectl get pods -n my-namespace

NAME                                READY   STATUS    AGE
llama-8b-kserve-xxxxx-aaaaa         1/1     Running   2m
llama-8b-kserve-xxxxx-bbbbb         1/1     Running   2m
mistral-7b-kserve-yyyyy-ccccc       1/1     Running   2m
mistral-7b-kserve-yyyyy-ddddd       1/1     Running   2m
mistral-7b-kserve-yyyyy-eeeee       1/1     Running   2m
```

Both LLMs use the **same base configuration** but different models and replica counts.

### Benefits

**Change all LLMs at once:**
```yaml
# Update base config
kind: LLMInferenceServiceConfig
metadata:
  name: standard-llm-config
spec:
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.7.0  # ← Update image version
```

All LLMs using this config will automatically update!

---

## Feature 5: Dynamic Configuration (Template Variables)

### What It Does
Automatically substitutes values in your configuration using variables like `{{.Name}}`, `{{.Namespace}}`, etc.

### When to Use
- Want configurations that adapt based on the LLM name
- Need namespace-aware configurations
- Want to avoid repeating values

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: dynamic-config
spec:
  model:
    name: "{{.Name}}-model"  # Automatically set based on LLM name
  
  template:
    containers:
    - name: main
      env:
      - name: MODEL_ID
        value: "{{.Name}}"
      - name: NAMESPACE
        value: "{{.Namespace}}"
      - name: FULL_NAME
        value: "{{.Namespace}}/{{.Name}}"

---
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: smart-llm
  namespace: production
spec:
  baseRefs:
  - name: dynamic-config
  
  model:
    uri: hf://meta-llama/Llama-3-8B
```

### What You'll See

```bash
$ kubectl get pod smart-llm-kserve-xxxxx -o yaml

env:
- name: MODEL_ID
  value: smart-llm           # ← Substituted from {{.Name}}
- name: NAMESPACE
  value: production          # ← Substituted from {{.Namespace}}
- name: FULL_NAME
  value: production/smart-llm  # ← Substituted from both
```

### ⚠️ Important Note

**Known Bug:** Template variables **don't work properly** in the current version (v1alpha1). They are not substituted and appear as literal strings `{{.Name}}`.

**Workaround:** Don't use template variables, or use `ServingRuntime` + `InferenceService` instead.

---

## Feature 6: Separating Prefill and Decode

### What It Does
Splits your LLM into two separate deployments:
- **Prefill pods**: Process prompts (fast, parallel, needs more GPUs)
- **Decode pods**: Generate output tokens (slower, sequential, needs less GPUs)

This is called **disaggregated serving**.

### When to Use
- Large models (30B+ parameters)
- Many users with different prompt lengths
- Want to scale prefill and decode independently
- Need to optimize GPU usage

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-70b
spec:
  model:
    uri: hf://meta-llama/Llama-3-70B-Instruct
  
  # Prefill configuration
  prefill:
    replicas: 2              # 2 prefill pods
    parallelism:
      tensor: 8              # 8 GPUs per prefill pod
    template:
      containers:
      - name: main
        env:
        - name: VLLM_PREFILL_MODE
          value: "true"      # Tell vLLM to run in prefill mode
        resources:
          requests:
            nvidia.com/gpu: "8"
            cpu: "32"
            memory: "256Gi"
  
  # Decode configuration
  replicas: 8                # 8 decode pods
  parallelism:
    tensor: 2                # 2 GPUs per decode pod
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "2"
          cpu: "16"
          memory: "64Gi"
  
  # Enable smart routing
  router:
    gateway: {}
    route: {}
    scheduler: {}            # ← Important for disaggregated serving!
```

### What You'll See

```bash
$ kubectl get pods -n my-namespace

NAME                                              READY   STATUS    AGE
# Prefill pods (2 pods)
llama-70b-kserve-prefill-xxxxx-aaaaa              1/1     Running   5m
llama-70b-kserve-prefill-xxxxx-bbbbb              1/1     Running   5m

# Decode pods (8 pods)
llama-70b-kserve-yyyyy-ccccc                      2/2     Running   5m
llama-70b-kserve-yyyyy-ddddd                      2/2     Running   5m
llama-70b-kserve-yyyyy-eeeee                      2/2     Running   5m
llama-70b-kserve-yyyyy-fffff                      2/2     Running   5m
llama-70b-kserve-yyyyy-ggggg                      2/2     Running   5m
llama-70b-kserve-yyyyy-hhhhh                      2/2     Running   5m
llama-70b-kserve-yyyyy-iiiii                      2/2     Running   5m
llama-70b-kserve-yyyyy-jjjjj                      2/2     Running   5m

# Scheduler pod (1 pod)
llama-70b-kserve-router-scheduler-zzzzz-kkkkk     1/1     Running   5m
```

**Pod Structure:**

**Prefill Pod:**
```
llama-70b-kserve-prefill-xxxxx-aaaaa
├─ Init: storage-initializer (completed)
└─ Container: main (vLLM prefill)
   └─ 8 GPUs, port 8000
```

**Decode Pod:**
```
llama-70b-kserve-yyyyy-ccccc
├─ Init: storage-initializer (completed)
├─ Init: llm-d-routing-sidecar (running as sidecar)
│  └─ Port 8000 (external)
└─ Container: main (vLLM decode)
   └─ Port 8001 (internal), 2 GPUs
```

**Scheduler Pod:**
```
llama-70b-kserve-router-scheduler-zzzzz-kkkkk
└─ Container: main (scheduler)
   └─ Ports: 9002, 9003, 9090
```

**Total Resources:**
- **11 pods** (2 prefill + 8 decode + 1 scheduler)
- **Prefill**: 2 pods × 8 GPUs = 16 GPUs
- **Decode**: 8 pods × 2 GPUs = 16 GPUs
- **Total**: 32 GPUs

### How Requests Work

**First Request:**
```
You
  ↓
Gateway
  ↓
Scheduler (decides: "Use decode pod 3")
  ↓
Decode Pod 3 → Routing Sidecar (port 8000)
  ↓ (No KV cache, need prefill)
  ↓
Prefill Pod 1 (port 8000)
  ↓ (Process entire prompt in parallel)
  ↓ (Generate first token + KV cache)
  ↓
Back to Decode Pod 3 → Routing Sidecar
  ↓ (Store KV cache, forward to vLLM decode)
  ↓
vLLM Decode (port 8001)
  ↓ (Generate remaining tokens sequentially)
  ↓
Stream tokens back to you
```

**Follow-up Requests (same conversation):**
```
You
  ↓
Gateway
  ↓
Scheduler (decides: "Use decode pod 3 again - has KV cache")
  ↓
Decode Pod 3 → Routing Sidecar
  ↓ (Check: Has KV cache? YES!)
  ↓ (Skip prefill, go directly to decode)
  ↓
vLLM Decode (port 8001)
  ↓ (Reuse KV cache, generate new tokens)
  ↓
Stream tokens back to you
```

### Benefits

| Aspect | Without Split | With Prefill/Decode Split |
|--------|---------------|---------------------------|
| **GPU Usage** | All GPUs always active | Prefill only when needed |
| **Scaling** | Scale everything together | Scale prefill and decode independently |
| **Cost** | Higher (more GPUs idle) | Lower (better utilization) |
| **Latency** | Same for all | First token faster (parallel prefill) |

### How to Identify Pods

```bash
# Find prefill pods
kubectl get pods -l llm-d.ai/role=prefill

# Find decode pods
kubectl get pods -l llm-d.ai/role=decode

# Find scheduler
kubectl get pods | grep scheduler
```

---

## Feature 7: Using Multiple GPUs (Parallelism)

### What It Does
Distributes your model across multiple GPUs so you can:
- Run larger models that don't fit on 1 GPU
- Process requests faster
- Handle more throughput

### Types of Parallelism

| Type | What It Does | When to Use |
|------|-------------|-------------|
| **Tensor** | Splits model layers across GPUs | Large models (13B+) |
| **Pipeline** | Splits model stages across GPUs | Very large models (40B+) |
| **Data** | Replicates model, different batches | High throughput |
| **Expert** | For Mixture-of-Experts models | MoE models only |

### How to Deploy (Tensor Parallelism)

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-70b
spec:
  model:
    uri: hf://meta-llama/Llama-3-70B-Instruct
  
  replicas: 2
  
  parallelism:
    tensor: 8  # Shard tensors within each layer across 8 GPUs
  
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "8"  # ← MUST match tensor: 8
        limits:
          nvidia.com/gpu: "8"
  
  router:
    gateway: {}
    route: {}
```

### What You'll See

```bash
$ kubectl get pods

NAME                              READY   STATUS    AGE
llama-70b-kserve-xxxxx-aaaaa      1/1     Running   5m
llama-70b-kserve-xxxxx-bbbbb      1/1     Running   5m
```

**Each pod:**
```
llama-70b-kserve-xxxxx-aaaaa
├─ Init: storage-initializer
└─ Container: main
   └─ 8 GPUs allocated
   └─ vLLM args: --tensor-parallel-size=8
```

**Inside the pod, vLLM uses 8 GPUs:**
```
GPU 0: Layers 0-9
GPU 1: Layers 10-19
GPU 2: Layers 20-29
GPU 3: Layers 30-39
GPU 4: Layers 40-49
GPU 5: Layers 50-59
GPU 6: Layers 60-69
GPU 7: Layers 70-79
```

**Total Resources:**
- **2 pods**
- **16 GPUs** (2 pods × 8 GPUs)

### ⚠️ Critical Rule

```yaml
parallelism:
  tensor: 8              # vLLM expects 8 GPUs

resources:
  requests:
    nvidia.com/gpu: "8"  # Kubernetes must allocate 8 GPUs

# THESE MUST MATCH!
```

If they don't match, vLLM will crash or not use all GPUs.

### How Requests Work

```
Request arrives at pod
  ↓
vLLM distributes computation across 8 GPUs:
  ↓
GPU 0 processes layers 0-9
GPU 1 processes layers 10-19
... (parallel processing)
GPU 7 processes layers 70-79
  ↓
Combine results
  ↓
Generate token
  ↓
Repeat for next token
```

All GPUs work together on **every request**.

---

## Feature 8: Multi-Node Deployment

### What It Does
Spreads your LLM across **multiple Kubernetes nodes** using a Leader + Workers setup.

### When to Use
- Model is too large for one node's GPUs
- Need pipeline parallelism across nodes
- Want to use all GPUs in your cluster

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-405b
spec:
  model:
    uri: hf://meta-llama/Llama-3-405B
  
  replicas: 2  # 2 leader-worker groups
  
  parallelism:
    pipeline: 4  # 4-stage pipeline
  
  # Leader (head) pod
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "8"
  
  # Worker pods
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

### What You'll See

```bash
$ kubectl get pods

NAME                                    READY   STATUS    AGE
# Group 1
llama-405b-kserve-mn-0                  1/1     Running   10m  (Leader)
llama-405b-kserve-mn-0-worker-1         1/1     Running   10m  (Worker)

# Group 2
llama-405b-kserve-mn-1                  1/1     Running   10m  (Leader)
llama-405b-kserve-mn-1-worker-1         1/1     Running   10m  (Worker)
```

**Pod Structure:**

**Leader Pod:**
```
llama-405b-kserve-mn-0
├─ Init: storage-initializer
└─ Container: main
   └─ 8 GPUs, runs Ray head
   └─ Stages 1-2 of pipeline
```

**Worker Pod:**
```
llama-405b-kserve-mn-0-worker-1
└─ Container: main
   └─ 8 GPUs, connects to Ray head
   └─ Stages 3-4 of pipeline
```

**Total Resources:**
- **4 pods** (2 leaders + 2 workers)
- **32 GPUs** (4 pods × 8 GPUs)

### How It Works

```
Request arrives at Leader Pod
  ↓
Leader: Process stages 1-2 (8 GPUs)
  ↓ (Send hidden states to Worker via Ray)
  ↓
Worker: Process stages 3-4 (8 GPUs)
  ↓ (Send results back to Leader)
  ↓
Leader: Generate final output
  ↓
Response to you
```

---

## Feature 9: Exposing Your LLM (Gateway API)

### What It Does
Makes your LLM accessible via HTTP using modern Kubernetes Gateway API.

### When to Use
- Always! You need this to access your LLM.
- Using modern Kubernetes (1.26+)
- Want advanced routing features

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B
  
  router:
    gateway: {}  # Use default gateway
    route: {}    # Controller creates HTTPRoute
```

### What You'll See

```bash
$ kubectl get llmisvc my-llm

NAME      URL                                           READY
my-llm    http://gateway.example.com/my-namespace/my-llm   True

$ kubectl get httproute

NAME                    HOSTNAMES   AGE
my-llm-kserve-route                 5m

$ kubectl describe httproute my-llm-kserve-route

Rules:
  Matches:
    Path:
      Type: PathPrefix
      Value: /my-namespace/my-llm
  Backend Refs:
    Group: inference.networking.x-k8s.io
    Kind: InferencePool
    Name: my-llm-inference-pool
    Port: 8000
  Filters:
    Type: URLRewrite
    URL Rewrite:
      Path:
        Type: ReplacePrefixMatch
        Replace Prefix Match: /
```

### How to Use

**Your LLM is available at:**
```
http://<gateway-address>/<namespace>/<llm-name>
```

Example:
```
http://gateway.example.com/production/my-llm
```

**API endpoints:**
```
/v1/models                          (List models)
/v1/chat/completions               (Chat)
/v1/completions                    (Text completion)
/v1/embeddings                     (Embeddings, if supported)
```

**Full request:**
```bash
curl -X POST \
  http://gateway.example.com/production/my-llm/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-llm",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is Kubernetes?"}
    ],
    "temperature": 0.7,
    "max_tokens": 200
  }'
```

---

## Feature 10: Using Custom Gateways

### What It Does
Lets you use your own existing Gateway instead of the default.

### When to Use
- You already have a Gateway configured
- Need custom Gateway settings
- Using Istio or other service mesh

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B
  
  router:
    gateway:
      refs:
      - name: my-custom-gateway
        namespace: istio-system
    route:
      http:
        spec:
          rules:
          - matches:
            - path:
                type: PathPrefix
                value: /api/llm/my-llm
```

### What You'll See

Your LLM will be accessible through your custom gateway at the path you specified:
```
http://my-custom-gateway.com/api/llm/my-llm
```

---

## Feature 11: Traditional Ingress

### What It Does
Uses traditional Kubernetes Ingress instead of Gateway API.

### When to Use
- Older Kubernetes clusters (pre-1.26)
- Already using Ingress
- Don't have Gateway API installed

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B
  
  router:
    ingress:
      refs:
      - name: my-ingress
```

---

## Feature 12: Smart Request Routing (Scheduler)

### What It Does
Adds an intelligent **Scheduler** (Endpoint Picker) that:
- Selects the best pod for each request
- Routes based on KV cache availability
- Balances load across pods
- Handles priority

### When to Use
- Using prefill/decode split (Feature 6)
- Have multiple replicas
- Want optimal performance
- Need intelligent routing

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: smart-llm
spec:
  model:
    uri: hf://meta-llama/Llama-3-70B
  
  prefill:
    replicas: 2
    # ... prefill config
  
  replicas: 8
  # ... decode config
  
  router:
    gateway: {}
    route: {}
    scheduler: {}  # ← Add scheduler
```

### What You'll See

```bash
$ kubectl get pods

NAME                                          READY   STATUS    AGE
smart-llm-kserve-prefill-xxxxx-aaaaa          1/1     Running   5m
smart-llm-kserve-prefill-xxxxx-bbbbb          1/1     Running   5m
smart-llm-kserve-yyyyy-ccccc                  2/2     Running   5m
smart-llm-kserve-yyyyy-ddddd                  2/2     Running   5m
# ... 6 more decode pods
smart-llm-kserve-router-scheduler-zzzzz       1/1     Running   5m  ← Scheduler pod
```

**Scheduler Pod:**
```
smart-llm-kserve-router-scheduler-zzzzz
└─ Container: main (llm-d-inference-scheduler)
   └─ Ports: 9002 (gRPC), 9003 (health), 9090 (metrics)
```

### How It Works

**Without Scheduler:**
```
Request → Gateway → Random pod (round-robin)
```

**With Scheduler:**
```
Request
  ↓
Gateway
  ↓
Scheduler analyzes:
  • Which pods are least loaded?
  • Which pod has KV cache for this conversation?
  • What's the model priority?
  ↓
Scheduler decides: "Use decode pod 3"
  ↓
Gateway → Decode Pod 3
```

### Benefits

| Metric | Without Scheduler | With Scheduler |
|--------|------------------|----------------|
| **Latency** | Variable | 20-30% lower |
| **Cache Hits** | Low | High |
| **Load Balance** | Round-robin | Intelligent |
| **Throughput** | Good | Better |

---

## Feature 13: LoRA Adapters

### What It Does
Adds Low-Rank Adaptation (LoRA) adapters to your base model for:
- Task-specific fine-tuning
- Multiple specialized versions
- Efficient model customization

### When to Use
- Need specialized versions (SQL, math, coding, etc.)
- Want efficient fine-tuning
- Multiple use cases from one base model

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-with-lora
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B
    lora:
      adapters:
      - uri: hf://user/sql-lora-adapter
        name: sql-adapter
      - uri: hf://user/math-lora-adapter
        name: math-adapter
      - uri: hf://user/code-lora-adapter
        name: code-adapter
  
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "1"
  
  router:
    gateway: {}
    route: {}
```

### What You'll See

```bash
$ kubectl logs llama-with-lora-kserve-xxxxx

INFO: Loading base model: Llama-3-8B
INFO: Loading LoRA adapter: sql-adapter from /mnt/models/adapters/sql-adapter
INFO: Loading LoRA adapter: math-adapter from /mnt/models/adapters/math-adapter
INFO: Loading LoRA adapter: code-adapter from /mnt/models/adapters/code-adapter
INFO: Server ready on port 8000
```

**Pod structure:** Same as basic deployment (1 pod, 1 container), but with adapters loaded.

### How to Use

**Request with specific adapter:**
```bash
# Use SQL adapter
curl -X POST http://gateway.../v1/chat/completions \
  -d '{
    "model": "sql-adapter",
    "messages": [{"role": "user", "content": "Generate SQL for user table"}]
  }'

# Use math adapter
curl -X POST http://gateway.../v1/chat/completions \
  -d '{
    "model": "math-adapter",
    "messages": [{"role": "user", "content": "Solve: x^2 + 5x + 6 = 0"}]
  }'

# Use base model (no adapter)
curl -X POST http://gateway.../v1/chat/completions \
  -d '{
    "model": "llama-with-lora",
    "messages": [{"role": "user", "content": "General question"}]
  }'
```

### Benefits

- **Efficiency**: One base model + small adapters vs multiple full models
- **Flexibility**: Switch adapters per request
- **Cost**: Save GPU memory and storage

---

## Feature 14: Model Priority

### What It Does
Assigns priority levels to models for resource allocation under load.

### When to Use
- Running multiple models
- Some models are more critical than others
- Need guaranteed service for important models

### Priority Levels

| Level | Behavior | Use For |
|-------|----------|---------|
| **Critical** | Always served, never preempted | Production, customer-facing |
| **Normal** | Standard priority | General use |
| **Sheddable** | Can be rejected under high load | Testing, non-critical |

### How to Deploy

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: critical-llm
spec:
  model:
    uri: hf://meta-llama/Llama-3-70B
    criticality: Critical  # ← High priority
  
  router:
    gateway: {}
    route: {}
    scheduler: {}  # Required for priority
```

### How It Works

**Under normal load:**
- All models get resources equally

**Under high load:**
```
Critical model requests    → Always processed
Normal model requests      → Processed if capacity available
Sheddable model requests   → May get HTTP 503 (Service Unavailable)
```

---

## Quick Reference Summary

### Deployment Cheat Sheet

| Scenario | Replicas | Prefill | Parallelism | Scheduler | Total Pods | Total GPUs |
|----------|----------|---------|-------------|-----------|------------|------------|
| **Simple** | 1 | No | No | No | 1 | 1 |
| **Scaled** | 3 | No | No | No | 3 | 3 |
| **Multi-GPU** | 1 | No | tensor: 8 | No | 1 | 8 |
| **Prefill/Decode** | 8 | Yes (2) | No | Yes | 11 | 10 |
| **Large Model** | 8 | Yes (2) | tensor: 4 | Yes | 11 | 40 |

### Container Count Reference

| Deployment Type | Init Containers | Running Containers | Total per Pod |
|-----------------|-----------------|-------------------|---------------|
| **Simple** | 1 (storage-init) | 1 (main) | 2 |
| **Prefill pod** | 1 (storage-init) | 1 (main) | 2 |
| **Decode pod** | 2 (storage-init, routing-sidecar) | 1 (main) | 3 total, 2 running |
| **Scheduler** | 0 | 1 (main) | 1 |

### Finding Your Pods

```bash
# All pods for an LLM
kubectl get pods -l app.kubernetes.io/name=<llm-name>

# Just prefill pods
kubectl get pods -l llm-d.ai/role=prefill

# Just decode pods
kubectl get pods -l llm-d.ai/role=decode

# Check LLM status
kubectl get llmisvc <llm-name>

# Get URL
kubectl get llmisvc <llm-name> -o jsonpath='{.status.url}'
```

---

## Troubleshooting Guide

### Pod Not Starting

**Check pod status:**
```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

**Common issues:**
- Model download taking too long (check storage-initializer logs)
- Not enough GPU resources (check node capacity)
- Image pull errors (check image name and credentials)

### Can't Access LLM

**Check URL:**
```bash
kubectl get llmisvc <llm-name> -o jsonpath='{.status.url}'
```

**Check HTTPRoute:**
```bash
kubectl get httproute
kubectl describe httproute <llm-name>-kserve-route
```

**Check Gateway:**
```bash
kubectl get gateway -A
```

### Slow Performance

**Check replica count:**
```bash
kubectl get pods -l app.kubernetes.io/name=<llm-name>
```

**Enable scheduler for better routing:**
```yaml
router:
  scheduler: {}
```

**Check GPU utilization:**
```bash
kubectl exec <pod-name> -- nvidia-smi
```

---

## Best Practices

### For Small Models (< 13B)

```yaml
replicas: 2-3
parallelism: Not needed
prefill: Not needed
scheduler: Optional
GPUs: 1 per pod
```

### For Large Models (13B-70B)

```yaml
replicas: 4-8
parallelism:
  tensor: 2-8
prefill: Yes (2-4 pods)
scheduler: Yes
GPUs: 2-8 per pod
```

### For Very Large Models (70B+)

```yaml
replicas: 8-16
parallelism:
  tensor: 8
prefill: Yes (4-8 pods)
scheduler: Yes
worker: Yes (multi-node)
GPUs: 8+ per pod
```

---

## Conclusion

You now understand all LLMD features from a user perspective! Start with simple deployments and gradually add features as needed.

### Recommended Learning Path:

1. ✅ Deploy a simple LLM (Feature 1)
2. ✅ Scale it (Feature 2)
3. ✅ Customize it (Feature 3)
4. ✅ Try prefill/decode split (Feature 6)
5. ✅ Add multi-GPU if needed (Feature 7)
6. ✅ Enable scheduler for optimization (Feature 12)

### Next Steps:

- Read `LLMD_COMPLETE_ARCHITECTURE_AND_FEATURES.md` for technical details
- Check `LLMD_E2E_TEST_REPORT.md` for validation examples
- Review `LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md` for alternatives

---

**Document Version:** 1.0  
**Last Updated:** October 13, 2025  
**Audience:** End Users, Developers, DevOps Engineers

