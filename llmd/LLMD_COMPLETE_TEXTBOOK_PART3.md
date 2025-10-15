# LLMD & KServe Complete Textbook - Part 3
## Continued from Part 2

---

## Chapter 12: vLLM Model Server

### What is vLLM?

vLLM (Very Fast LLM) is a high-throughput, memory-efficient inference engine for LLMs. It's the default runtime for LLMD and llm-d.

**Key Features:**
- **PagedAttention:** Efficient KV cache management
- **Continuous batching:** Process requests as they arrive
- **Tensor parallelism:** Scale across GPUs
- **Quantization:** Support for INT8, INT4, AWQ, GPTQ
- **OpenAI-compatible API:** Drop-in replacement
- **Prefix caching:** Reuse common prompt prefixes

**Website:** https://vllm.ai  
**GitHub:** https://github.com/vllm-project/vllm

### PagedAttention (The Secret Sauce)

Traditional KV cache management:
```
┌────────────────────────────────────────────┐
│  Traditional KV Cache (Contiguous)         │
├────────────────────────────────────────────┤
│                                            │
│  Conversation 1: [████████████░░░░░░░░░░] │ ← Fragmentation!
│  Conversation 2: [████░░░░░░░░░░░░░░░░░░] │
│  Conversation 3: [████████░░░░░░░░░░░░░░] │
│                                            │
│  Wasted space: 50%! 😱                     │
└────────────────────────────────────────────┘
```

PagedAttention (like OS virtual memory):
```
┌────────────────────────────────────────────┐
│  PagedAttention (Blocks)                   │
├────────────────────────────────────────────┤
│                                            │
│  Physical Memory (Blocks):                 │
│  [Block 0][Block 1][Block 2][Block 3]...   │
│                                            │
│  Logical Conversations:                    │
│  Conv 1: Block 0 → Block 2 → Block 5       │
│  Conv 2: Block 1 → Block 3                 │
│  Conv 3: Block 4 → Block 6 → Block 7       │
│                                            │
│  Utilization: 95%! ✅                       │
│  Can share blocks for common prefixes!     │
└────────────────────────────────────────────┘
```

**Benefits:**
- 24x higher throughput than HuggingFace Transformers
- Near-zero waste in memory
- Dynamic memory allocation
- Prefix sharing across requests

### vLLM Architecture

```
┌────────────────────────────────────────────────────┐
│  vLLM Server                                       │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │  API Server (FastAPI)                        │ │
│  │  Port 8000 (or 8001 for decode)              │ │
│  └───────────┬──────────────────────────────────┘ │
│              │                                     │
│              ▼                                     │
│  ┌──────────────────────────────────────────────┐ │
│  │  LLM Engine                                  │ │
│  │  ┌────────────────────────────────────────┐ │ │
│  │  │  Tokenizer                             │ │ │
│  │  ├────────────────────────────────────────┤ │ │
│  │  │  Scheduler                             │ │ │
│  │  │  • Continuous batching                 │ │ │
│  │  │  • Request prioritization              │ │ │
│  │  ├────────────────────────────────────────┤ │ │
│  │  │  Block Manager (PagedAttention)        │ │ │
│  │  │  • Allocate/free KV blocks            │ │ │
│  │  │  • Share prefixes                      │ │ │
│  │  ├────────────────────────────────────────┤ │ │
│  │  │  Model Executor                        │ │ │
│  │  │  • Run model forward pass              │ │ │
│  │  │  • Tensor parallel coordination        │ │ │
│  │  └────────────────────────────────────────┘ │ │
│  └───────────┬──────────────────────────────────┘ │
│              │                                     │
│              ▼                                     │
│  ┌──────────────────────────────────────────────┐ │
│  │  Model (PyTorch)                             │ │
│  │  • Llama, Mistral, Mixtral, etc.             │ │
│  │  • Loaded across GPUs (if TP > 1)            │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
```

### vLLM Configuration

**Common Arguments:**

