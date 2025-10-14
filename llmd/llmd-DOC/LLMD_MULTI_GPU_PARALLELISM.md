# LLMD Multi-GPU Parallelism Guide

**Component:** LLMInferenceService (LLMD)  
**Feature:** Multi-GPU Distribution for Prefill & Decode  
**Date:** October 12, 2025

---

## 🎯 Short Answer

**YES!** Both Prefill and Decode can be distributed across multiple GPUs using **4 types of parallelism**:

1. **Tensor Parallelism** - Shard tensors within each layer across GPUs
2. **Pipeline Parallelism** - Split model stages across GPUs  
3. **Data Parallelism** - Replicate model, split batches
4. **Expert Parallelism** - For MoE (Mixture of Experts) models

---

## 📊 ParallelismSpec API

```go
type ParallelismSpec struct {
    // Tensor parallelism size
    Tensor *int32 `json:"tensor,omitempty"`
    
    // Pipeline parallelism size
    Pipeline *int32 `json:"pipeline,omitempty"`
    
    // Data parallelism size
    Data *int32 `json:"data,omitempty"`
    
    // Data local parallelism size
    DataLocal *int32 `json:"dataLocal,omitempty"`
    
    // Data parallelism RPC port
    DataRPCPort *int32 `json:"dataRPCPort,omitempty"`
    
    // Expert parallelism (for MoE models)
    Expert bool `json:"expert,omitempty"`
}
```

**You can configure these SEPARATELY for Prefill and Decode!**

---

## 🔀 Type 1: Tensor Parallelism

**Best for:** Large models that don't fit in single GPU memory

### How It Works

```
┌────────────────────────────────────────────────────────────────┐
│              SINGLE GPU (Model doesn't fit)                    │
└────────────────────────────────────────────────────────────────┘

Model: 70B parameters (140GB)
GPU Memory: 80GB
Result: ❌ OUT OF MEMORY!


┌────────────────────────────────────────────────────────────────┐
│           TENSOR PARALLELISM (Split across 4 GPUs)             │
└────────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   GPU 0                                                            │
│                                                                    │
│  Layers                                                            │
│  1-10                                                              │
│  (1/4 width)                                                       │
│                                                                    │
│  35GB used                                                         │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
       ↓                 ↓                 ↓                 ↓
       └─────────────────┴─────────────────┴─────────────────┘
                              │
                    All-reduce (combine results)
                              │
                         Output token
```

**Each GPU holds 1/4 of the model weights for EACH layer**

### Configuration

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama2-70b-tensor-parallel
spec:
  model:
    uri: hf://meta-llama/Llama-2-70b-chat-hf
  
  # Prefill with tensor parallelism
  prefill:
    replicas: 1                    # 1 pod
    parallelism:
      tensor: 8                    # 8 GPUs per pod
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "8"   # Request 8 GPUs
          limits:
            nvidia.com/gpu: "8"
  
  # Decode with tensor parallelism
  replicas: 2                      # 2 pods
  parallelism:
    tensor: 4                      # 4 GPUs per pod
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          nvidia.com/gpu: "4"     # Request 4 GPUs
        limits:
          nvidia.com/gpu: "4"
```

**Result:**
- Prefill: 1 pod × 8 GPUs = **8 GPUs** (process large batches fast)
- Decode: 2 pods × 4 GPUs = **8 GPUs** (more instances for throughput)
- Total: **16 GPUs**

### vLLM Args Generated

```bash
# Prefill pod:
vllm serve /mnt/models \
  --tensor-parallel-size=8 \
  --port=8000

# Decode pod:
vllm serve /mnt/models \
  --tensor-parallel-size=4 \
  --port=8001
```

---

## 🔗 Type 2: Pipeline Parallelism

**Best for:** Very large models + multi-node setups

### How It Works

```
┌────────────────────────────────────────────────────────────────┐
│         PIPELINE PARALLELISM (Split stages across GPUs)        │
└────────────────────────────────────────────────────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   GPU 0                                                      │
│                                                              │
│  Layers 1-13                                                 │
│  (Stage 1)                                                   │
│                                                              │
│  Embedding                                                   │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
│                                                              │
    Token batch            KV cache             KV cache
│ ──────────────────►                                          │
│                                                  │
│◄────────────────────                             │
│                                                    │
    Gradients (training)   Gradients           Gradients


Pipeline execution:
  Batch 1: [GPU 0] ──────────► [GPU 1] ──────────► [GPU 2]
  Batch 2:         [GPU 0] ──────────► [GPU 1] ──────────► [GPU 2]
  Batch 3:                     [GPU 0] ──────────► [GPU 1] ──────────►