```bash
vllm serve /path/to/model \
  # Model settings
  --model /mnt/models/llama-3-8b \
  --dtype float16 \               # or bfloat16, int8, int4
  --tokenizer-mode auto \
  
  # Serving settings
  --port 8000 \
  --host 0.0.0.0 \
  --served-model-name llama-3-8b \
  
  # GPU parallelism
  --tensor-parallel-size 2 \      # 2 GPUs
  --pipeline-parallel-size 1 \
  
  # Performance tuning
  --max-model-len 4096 \          # Max context length
  --max-num-seqs 256 \            # Max concurrent requests
  --gpu-memory-utilization 0.9 \  # Use 90% of GPU memory
  
  # KV cache
  --kv-cache-dtype auto \         # or fp8 for quantized cache
  --enable-prefix-caching \       # Reuse common prefixes
  
  # Disaggregation (if needed)
  --enable-disaggregated-serving \
  --disaggregated-mode prefill \  # or decode
```

**In Kubernetes (LLMD):**

```yaml
spec:
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      command: ["vllm", "serve"]
      args:
      - /mnt/models
      - --port=8000
      - --dtype=bfloat16
      - --tensor-parallel-size=2
      - --max-model-len=8192
      - --gpu-memory-utilization=0.9
      env:
      - name: VLLM_LOGGING_LEVEL
        value: INFO
      resources:
        requests:
          nvidia.com/gpu: "2"  # Must match tensor-parallel-size!
```

### vLLM API (OpenAI-Compatible)

**Chat Completions:**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3-8b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7,
    "max_tokens": 100,
    "stream": true
  }'
```

**Response (Streaming):**

```
data: {"id":"chat-123","object":"chat.completion.chunk","created":1234567890,"model":"llama-3-8b","choices":[{"index":0,"delta":{"role":"assistant","content":"The"},"finish_reason":null}]}

data: {"id":"chat-123","object":"chat.completion.chunk","created":1234567890,"model":"llama-3-8b","choices":[{"index":0,"delta":{"content":" capital"},"finish_reason":null}]}

data: {"id":"chat-123","object":"chat.completion.chunk","created":1234567890,"model":"llama-3-8b","choices":[{"index":0,"delta":{"content":" of"},"finish_reason":null}]}

data: {"id":"chat-123","object":"chat.completion.chunk","created":1234567890,"model":"llama-3-8b","choices":[{"index":0,"delta":{"content":" France"},"finish_reason":null}]}

data: {"id":"chat-123","object":"chat.completion.chunk","created":1234567890,"model":"llama-3-8b","choices":[{"index":0,"delta":{"content":" is"},"finish_reason":null}]}

data: {"id":"chat-123","object":"chat.completion.chunk","created":1234567890,"model":"llama-3-8b","choices":[{"index":0,"delta":{"content":" Paris"},"finish_reason":null}]}

data: {"id":"chat-123","object":"chat.completion.chunk","created":1234567890,"model":"llama-3-8b","choices":[{"index":0,"delta":{"content":"."},"finish_reason":"stop"}]}

data: [DONE]
```

**Completions (Legacy):**

```bash
curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3-8b",
    "prompt": "Once upon a time",
    "max_tokens": 50
  }'
```

**Models List:**

```bash
curl http://localhost:8000/v1/models
```

**Health Check:**

```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

### vLLM Metrics

vLLM exposes Prometheus metrics on `/metrics`:

```
# Request metrics
vllm:num_requests_running 5
vllm:num_requests_waiting 2

# Token metrics
vllm:generation_tokens_total 1234567
vllm:prompt_tokens_total 456789

# Latency metrics
vllm:time_to_first_token_seconds{quantile="0.5"} 0.150
vllm:time_to_first_token_seconds{quantile="0.9"} 0.250
vllm:time_per_output_token_seconds{quantile="0.5"} 0.030

# GPU metrics
vllm:gpu_cache_usage_perc 75.5
vllm:gpu_memory_usage_bytes{gpu="0"} 45000000000
```

---

## Chapter 13: InferencePool and InferenceModel

### What are They?

These are CRDs from the Gateway API Inference Extension that enable service discovery and model metadata for intelligent routing.