```

**Each GPU holds different layers (stages) of the model**

### Configuration

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama2-70b-pipeline
spec:
  model:
    uri: hf://meta-llama/Llama-2-70b-chat-hf
  
  # Prefill with pipeline parallelism + multi-node
  prefill:
    replicas: 1
    parallelism:
      pipeline: 4              # 4-stage pipeline
      tensor: 2                # 2-way tensor parallel per stage
                               # Total: 4 × 2 = 8 GPUs
    template:                  # Head node (Stage 0)
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "2"
    
    worker:                    # Worker nodes (Stages 1-3)
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "2"
  
  # Decode (simpler, fewer stages)
  replicas: 2
  parallelism:
    pipeline: 2
    tensor: 2                  # Total: 2 × 2 = 4 GPUs per pod
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          nvidia.com/gpu: "2"
  worker:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          nvidia.com/gpu: "2"
```

**Result:**
- Prefill: 1 cluster (4 stages × 2 GPUs) = **8 GPUs**
- Decode: 2 clusters (2 stages × 2 GPUs each) = **8 GPUs**
- Total: **16 GPUs**

---

## 🔄 Type 3: Data Parallelism

**Best for:** High throughput with many concurrent requests

### How It Works

```
┌────────────────────────────────────────────────────────────────┐
│      DATA PARALLELISM (Replicate model, split batches)         │
└────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              Complete Model (Replicated 4 times)             │
└──────────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Replica 0                                                                    │
│   (GPU 0-1)                                                                    │
│                                                                                │
│  Full Model                                                                    │
│  TP=2                                                                          │
│                                                                                │
│  Batch 1                                                                       │
│  Req 1-8                                                                       │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
        ↓                    ↓                    ↓                    ↓
    Results 1-8         Results 9-16        Results 17-24        Results 25-32

All replicas process different batches IN PARALLEL!
4× throughput compared to single replica
```

**Each replica holds the full model and processes different data**

### Configuration

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama2-13b-data-parallel
spec:
  model:
    uri: hf://meta-llama/Llama-2-13b-chat-hf
  
  # Prefill with data parallelism
  prefill:
    replicas: 1
    parallelism:
      tensor: 2                # 2-way tensor parallel per replica
      data: 4                  # 4 data parallel replicas
      dataLocal: 2             # 2 replicas per node
      dataRPCPort: 5555        # Port for inter-replica communication
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "2"
    worker:                    # Workers for data parallelism
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "2"
  
  # Decode with data parallelism
  replicas: 2
  parallelism:
    tensor: 1
    data: 2
    dataLocal: 2
```

**Result:**
- Prefill: 4 replicas × 2 GPUs = **8 GPUs** (4× throughput)
- Decode: 2 pods × 2 replicas × 1 GPU = **4 GPUs**
- Total: **12 GPUs**

### vLLM Args Generated

```bash
# Prefill leader pod:
vllm serve /mnt/models \
  --tensor-parallel-size=2 \
  --data-parallel-size=4 \
  --data-parallel-size-local=2 \
  --data-parallel-address=$(LWS_LEADER_ADDRESS) \
  --data-parallel-rpc-port=5555

# Prefill worker pods (headless):
vllm serve /mnt/models \
  --tensor-parallel-size=2 \
  --data-parallel-size=4 \
  --data-parallel-size-local=2 \
  --data-parallel-address=$(LWS_LEADER_ADDRESS) \
  --data-parallel-rpc-port=5555 \
  --headless
```

---

## 🧠 Type 4: Expert Parallelism

**Best for:** Mixture of Experts (MoE) models like Mixtral

### How It Works

```
┌────────────────────────────────────────────────────────────────┐
│    EXPERT PARALLELISM (For MoE models like Mixtral 8×7B)       │
└────────────────────────────────────────────────────────────────┘

MoE Model: 8 experts, each 7B parameters

┌────────────────────────────────────────────────────────────────┐
│                    Router (Gating Network)                     │
│              "Which experts should handle this?"               │
└──────────────┬────────────┬────────────┬────────────┬──────────┘
│                                                                │
       ┌───────▼────┐ ┌────▼─────┐ ┌───▼──────┐ ┌───▼──────┐
│ Expert 0-1                                        │
│  (GPU 0)                                          │
       └────────────┘ └──────────┘ └──────────┘ └──────────┘
            ↓              ↓            ↓            ↓
       Process token  Process token Process token Process token
            ↓              ↓            ↓            ↓
       ┌────┴──────────────┴────────────┴────────────┴────┐