**InferencePool:**
- Lists available pods for a model
- Selector-based discovery (like Service)
- Used by Scheduler to find pods

**InferenceModel:**
- Metadata about the model
- Links to InferencePool
- Criticality, version, etc.

### InferencePool CRD

```yaml
apiVersion: inference.networking.x-k8s.io/v1alpha2
kind: InferencePool
metadata:
  name: my-llm-inference-pool
  namespace: default
spec:
  # How to find pods
  selector:
    matchLabels:
      app.kubernetes.io/name: my-llm
      kserve.io/component: workload
  
  # Which port to use
  targetPortNumber: 8000
  
  # ExtProc configuration (points to Scheduler)
  extensionRef:
    group: ""
    kind: Service
    name: my-llm-epp-service
    namespace: default
    failureMode: FailOpen  # Continue even if scheduler fails

status:
  # Controller populates this
  targets:
  - name: my-llm-kserve-workload-abc123
    address: 10.244.1.5
    port: 8000
    ready: true
    metadata:
      role: decode
      sessions: ["sess-1", "sess-2"]
  
  - name: my-llm-kserve-workload-def456
    address: 10.244.1.6
    port: 8000
    ready: true
    metadata:
      role: decode
      sessions: ["sess-3"]
  
  - name: my-llm-kserve-prefill-ghi789
    address: 10.244.1.7
    port: 8000
    ready: true
    metadata:
      role: prefill
```

**How it works:**

```
1. InferencePool controller watches Pods
   
2. Finds pods matching selector:
   app.kubernetes.io/name: my-llm
   
3. Filters to ready pods
   
4. Populates status.targets with:
   • Pod name
   • IP address
   • Port
   • Readiness
   • Metadata (from labels/annotations)
   
5. Scheduler queries InferencePool:
   GET /apis/inference.networking.x-k8s.io/v1alpha2/
       namespaces/default/inferencepools/my-llm-inference-pool
   
6. Scheduler gets list of available pods
   
7. Scheduler applies scoring and selects best pod
```

### InferenceModel CRD

```yaml
apiVersion: inference.networking.x-k8s.io/v1alpha2
kind: InferenceModel
metadata:
  name: my-llm
  namespace: default
spec:
  # Model name (for API requests)
  modelName: llama-3-8b
  
  # Link to InferencePool
  poolRef:
    group: inference.networking.x-k8s.io
    kind: InferencePool
    name: my-llm-inference-pool
  
  # Scheduling priority
  criticality: Critical  # or Normal, Sheddable
  
  # Optional metadata
  version: "1.0"
  framework: "vllm"
  
status:
  # Controller updates
  ready: true
  poolReady: true
  endpointCount: 10
```

**Criticality Levels:**

| Level | Priority | Behavior |
|-------|----------|----------|
| Critical | Highest | Always served, never preempted |
| Normal | Medium | Standard priority |
| Sheddable | Lowest | Can be rejected under high load |

**How Scheduler uses InferenceModel:**

```
Request arrives: {model: "llama-3-8b"}

1. Scheduler looks up InferenceModel:
   modelName == "llama-3-8b"
   
2. Get criticality: Critical
   
3. Follow poolRef to InferencePool:
   name: my-llm-inference-pool
   
4. Get list of pods from InferencePool
   
5. Apply criticality boost to scoring:
   if criticality == Critical:
     score += 100
   
6. Select best pod
```

### Integration with HTTPRoute

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: my-llm-route
spec:
  parentRefs:
  - name: llm-gateway
    namespace: istio-system
  
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /default/my-llm
    
    # Backend is InferencePool (not Service!)
    backendRefs:
    - group: inference.networking.x-k8s.io
      kind: InferencePool  # ← Points to InferencePool
      name: my-llm-inference-pool
      port: 8000