│              Combine Expert Outputs              │
│                  Final Token                     │
└──────────────────────────────────────────────────┘

Each GPU holds 2 experts (distributed)
Only activated experts compute (sparse MoE)
```

### Configuration

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: mixtral-8x7b-expert-parallel
spec:
  model:
    uri: hf://mistralai/Mixtral-8x7B-Instruct-v0.1
  
  # Prefill with expert + tensor parallelism
  prefill:
    replicas: 1
    parallelism:
      expert: true             # Enable expert parallelism
      tensor: 4                # 4-way tensor parallel
                               # Total: 4 GPUs (2 experts per GPU)
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "4"
  
  # Decode with expert parallelism
  replicas: 2
  parallelism:
    expert: true
    tensor: 2
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          nvidia.com/gpu: "2"
```

### vLLM Args Generated

```bash
# With expert parallelism:
vllm serve /mnt/models \
  --enable-expert-parallel \
  --tensor-parallel-size=4 \
  --port=8000
```

---

## 🎯 Complete Example: All Parallelism Types Combined

### Use Case: Ultra-Large Model (175B+ parameters)

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: gpt-175b-ultimate
spec:
  model:
    uri: s3://models/gpt-175b
  
  # PREFILL: Maximum parallelism for fast prompt processing
  prefill:
    replicas: 1                          # 1 multi-node cluster
    parallelism:
      tensor: 8                          # 8-way tensor parallel
      pipeline: 4                        # 4-stage pipeline
      data: 2                            # 2 data parallel replicas
      # Total: 8 × 4 × 2 = 64 GPUs for prefill!
    
    template:                            # Head node
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "8"          # Stage 0: 8 GPUs
    
    worker:                              # Worker nodes (stages 1-3)
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "8"          # Each stage: 8 GPUs
  
  # DECODE: Optimized for throughput
  replicas: 4                            # 4 multi-node clusters
  parallelism:
    tensor: 4                            # 4-way tensor parallel
    pipeline: 2                          # 2-stage pipeline
    # Total: 4 × 2 × 4 = 32 GPUs for decode!
  
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          nvidia.com/gpu: "4"
  
  worker:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          nvidia.com/gpu: "4"
  
  router:
    route:
      http: {}
    scheduler:
      pool: {}
```

**Resource Allocation:**
```
Prefill:  64 GPUs (1 cluster × 8 TP × 4 PP × 2 DP)
Decode:   32 GPUs (4 clusters × 4 TP × 2 PP)
Total:    96 GPUs!

Characteristics:
  • Prefill: Massive parallel processing (64 GPUs work together)
  • Decode: 4 independent clusters (high throughput)
  • Can process: 100+ concurrent users
  • Latency: <100ms TTFT, ~50 tokens/sec per user
```

---

## 📊 Comparison Matrix

| Parallelism Type | Model Distribution | Use Case | Communication Overhead | Complexity |
|------------------|-------------------|----------|------------------------|------------|
| **Tensor** | Shard tensors within each layer | Large models (>40GB) | High (all-reduce) | Medium |
| **Pipeline** | Split stages across GPUs | Very large models + multi-node | Medium (point-to-point) | High |
| **Data** | Replicate full model | High throughput | Low (independent) | Low |
| **Expert** | Distribute experts | MoE models only | Medium (sparse) | Medium |

---

## 🎯 Choosing the Right Parallelism

### Decision Tree

```
Is your model > 80GB?
  ├─ YES → Use Tensor Parallelism (TP)
  │         ├─ Model > 200GB?
│                           │
  │         └─ High throughput needed?
  │             └─ YES → Add Data Parallelism (TP + DP)
  │
  └─ NO → Use Data Parallelism for throughput
            └─ Need > 100 req/sec?
                └─ YES → Increase DP replicas

Is this a MoE model (Mixtral, etc.)?
  └─ YES → Enable Expert Parallelism + TP
```

### Real-World Examples

#### Small Model (7B) - High Throughput

```yaml
prefill:
  replicas: 1
  parallelism:
    tensor: 1      # Single GPU fits model
    data: 4        # 4 replicas for throughput
  # Total: 4 GPUs

replicas: 8
parallelism:
  tensor: 1
  data: 2
# Total: 16 GPUs (8 pods × 2 replicas)
```

#### Medium Model (13B-30B) - Balanced

```yaml
prefill:
  replicas: 1
  parallelism:
    tensor: 2      # 2 GPUs per replica (model split)
    data: 2        # 2 replicas
  # Total: 4 GPUs

replicas: 4
parallelism:
  tensor: 2
# Total: 8 GPUs (4 pods × 2 TP)
```

#### Large Model (70B) - Memory Constrained

```yaml
prefill:
  replicas: 1
  parallelism:
    tensor: 8      # 8 GPUs to fit model
  # Total: 8 GPUs

replicas: 2
parallelism:
  tensor: 4        # 4 GPUs per pod
# Total: 8 GPUs (2 pods × 4 TP)
```

#### Ultra-Large Model (175B+) - Everything

```yaml
prefill:
  replicas: 1
  parallelism:
    tensor: 8
    pipeline: 4
    data: 2
  # Total: 64 GPUs (8 TP × 4 PP × 2 DP)

replicas: 4
parallelism:
  tensor: 4
  pipeline: 2
# Total: 32 GPUs (4 pods × 4 TP × 2 PP)
```

---

## 🚀 Performance Implications

### Prefill Phase

| Configuration | GPUs | Prompt Tokens/Sec | Batch Size | TTFT* |
|---------------|------|-------------------|------------|-------|
| Single GPU | 1 | 2,000 | 1 | 500ms |
| TP=4 | 4 | 6,000 | 4 | 150ms |
| TP=8 | 8 | 10,000 | 8 | 80ms |
| TP=8, DP=4 | 32 | 40,000 | 32 | 80ms |

*TTFT = Time To First Token

### Decode Phase

| Configuration | GPUs | Tokens/Sec/User | Concurrent Users | Total Throughput |
|---------------|------|-----------------|------------------|------------------|
| Single GPU | 1 | 50 | 10 | 500 tok/s |
| TP=2 | 2 | 45 | 20 | 900 tok/s |
| DP=4, TP=1 | 4 | 50 | 40 | 2,000 tok/s |
| TP=4, Pods=4 | 16 | 40 | 80 | 3,200 tok/s |

---

## ⚠️ Important Considerations

### 1. **GPU Requirements**

```yaml
# You MUST request GPUs in pod spec!
template:
  containers:
  - name: main
    resources:
      requests:
        nvidia.com/gpu: "4"    # Must match parallelism config
      limits:
        nvidia.com/gpu: "4"
```

### 2. **Shared Memory**

For multi-GPU, increase shared memory:

```yaml
template:
  volumes:
  - name: dshm
    emptyDir:
      medium: Memory
      sizeLimit: 16Gi          # Increase for multi-GPU
  containers:
  - name: main
    volumeMounts:
    - name: dshm
      mountPath: /dev/shm
```

### 3. **Network Requirements**

- **Tensor/Pipeline Parallelism:** Needs high-bandwidth GPU interconnect (NVLink, InfiniBand)
- **Data Parallelism:** Can work with standard networking
- **Multi-Node:** Requires fast inter-node networking

### 4. **Cost Optimization**

```
Prefill (compute-intensive):
  ✅ High GPU count (TP=8)
  ✅ Few replicas (1-2)
  ✅ Maximize GPU utilization

Decode (memory-intensive):
  ✅ Lower GPU count per pod (TP=1-2)
  ✅ Many replicas (4-8+)
  ✅ Better throughput/cost ratio
```

---

## 📚 Summary

### Key Takeaways

1. **YES, both Prefill and Decode support multi-GPU**
   - Configure independently using `parallelism` spec
   
2. **4 types of parallelism available**
   - Tensor: Split layers
   - Pipeline: Split stages
   - Data: Replicate model
   - Expert: MoE models
   
3. **Can combine multiple types**
   - Example: TP=8, PP=4, DP=2 = 64 GPUs!
   
4. **Different strategies for Prefill vs Decode**
   - Prefill: More GPUs per pod (TP=8)
   - Decode: More pods with fewer GPUs (TP=1-2, many replicas)

5. **Configuration is separate**
   ```yaml
   prefill:
     parallelism:
       tensor: 8    # Prefill uses 8 GPUs
   
   parallelism:      # Top-level = decode
     tensor: 2       # Decode uses 2 GPUs
   ```

---

## 🔗 References

- **ParallelismSpec:** `pkg/apis/serving/v1alpha1/llm_inference_service_types.go:242`
- **Config Templates:** `config/llmisvc/config-llm-*-worker-*.yaml`
- **vLLM Parallelism Docs:** https://docs.vllm.ai/en/latest/serving/distributed_serving.html

---

**Document Version:** 1.0  
**Date:** October 12, 2025