```

**Why InferencePool instead of Service?**

| Aspect | Service | InferencePool |
|--------|---------|---------------|
| Discovery | Static endpoints | Dynamic pod list |
| Load balancing | Round-robin | Intelligent (via Scheduler) |
| Metadata | No | Yes (sessions, load, etc.) |
| ExtProc integration | No | Yes |
| Filtering | No | Yes (prefill vs decode) |

---

## Chapter 14: GPU Parallelism Strategies

### The Four Types of Parallelism

When a model doesn't fit on one GPU or you need more throughput, you distribute the workload:

**1. Tensor Parallelism (TP)**
```
Split each layer across GPUs

Example: Llama-70B, TP=8
┌─────────────────────────────────────┐
│  Layer 0 (Embedding)                │
│  Split across GPU 0-7               │
│  Each GPU: 1/8 of embeddings        │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Layer 1 (Attention)                │
│  Q, K, V matrices split 8 ways      │
│  All-reduce after computation       │
└─────────────────────────────────────┘
         ↓
    ... (repeat for all layers)
```

**When to use:**
- Model too big for 1 GPU
- Want lower latency (more parallel compute)
- GPUs on same host (fast interconnect)

**2. Pipeline Parallelism (PP)**
```
Split layers across GPUs/hosts

Example: 80-layer model, PP=4
┌─────────────────┐
│ GPU 0: Layer 0-19│ ← Stage 1
└────────┬────────┘
         │ Pass activations
┌────────▼────────┐
│ GPU 1: Layer 20-39│ ← Stage 2
└────────┬────────┘
         │
┌────────▼────────┐
│ GPU 2: Layer 40-59│ ← Stage 3
└────────┬────────┘
         │
┌────────▼────────┐
│ GPU 3: Layer 60-79│ ← Stage 4
└─────────────────┘
```

**When to use:**
- Model spans multiple hosts
- GPUs have slower interconnect
- Combine with TP for very large models

**3. Data Parallelism (DP)**
```
Replicate full model, different requests

┌─────────────────┐  ┌─────────────────┐
│ GPU 0: Full model│  │ GPU 1: Full model│
│ Request A        │  │ Request B        │
└─────────────────┘  └─────────────────┘

For inference: Independent replicas
For training: Synchronize gradients
```

**When to use:**
- Need higher throughput
- Model fits on one GPU
- Have many GPUs available

**4. Expert Parallelism (EP)**
```
For Mixture-of-Experts (MoE) models

Router decides which experts to use:
┌─────────────────────────────────────┐
│  Token: "Hello"                     │
└────────┬────────────────────────────┘
         │
         ▼
    [Router]
         │
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
 Expert 0  Expert 1  Expert 2  Expert 3
 (GPU 0)   (GPU 1)   (GPU 2)   (GPU 3)
    │         │
    └────┬────┘
         ▼
     Output
```

**When to use:**
- MoE models (Mixtral, DeepSeek)
- Combine with TP/DP
- Need massive scale

### Combining Parallelism

Real deployments often combine strategies:

**Example: Llama-70B on 32 GPUs**

```
Configuration:
  TP = 8  (tensor parallel)
  DP = 4  (data parallel)
  Total GPUs: 8 × 4 = 32

Layout:
┌──────────────────────────────────────────┐
│  Data Parallel Group 0 (TP=8)            │
│  GPUs 0-7: Full model sharded 8 ways     │
│  Serves Request A                        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Data Parallel Group 1 (TP=8)            │
│  GPUs 8-15: Full model sharded 8 ways    │
│  Serves Request B                        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Data Parallel Group 2 (TP=8)            │
│  GPUs 16-23: Full model sharded 8 ways   │
│  Serves Request C                        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Data Parallel Group 3 (TP=8)            │
│  GPUs 24-31: Full model sharded 8 ways   │
│  Serves Request D                        │
└──────────────────────────────────────────┘

Throughput: 4 concurrent requests
Latency: Same as TP=8 (parallelism within group)
```

**Example: Mixtral-8x7B on 16 GPUs**

```
Configuration:
  TP = 2  (tensor parallel)
  EP = 8  (8 experts, 1 per pair of GPUs)
  Total GPUs: 2 × 8 = 16

Layout:
Each expert on 2 GPUs (TP=2):
┌─────────────┬─────────────┐
│ GPU 0       │ GPU 1       │ → Expert 0
├─────────────┼─────────────┤
│ GPU 2       │ GPU 3       │ → Expert 1
├─────────────┼─────────────┤
│ GPU 4       │ GPU 5       │ → Expert 2
├─────────────┼─────────────┤
│ ...         │ ...         │
├─────────────┼─────────────┤
│ GPU 14      │ GPU 15      │ → Expert 7
└─────────────┴─────────────┘

Router activates top-K experts per token
```

### LLMD Configuration for Parallelism

**Simple TP:**

```yaml
spec:
  parallelism:
    tensor: 4  # 4-way tensor parallel
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "4"  # MUST match TP!
```

**TP + PP (Multi-node):**

```yaml
spec:
  parallelism:
    tensor: 4
    pipeline: 2  # 2 stages
  
  # Leader pod (stage 1)
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "4"
  
  # Worker pod (stage 2)
  worker:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "4"

# Creates: 2 pods per replica (leader + worker)
# Each pod: 4 GPUs
# Total: 8 GPUs per replica
```

**Disaggregated with Different Parallelism:**

```yaml
spec:
  # Prefill: High TP for parallel processing
  prefill:
    replicas: 2
    parallelism:
      tensor: 8
    template:
      containers:
      - name: main
        resources:
          requests:
            nvidia.com/gpu: "8"
  
  # Decode: Lower TP, more replicas for throughput
  replicas: 16
  parallelism:
    tensor: 1
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "1"
```

### Choosing Parallelism Strategy

**Decision Matrix:**

| Model Size | GPUs per Host | Strategy | Example |
|------------|---------------|----------|---------|
| < 13B | 1-2 | None or TP=2 | Llama-7B: 1 GPU |
| 13B-30B | 2-4 | TP=2-4 | Llama-13B: TP=2 |
| 30B-70B | 4-8 | TP=4-8 | Llama-70B: TP=8 |
| 70B-200B | 8-16 | TP=8 + PP=2 | Llama-70B × 2 hosts |
| > 200B | 16+ | TP=8 + PP=4+ | Llama-405B: Multi-host |
| MoE (8x7B) | 16 | TP=2 + EP=8 | Mixtral-8x7B |

**Rule of Thumb:**
- **TP first:** Use TP to fit model on available GPUs
- **PP second:** Use PP if model spans hosts
- **DP last:** Use DP (more replicas) for throughput
- **EP:** Only for MoE models

---

## Chapter 15: Multi-Node Deployments

### When Do You Need Multi-Node?

Multi-node deployment is required when:
- Model doesn't fit on GPUs of a single host
- Need pipeline parallelism across hosts
- Want to distribute across different GPU types

**Example Scenarios:**
- Llama-405B: Too big for 8×H100 (even with TP=8)
- High availability: Spread across availability zones
- Cost optimization: Mix GPU types (some hosts with more GPUs)

### LeaderWorkerSet

LeaderWorkerSet (LWS) is a Kubernetes controller that manages groups of pods with leader-worker relationships.

**GitHub:** https://github.com/kubernetes-sigs/lws

**Why LWS?**
- Coordinates multi-pod deployments
- Provides pod-to-pod discovery
- Handles rolling updates gracefully
- Integrates with Kubernetes primitives

### LWS Architecture

```
┌────────────────────────────────────────────────────┐
│  LeaderWorkerSet: my-llm-mn                        │
│  Replicas: 2 (creates 2 groups)                    │
└────────────────────────────────────────────────────┘
         │
         ├─────────────────────┬─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Group 0         │   │ Group 1         │   │ Group 2 (future)│
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                     │
    ┌────┴────┐           ┌────┴────┐
    ▼         ▼           ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Leader  │ │Worker  │ │Leader  │ │Worker  │
│Pod 0   │ │Pod 0-1 │ │Pod 1   │ │Pod 1-1 │
└────────┘ └────────┘ └────────┘ └────────┘
```

**Group Composition:**
- 1 Leader pod
- N Worker pods (N ≥ 1)
- All pods in group coordinate via environment variables

**Pod Naming:**
```
Leader:  <lws-name>-<group-index>
Worker:  <lws-name>-<group-index>-worker-<worker-index>

Example:
  my-llm-mn-0           (leader, group 0)
  my-llm-mn-0-worker-1  (worker, group 0)
  my-llm-mn-0-worker-2  (worker, group 0)
  my-llm-mn-1           (leader, group 1)
  my-llm-mn-1-worker-1  (worker, group 1)
```

### LWS Environment Variables

LWS injects environment variables for pod discovery:

```yaml
env:
# Leader address
- name: LWS_LEADER_ADDRESS
  value: "my-llm-mn-0.my-llm-mn-svc.default.svc.cluster.local"

# Worker index (0 for leader, 1+ for workers)
- name: LWS_WORKER_INDEX
  value: "0"

# Total workers in group
- name: LWS_GROUP_SIZE
  value: "3"

# Group index
- name: LWS_GROUP_INDEX
  value: "0"
```

**Usage in vLLM:**

```bash
# Leader pod
if [ "$LWS_WORKER_INDEX" = "0" ]; then
  # Start vLLM as leader (Ray head)
  vllm serve /mnt/models \
    --tensor-parallel-size=4 \
    --pipeline-parallel-size=2 \
    --distributed-executor-backend=ray
else
  # Start vLLM as worker (Ray worker)
  ray start --address=${LWS_LEADER_ADDRESS}:6379
  vllm serve /mnt/models \
    --tensor-parallel-size=4 \
    --pipeline-parallel-size=2 \
    --distributed-executor-backend=ray
fi
```

### LLMD Multi-Node Configuration

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-405b
spec:
  model:
    uri: hf://meta-llama/Llama-3-405B
  
  # Number of leader-worker groups
  replicas: 2
  
  # Parallelism (applied across leader + workers)
  parallelism:
    tensor: 8
    pipeline: 4  # 4 stages across 2 pods (leader + worker)
  
  # Leader pod configuration
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:latest
      resources:
        requests:
          nvidia.com/gpu: "8"  # 8 GPUs on leader
      env:
      - name: VLLM_PIPELINE_STAGE
        value: "0-1"  # Stages 0-1 on leader
  
  # Worker pod configuration
  worker:
    containers:
    - name: main
      image: vllm/vllm-openai:latest
      resources:
        requests:
          nvidia.com/gpu: "8"  # 8 GPUs on worker
      env:
      - name: VLLM_PIPELINE_STAGE
        value: "2-3"  # Stages 2-3 on worker
```

**What gets created:**

```
LeaderWorkerSet: llama-405b-kserve-mn
  replicas: 2
  
  Group 0:
    llama-405b-kserve-mn-0 (leader)
      • 8 GPUs
      • Pipeline stages 0-1
      • Ray head node
    
    llama-405b-kserve-mn-0-worker-1
      • 8 GPUs
      • Pipeline stages 2-3
      • Ray worker node
  
  Group 1:
    llama-405b-kserve-mn-1 (leader)
      • 8 GPUs
      • Pipeline stages 0-1
      • Ray head node
    
    llama-405b-kserve-mn-1-worker-1
      • 8 GPUs
      • Pipeline stages 2-3
      • Ray worker node

Total: 4 pods, 32 GPUs
Each group serves requests independently (DP=2)
```

### Request Flow in Multi-Node

```
Client Request
  │
  ▼
Gateway
  │
  ▼
Service (targets leaders only)
  │
  ├─→ Leader Pod 0 (receives request)
  │   │
  │   ├─ Process stages 0-1 (GPUs 0-7)
  │   ├─ Send activations to Worker 0-1
  │   │
  │   ▼
  │   Worker Pod 0-1
  │   │
  │   ├─ Process stages 2-3 (GPUs 8-15)
  │   ├─ Send result back to Leader
  │   │
  │   ▼
  │   Leader Pod 0 (generates response)
  │   │
  │   └─→ Response to client
  │
  └─→ Leader Pod 1 (serves different request)
```

---

*Due to length constraints, I'll create one more comprehensive final part with hands-on labs, troubleshooting, and all remaining sections...*


