# LLM-D Deployment - Complete Advanced Guide

## 📋 Table of Contents
1. [What is LLM-D Mode](#what-is-llm-d-mode)
2. [When to Use LLM-D](#when-to-use-llm-d)
3. [Complete Architecture](#complete-architecture)
4. [All 5 Components Explained](#all-5-components-explained)
5. [Prefill/Decode Disaggregation](#prefill-decode-disaggregation)
6. [KV-Cache Optimization](#kv-cache-optimization)
7. [Multi-Node Distributed Inference](#multi-node-distributed-inference)
8. [Intelligent Autoscaling](#intelligent-autoscaling) **(NEW!)**
9. [Complete Request Flows](#complete-request-flows)
10. [Configuration Examples](#configuration-examples)
11. [Performance & Cost Benefits](#performance--cost-benefits)
12. [Troubleshooting](#troubleshooting)

---

## What is LLM-D Mode

### Simple Explanation

LLM-D (Large Language Model - Distributed) is an **advanced deployment mode** specifically optimized for serving large language models. It adds intelligent routing, caching, and distributed inference capabilities on top of standard Kubernetes deployments.

### Key Value Proposition

```mermaid
flowchart LR
    subgraph "Without LLM-D"
        Normal[Standard Deployment<br/>- Random routing<br/>- No cache awareness<br/>- Single-node only<br/>- Basic load balancing]
    end
    
    subgraph "With LLM-D"
        LLMD[LLM-D Deployment<br/>✅ Cache-aware routing<br/>✅ 10x faster repeats<br/>✅ Multi-node support<br/>✅ P/D optimization<br/>✅ Load-aware routing]
    end
    
    Normal -->|Upgrade| LLMD
    
    style Normal fill:#ffccbc
    style LLMD fill:#a5d6a7
```

### What Makes LLM-D Special

- **Cache-Aware Routing**: Routes requests to pods with cached KV data (10x speedup)
- **Disaggregated P/D**: Separates prefill and decode stages for optimization
- **Distributed Inference**: Splits large models across multiple GPUs/nodes
- **Load-Aware Balancing**: Intelligent load distribution
- **Real-Time Optimization**: Continuously optimizes routing decisions

---

## When to Use LLM-D

### Decision Flowchart

```mermaid
flowchart TB
    Start{Deploying<br/>LLM?} --> Size{Model<br/>Size?}
    
    Size -->|< 7B params| Small[Small LLM<br/>< 20GB]
    Size -->|7B - 70B| Medium[Medium LLM<br/>20-140GB]
    Size -->|> 70B| Large[Large LLM<br/>> 140GB]
    
    Small --> Features{Need Advanced<br/>Features?}
    Features -->|Cache Optimization| YesLLMD1[✅ Use LLM-D]
    Features -->|Multi-turn Chats| YesLLMD1
    Features -->|Cost Optimization| YesLLMD1
    Features -->|No| Maybe[⚠️ Consider Serverless<br/>Simpler Setup]
    
    Medium --> SingleNode{Fits Single<br/>Node?}
    SingleNode -->|Yes| YesLLMD2[✅ Use LLM-D<br/>Tensor Parallel]
    SingleNode -->|No| YesLLMD3[✅ Use LLM-D<br/>Multi-Node]
    
    Large --> YesLLMD4[✅ MUST Use LLM-D<br/>Multi-Node Required]
    
    YesLLMD1 --> Benefits[Get:<br/>- Cache speedup<br/>- Session affinity<br/>- Load balancing<br/>- Cost reduction]
    YesLLMD2 --> Benefits
    YesLLMD3 --> Benefits
    YesLLMD4 --> Benefits
    
    Maybe --> Eval[Evaluate:<br/>- Traffic pattern<br/>- Cache hit rate<br/>- Cost sensitivity]
    
    style YesLLMD1 fill:#a5d6a7
    style YesLLMD2 fill:#a5d6a7
    style YesLLMD3 fill:#a5d6a7
    style YesLLMD4 fill:#81c784
    style Maybe fill:#fff9c4
    style Benefits fill:#a5d6a7
```

### Use Cases

| Scenario | Why LLM-D? |
|----------|------------|
| **ChatGPT-like service** | Cache awareness + session affinity |
| **Multi-turn conversations** | KV-cache reuse across turns |
| **Models > 70B** | ONLY option for distributed inference |
| **Cost-sensitive** | Optimal resource utilization |
| **High throughput** | Load-aware routing + P/D |
| **Production LLMs** | Full observability + reliability |

---

## Complete Architecture

### All 5 Components Together

```mermaid
flowchart TB
    subgraph "Users"
        User[Client<br/>Applications]
    end
    
    subgraph "Component 1: Routing Sidecar"
        Router[LLM-D Routing Sidecar<br/>- Request routing<br/>- Cache checking<br/>- Load balancing]
        LocalCache[Local Cache<br/>In-Memory]
        Redis[Redis Cache<br/>Shared]
    end
    
    subgraph "Component 2: EPP Scheduler"
        EPP[Endpoint Picker<br/>- Filters pods<br/>- Scores backends<br/>- Selects best pod]
        Filters[Pluggable Filters:<br/>- Prefill/Decode<br/>- By Label]
        Scorers[Pluggable Scorers:<br/>- Cache Hit<br/>- Load Aware<br/>- LRU]
    end
    
    subgraph "Component 3: KV-Cache Manager"
        KVMgr[KV-Cache Manager<br/>- Tracks cache globally<br/>- ZMQ event stream<br/>- HTTP API]
        GlobalIndex[Global Index<br/>prompt → pod mapping]
    end
    
    subgraph "Component 4: Load Monitor"
        Monitor[Load Monitor<br/>- Scrapes metrics<br/>- GPU usage<br/>- Queue length]
        Prometheus[Prometheus<br/>Metrics Store]
    end
    
    subgraph "Component 5: vLLM Workers"
        direction LR
        Prefill[Prefill Workers<br/>Process prompts]
        Decode[Decode Workers<br/>Generate tokens]
        LocalModel[LocalModel Agents<br/>Multi-node coordinator]
    end
    
    subgraph "Infrastructure"
        Gateway[Gateway API<br/>+ Envoy]
        K8s[Kubernetes]
        GPUs[GPU Nodes]
    end
    
    User -->|Request| Gateway
    Gateway -->|ext-proc| EPP
    EPP -->|Selected pod| Router
    
    Router --> LocalCache
    Router --> Redis
    Router -->|Query cache state| KVMgr
    Router -->|Forward request| Prefill
    Router -->|Forward request| Decode
    
    EPP --> Filters
    EPP --> Scorers
    EPP -->|Query scores| KVMgr
    EPP -->|Query load| Monitor
    
    KVMgr --> GlobalIndex
    Prefill -->|ZMQ events| KVMgr
    Decode -->|ZMQ events| KVMgr
    
    Monitor --> Prometheus
    Prefill -->|Metrics| Prometheus
    Decode -->|Metrics| Prometheus
    
    Prefill <-->|KV transfer<br/>NIXLv2| Decode
    
    Prefill --> LocalModel
    Decode --> LocalModel
    LocalModel -->|NCCL| GPUs
    
    K8s --> Prefill
    K8s --> Decode
    K8s --> LocalModel
    
    style User fill:#e1f5ff
    style Router fill:#fff9c4
    style EPP fill:#ffe0b2
    style KVMgr fill:#ffccbc
    style Monitor fill:#c5cae9
    style Prefill fill:#c8e6c9
    style Decode fill:#a5d6a7
    style LocalModel fill:#b2dfdb
```

---

## All 5 Components Explained

### Component 1: LLM-D Routing Sidecar

**What it does**: Smart proxy that routes requests to the best worker based on cache and load

```mermaid
flowchart TB
    Request[Incoming<br/>Request] --> Router[Routing Sidecar]
    
    Router --> Extract[Extract:<br/>- Prompt<br/>- Headers<br/>- Session ID]
    
    Extract --> Hash[Calculate<br/>Prompt Hash]
    
    Hash --> Check1{Check Local<br/>Cache}
    
    Check1 -->|Hit| Return1[⚡ Return<br/>in 5ms]
    Check1 -->|Miss| Check2{Check Redis<br/>Cache}
    
    Check2 -->|Hit| SaveLocal[Save to Local]
    SaveLocal --> Return2[Return<br/>in 10ms]
    
    Check2 -->|Miss| QueryKV[Query KV-Cache<br/>Manager]
    
    QueryKV --> Scores[Get Cache<br/>Scores per Pod]
    
    Scores --> QueryLoad[Query Load<br/>Monitor]
    
    QueryLoad --> LoadMetrics[Get Load<br/>Metrics per Pod]
    
    LoadMetrics --> Combine[Combine Scores:<br/>- Cache: 50%<br/>- Load: 30%<br/>- Latency: 20%]
    
    Combine --> SelectPod[Select Best<br/>Pod]
    
    SelectPod --> CheckPD{P/D<br/>Enabled?}
    
    CheckPD -->|Yes| Prefill[Route to<br/>Prefill Worker]
    CheckPD -->|No| Worker[Route to<br/>Worker]
    
    Prefill --> Transfer[KV Transfer<br/>to Decode]
    Transfer --> Decode[Decode Worker<br/>Generates]
    
    Worker --> Generate[Generate<br/>Response]
    Decode --> Generate
    
    Generate --> Cache[Save to<br/>Caches]
    Cache --> Return3[Return<br/>Response]
    
    Return3 --> Metrics[Update<br/>Metrics]
    
    style Request fill:#e1f5ff
    style Router fill:#fff9c4
    style Return1 fill:#a5d6a7
    style Return2 fill:#c8e6c9
    style QueryKV fill:#ffe0b2
    style Combine fill:#c5cae9
    style Prefill fill:#c8e6c9
    style Decode fill:#a5d6a7
    style Cache fill:#fff9c4
    style Metrics fill:#c5cae9
```

**Key Features**:
- **Multi-level caching**: Local (in-memory) + Redis (shared)
- **SSRF protection**: Validates prefiller host headers
- **Connector protocols**: NIXLv1, NIXLv2, LMCache
- **Session affinity**: Routes same session to same pod
- **Metrics**: Latency, cache hits, routing decisions

**Configuration**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-routing-sidecar
spec:
  containers:
  - name: router
    image: quay.io/llm-d/llm-d-routing-sidecar:0.3
    ports:
    - containerPort: 8000
    env:
    - name: CACHE_ENABLED
      value: "true"
    - name: REDIS_URL
      value: "redis://redis:6379"
    - name: KV_CACHE_MANAGER_URL
      value: "http://kv-cache-manager:8080"
    - name: CONNECTOR
      value: "nixlv2"
    - name: ENABLE_SSRF_PROTECTION
      value: "true"
    args:
    - "-port=8000"
    - "-vllm-port=8001"
```

---

### Component 2: EPP (Endpoint Picker) Scheduler

**What it does**: Selects the best pod for each request using pluggable filters and scorers

```mermaid
flowchart TB
    Request[Request from<br/>Gateway] --> EPP[EPP Scheduler]
    
    EPP --> GetPods[Get All<br/>Candidate Pods]
    
    GetPods --> Filtering[Phase 1:<br/>Filtering]
    
    Filtering --> Filter1{Prefill Filter}
    Filter1 -->|P/D Enabled| OnlyPrefill[Keep Only<br/>Prefill Pods]
    Filter1 -->|P/D Disabled| AllPods[Keep All<br/>Pods]
    
    OnlyPrefill --> Filter2{Label Filter}
    AllPods --> Filter2
    
    Filter2 --> ByLabel[Filter by<br/>Labels]
    
    ByLabel --> Scoring[Phase 2:<br/>Scoring]
    
    Scoring --> Score1[Precise Prefix<br/>Cache Scorer]
    Score1 -->|Query KV Mgr| CacheScore[Cache Hit<br/>Scores]
    
    Scoring --> Score2[Load Aware<br/>Scorer]
    Score2 -->|Query Metrics| LoadScore[Load<br/>Scores]
    
    Scoring --> Score3[Active Request<br/>Scorer]
    Score3 --> ActiveScore[Concurrent Req<br/>Scores]
    
    Scoring --> Score4[Session Affinity<br/>Scorer]
    Score4 --> SessionScore[Session<br/>Scores]
    
    CacheScore --> Combine[Combine<br/>Weighted Scores]
    LoadScore --> Combine
    ActiveScore --> Combine
    SessionScore --> Combine
    
    Combine --> Rank[Rank Pods<br/>by Total Score]
    
    Rank --> Select[Select Top<br/>Pod]
    
    Select --> Header[Add Custom<br/>Headers]
    
    Header --> Forward[Forward to<br/>Router]
    
    style Request fill:#e1f5ff
    style EPP fill:#ffe0b2
    style Filtering fill:#fff4e1
    style OnlyPrefill fill:#c8e6c9
    style Scoring fill:#c5cae9
    style CacheScore fill:#fff9c4
    style LoadScore fill:#ffccbc
    style Combine fill:#ffe0b2
    style Select fill:#a5d6a7
    style Forward fill:#c8e6c9
```

**Pluggable Architecture**:

| Plugin Type | Examples | Purpose |
|-------------|----------|---------|
| **Filters** | PrefillFilter, DecodeFilter, ByLabelSelector | Narrow down candidates |
| **Scorers** | PrecisePrefixCacheScorer, LoadAwareScorer, SessionAffinity | Score remaining pods |
| **Scrapers** | PrometheusMetricScraper, KVCacheStateScraper | Collect scoring data |

**Configuration**:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: epp-config
data:
  config.yaml: |
    filters:
    - name: prefill
      enabled: true
    - name: by-label
      enabled: true
      labels:
        llm-d.ai/role: prefill
    
    scorers:
    - name: cache-scorer
      enabled: true
      weight: 0.5
      endpoint: "http://kv-cache-manager:8080"
    - name: load-scorer
      enabled: true
      weight: 0.3
    - name: session-affinity
      enabled: true
      weight: 0.2
```

---

### Component 3: KV-Cache Manager

**What it does**: Maintains global view of KV-cache state across all vLLM pods

```mermaid
flowchart TB
    subgraph "vLLM Fleet"
        Pod1[vLLM Pod 1<br/>Local KV Cache]
        Pod2[vLLM Pod 2<br/>Local KV Cache]
        Pod3[vLLM Pod 3<br/>Local KV Cache]
    end
    
    subgraph "KV-Cache Manager"
        Subscriber[ZMQ Event<br/>Subscriber]
        Processor[Event<br/>Processor]
        Index[Global Index<br/>Block Mapping]
        API[HTTP API<br/>Query Interface]
    end
    
    subgraph "Event Flow"
        E1[Event: Block Allocated<br/>prompt_hash → block_id]
        E2[Event: Block Freed<br/>block_id released]
        E3[Event: Block Swapped<br/>moved to CPU/GPU]
    end
    
    Pod1 -->|ZMQ Stream| Subscriber
    Pod2 -->|ZMQ Stream| Subscriber
    Pod3 -->|ZMQ Stream| Subscriber
    
    Subscriber --> E1
    Subscriber --> E2
    Subscriber --> E3
    
    E1 --> Processor
    E2 --> Processor
    E3 --> Processor
    
    Processor --> Update[Update<br/>Global Index]
    
    Update --> Index
    
    Index --> Mappings[Mappings:<br/>prompt_hash_X → Pod 2, blocks [5,6,7]<br/>prompt_hash_Y → Pod 1, blocks [2,3]<br/>prompt_hash_Z → Pod 3, blocks [8,9]]
    
    EPP[EPP Scheduler] -->|GET /score?prompt=X| API
    
    API --> Index
    Index -->|Query| Lookup[Lookup Cache<br/>for prompt X]
    
    Lookup --> Scores[Calculate Scores:<br/>Pod 1: 0% hit<br/>Pod 2: 80% hit ⭐<br/>Pod 3: 0% hit]
    
    Scores --> API
    API -->|Response| EPP
    
    EPP -->|Routes to| Pod2
    
    style Pod1 fill:#c8e6c9
    style Pod2 fill:#a5d6a7
    style Pod3 fill:#c8e6c9
    style Subscriber fill:#c5cae9
    style Processor fill:#fff9c4
    style Index fill:#ffe0b2
    style API fill:#fff4e1
    style EPP fill:#bbdefb
    style Pod2 fill:#81c784
```

**Event Types**:

```mermaid
flowchart LR
    subgraph "KVEvent Structure"
        Event[KVEvent] --> Type[event_type]
        Event --> SeqNum[seq_num]
        Event --> Time[timestamp]
        Event --> Blocks[block_ids: List]
        Event --> Hash[prompt_hash]
    end
    
    Type -->|Values| T1[kv_alloc]
    Type --> T2[kv_free]
    Type --> T3[kv_swap_in]
    Type --> T4[kv_swap_out]
    
    style Event fill:#e1f5ff
    style Type fill:#fff9c4
    style T1 fill:#c8e6c9
    style T2 fill:#ffccbc
    style T3 fill:#ffe0b2
    style T4 fill:#c5cae9
```

**Benefits**:
- **10x speedup** for cached prompts
- **Real-time tracking** via ZMQ
- **Global optimization** across fleet
- **Session affinity** for multi-turn
- **HTTP API** for easy integration

**Configuration**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kv-cache-manager
spec:
  containers:
  - name: manager
    image: quay.io/llm-d/kv-cache-manager:latest
    ports:
    - containerPort: 8080
      name: http
    - containerPort: 5555
      name: zmq
    env:
    - name: ZMQ_BIND_ADDRESS
      value: "tcp://*:5555"
    - name: HTTP_PORT
      value: "8080"
    - name: CACHE_TTL_SECONDS                   
      value: "3600"
```

---

### Component 4: Load Monitor

**What it does**: Scrapes and aggregates metrics from all pods

```mermaid
flowchart TB
    Monitor[Load Monitor] --> Scrape[Scrape Targets]
    
    Scrape --> Pod1[Pod 1<br/>Prometheus Endpoint]
    Scrape --> Pod2[Pod 2<br/>Prometheus Endpoint]
    Scrape --> Pod3[Pod 3<br/>Prometheus Endpoint]
    
    Pod1 --> Metrics1[Metrics:<br/>- GPU: 60%<br/>- Queue: 3<br/>- Latency: 1.8s<br/>- Active: 5]
    
    Pod2 --> Metrics2[Metrics:<br/>- GPU: 85%<br/>- Queue: 12<br/>- Latency: 4.2s<br/>- Active: 15]
    
    Pod3 --> Metrics3[Metrics:<br/>- GPU: 45%<br/>- Queue: 1<br/>- Latency: 1.2s<br/>- Active: 2]
    
    Metrics1 --> Aggregate[Aggregate &<br/>Store]
    Metrics2 --> Aggregate
    Metrics3 --> Aggregate
    
    Aggregate --> Prometheus[Prometheus<br/>Time Series DB]
    
    Prometheus --> Query[Query Interface]
    
    EPP[EPP Scheduler] -->|Query Load| Query
    Query -->|Load Data| EPP
    
    Router[Router Sidecar] -->|Query Load| Query
    Query -->|Load Data| Router
    
    style Monitor fill:#c5cae9
    style Pod1 fill:#c8e6c9
    style Pod2 fill:#ffccbc
    style Pod3 fill:#a5d6a7
    style Metrics1 fill:#c8e6c9
    style Metrics2 fill:#ffccbc
    style Metrics3 fill:#a5d6a7
    style Prometheus fill:#ffe0b2
    style EPP fill:#fff4e1
    style Router fill:#fff9c4
```

**Collected Metrics**:
- `vllm_gpu_utilization_percent`
- `vllm_queue_length`
- `vllm_active_requests`
- `vllm_avg_latency_seconds`
- `vllm_cache_hit_rate`

---

### Component 5: vLLM Workers (Prefill/Decode)

**What they do**: Process inference requests, optionally split into P/D stages

```mermaid
flowchart TB
    subgraph "Without P/D Disaggregation"
        Worker1[Single Worker<br/>Does Both:<br/>1. Prefill<br/>2. Decode]
        Worker1 --> Output1[Response]
    end
    
    subgraph "With P/D Disaggregation"
        Prefill[Prefill Worker<br/>- Process prompt<br/>- Build KV cache<br/>- Return logits]
        
        Prefill -->|Transfer| KVTransfer[KV Cache Transfer<br/>via NIXLv2]
        
        KVTransfer --> Decode[Decode Worker<br/>- Receive KV cache<br/>- Generate tokens<br/>- Stream response]
        
        Decode --> Output2[Response]
    end
    
    style Worker1 fill:#c8e6c9
    style Prefill fill:#fff9c4
    style KVTransfer fill:#ffe0b2
    style Decode fill:#a5d6a7
    style Output1 fill:#c8e6c9
    style Output2 fill:#a5d6a7
```

---

## Prefill/Decode Disaggregation

### What is P/D Disaggregation?

**Simple Explanation**: Splitting LLM inference into two stages that run on different workers

```mermaid
flowchart LR
    subgraph "Stage 1: Prefill"
        Input[User Prompt<br/>256 tokens] --> Process[Process ALL<br/>tokens at once]
        Process --> KV[Build KV Cache<br/>Compute-intensive]
    end
    
    subgraph "Stage 2: Decode"
        KV2[Receive<br/>KV Cache] --> Gen[Generate tokens<br/>one by one]
        Gen --> T1[Token 1]
        T1 --> T2[Token 2]
        T2 --> T3[Token 3]
        T3 --> More[...]
    end
    
    KV -->|Transfer| KV2
    
    style Input fill:#e1f5ff
    style Process fill:#fff9c4
    style KV fill:#ffe0b2
    style KV2 fill:#ffe0b2
    style Gen fill:#c8e6c9
    style T1 fill:#a5d6a7
    style T2 fill:#a5d6a7
    style T3 fill:#a5d6a7
```

### Why Separate Prefill and Decode?

```mermaid
flowchart TB
    Question[Why Separate?] --> Reason1[Different Resource<br/>Needs]
    Question --> Reason2[Different Performance<br/>Characteristics]
    Question --> Reason3[Better Utilization]
    
    Reason1 --> R1Detail[Prefill:<br/>- High compute<br/>- Parallel processing<br/>- GPU memory bandwidth]
    
    Reason1 --> R2Detail[Decode:<br/>- Sequential<br/>- Memory-bound<br/>- Lower compute]
    
    Reason2 --> R3Detail[Prefill:<br/>- Batch efficiently<br/>- High throughput]
    
    Reason2 --> R4Detail[Decode:<br/>- Latency-sensitive<br/>- One token at a time]
    
    Reason3 --> Benefits[Benefits:<br/>✅ Scale independently<br/>✅ Better GPU use<br/>✅ Lower latency<br/>✅ Higher throughput<br/>✅ Cost savings]
    
    style Question fill:#e1f5ff
    style Reason1 fill:#fff9c4
    style Reason2 fill:#ffe0b2
    style Reason3 fill:#c5cae9
    style R1Detail fill:#fff4e1
    style R2Detail fill:#fff4e1
    style R3Detail fill:#fff4e1
    style R4Detail fill:#fff4e1
    style Benefits fill:#a5d6a7
```

### Complete P/D Flow

```mermaid
flowchart TB
    Request[User Request:<br/>"Explain quantum computing<br/>in simple terms"] --> Router[Routing Sidecar]
    
    Router --> EPP[EPP Scheduler]
    
    EPP --> FilterP[Filter:<br/>Show only Prefill<br/>workers]
    
    FilterP --> ScoreP[Score Prefill<br/>workers]
    
    ScoreP --> SelectP[Select Best<br/>Prefill Worker]
    
    SelectP --> PrefillPod[Prefill Worker<br/>Pod-3]
    
    PrefillPod --> ProcessPrompt[Process Prompt:<br/>- Tokenize<br/>- Embed<br/>- Attention<br/>- Build KV cache]
    
    ProcessPrompt --> KVReady[KV Cache Ready<br/>256 tokens processed]
    
    KVReady --> Header[Add Header:<br/>x-prefiller-host-port:<br/>pod-3:5555]
    
    Header --> SelectD[EPP Selects<br/>Decode Worker]
    
    SelectD --> DecodePod[Decode Worker<br/>Pod-7]
    
    DecodePod --> Validate[Validate<br/>x-prefiller header<br/>SSRF Protection ✓]
    
    Validate --> Connect[Connect to<br/>Prefiller via NIXLv2]
    
    Connect --> Transfer[Transfer KV Cache<br/>Pod-3 → Pod-7<br/>~10-50ms]
    
    Transfer --> StartDecode[Start Token<br/>Generation]
    
    StartDecode --> Gen1[Generate Token 1:<br/>"Quantum"]
    Gen1 --> Gen2[Generate Token 2:<br/>"computing"]
    Gen2 --> Gen3[Generate Token 3:<br/>"is"]
    Gen3 --> More[... continue until<br/>EOS or max_tokens]
    
    More --> Stream[Stream Response<br/>to User]
    
    Stream --> Complete[✅ Complete]
    
    Complete --> Cleanup[Cleanup:<br/>- Free KV cache<br/>- Update metrics<br/>- Close connections]
    
    style Request fill:#e1f5ff
    style Router fill:#fff9c4
    style EPP fill:#ffe0b2
    style PrefillPod fill:#c8e6c9
    style ProcessPrompt fill:#fff4e1
    style KVReady fill:#ffe0b2
    style DecodePod fill:#a5d6a7
    style Transfer fill:#ffccbc
    style Gen1 fill:#c8e6c9
    style Gen2 fill:#c8e6c9
    style Gen3 fill:#c8e6c9
    style Stream fill:#a5d6a7
    style Complete fill:#81c784
```

### P/D Configuration

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: InferencePool
metadata:
  name: llama-70b-pd-pool
spec:
  modelName: meta-llama/Llama-2-70b-hf
  
  disaggregation:
    enabled: true
    
    prefillSelector:
      matchLabels:
        llm-d.ai/role: prefill
    
    decodeSelector:
      matchLabels:
        llm-d.ai/role: decode
    
    connector:
      type: nixlv2
      config:
        compressionEnabled: true
        rdmaEnabled: true
        sideChannelPortRange: "5555-5556"
```

---

## KV-Cache Optimization

### How KV-Cache Works

```mermaid
flowchart TB
    subgraph "First Request"
        Q1[Prompt:<br/>"What is AI?"] --> Compute1[Compute KV<br/>Cache]
        Compute1 --> Store1[Store in<br/>Memory]
        Store1 --> Gen1[Generate:<br/>"AI is..."]
        Gen1 --> Cache1[KV Cache<br/>Stored]
    end
    
    subgraph "Second Request - Same Prefix"
        Q2[Prompt:<br/>"What is AI and<br/>machine learning?"] --> Check{Check Cache}
        Check -->|Hit!| Reuse[Reuse "What is AI"<br/>KV cache blocks]
        Check -->|Miss| Compute2[Compute new]
        
        Reuse --> Only[Only compute<br/>new tokens:<br/>"and machine learning"]
        
        Only --> Fast[⚡ 10x Faster!<br/>~200ms vs 2s]
    end
    
    Cache1 -.Cache Available.-> Check
    
    style Q1 fill:#e1f5ff
    style Compute1 fill:#ffccbc
    style Gen1 fill:#c8e6c9
    style Q2 fill:#e1f5ff
    style Check fill:#fff4e1
    style Reuse fill:#a5d6a7
    style Only fill:#c8e6c9
    style Fast fill:#81c784
```

### Cache-Aware Routing

```mermaid
flowchart TB
    Request[Request:<br/>Prompt X] --> Router[Router]
    
    Router --> Query[Query KV-Cache<br/>Manager]
    
    Query --> KVMgr[KV-Cache Manager]
    
    KVMgr --> Check[Check Global<br/>Index]
    
    Check --> Results[Results:<br/>Pod 1: 0% hit<br/>Pod 2: 80% hit ⭐<br/>Pod 3: 30% hit]
    
    Results --> Select[Select Pod 2<br/>Best cache hit!]
    
    Select --> Route[Route to<br/>Pod 2]
    
    Route --> Pod2[Pod 2]
    
    Pod2 --> Reuse[Reuse 80%<br/>of KV cache]
    
    Reuse --> Compute[Compute only<br/>20% new]
    
    Compute --> Fast[⚡ Response in<br/>400ms vs 2s]
    
    Fast --> Benefit[10x Speedup!<br/>5x Cost Reduction!]
    
    style Request fill:#e1f5ff
    style Router fill:#fff9c4
    style KVMgr fill:#ffe0b2
    style Results fill:#fff4e1
    style Select fill:#c8e6c9
    style Pod2 fill:#a5d6a7
    style Reuse fill:#81c784
    style Fast fill:#a5d6a7
    style Benefit fill:#81c784
```

---

## Multi-Node Distributed Inference

### Why Multi-Node?

**When a model is too large for one GPU/node**

```mermaid
flowchart LR
    subgraph "Problem"
        Model[LLaMA 70B<br/>140GB Model] -->|Too Big!| GPU[Single GPU<br/>80GB Max]
    end
    
    subgraph "Solution"
        Split[Split Model<br/>Across 4 GPUs]
        GPU1[GPU 1<br/>35GB]
        GPU2[GPU 2<br/>35GB]
        GPU3[GPU 3<br/>35GB]
        GPU4[GPU 4<br/>35GB]
        
        Split --> GPU1
        Split --> GPU2
        Split --> GPU3
        Split --> GPU4
    end
    
    GPU -->|❌ Won't Fit| Failed[Can't Deploy]
    
    GPU1 -->|✅ Fits!| Works[Can Deploy]
    GPU2 --> Works
    GPU3 --> Works
    GPU4 --> Works
    
    style Model fill:#ffccbc
    style GPU fill:#ffcdd2
    style Split fill:#fff9c4
    style GPU1 fill:#c8e6c9
    style GPU2 fill:#c8e6c9
    style GPU3 fill:#c8e6c9
    style GPU4 fill:#c8e6c9
    style Failed fill:#ffcdd2
    style Works fill:#a5d6a7
```

### Tensor Parallelism

```mermaid
flowchart TB
    Input[Input Tokens] --> Broadcast[Broadcast to<br/>All GPUs]
    
    Broadcast --> GPU1[GPU 1<br/>Shard 0]
    Broadcast --> GPU2[GPU 2<br/>Shard 1]
    Broadcast --> GPU3[GPU 3<br/>Shard 2]
    Broadcast --> GPU4[GPU 4<br/>Shard 3]
    
    GPU1 --> Compute1[Compute<br/>Layers 0-17]
    GPU2 --> Compute2[Compute<br/>Layers 18-35]
    GPU3 --> Compute3[Compute<br/>Layers 36-53]
    GPU4 --> Compute4[Compute<br/>Layers 54-71]
    
    Compute1 --> AllReduce[All-Reduce<br/>NCCL Communication]
    Compute2 --> AllReduce
    Compute3 --> AllReduce
    Compute4 --> AllReduce
    
    AllReduce --> Sync[Synchronized<br/>Result]
    
    Sync --> NextToken[Next Token]
    
    NextToken -->|Loop| Broadcast
    
    style Input fill:#e1f5ff
    style Broadcast fill:#fff4e1
    style GPU1 fill:#c8e6c9
    style GPU2 fill:#fff9c4
    style GPU3 fill:#ffe0b2
    style GPU4 fill:#ffccbc
    style AllReduce fill:#c5cae9
    style Sync fill:#a5d6a7
```

### LocalModel Architecture

```mermaid
flowchart TB
    subgraph "Control Plane"
        KServe[KServe Controller]
        LMController[LocalModel<br/>Controller]
    end
    
    subgraph "LocalModelNode 1"
        Agent1[LocalModel Agent 1]
        vLLM1[vLLM Process 1<br/>Shard 0]
        GPU1A[GPU 0]
        GPU1B[GPU 1]
    end
    
    subgraph "LocalModelNode 2"
        Agent2[LocalModel Agent 2]
        vLLM2[vLLM Process 2<br/>Shard 1]
        GPU2A[GPU 0]
        GPU2B[GPU 1]
    end
    
    subgraph "Communication"
        NCCL[NCCL<br/>High-Speed GPU<br/>Communication]
        RDMA[RDMA/InfiniBand<br/>Network]
    end
    
    KServe --> LMController
    LMController --> Agent1
    LMController --> Agent2
    
    Agent1 --> vLLM1
    Agent2 --> vLLM2
    
    vLLM1 --> GPU1A
    vLLM1 --> GPU1B
    vLLM2 --> GPU2A
    vLLM2 --> GPU2B
    
    vLLM1 <-->|NCCL| NCCL
    vLLM2 <-->|NCCL| NCCL
    
    NCCL <--> RDMA
    
    style KServe fill:#c8e6c9
    style LMController fill:#ffe0b2
    style Agent1 fill:#fff9c4
    style Agent2 fill:#fff9c4
    style vLLM1 fill:#c8e6c9
    style vLLM2 fill:#a5d6a7
    style NCCL fill:#ffccbc
    style RDMA fill:#c5cae9
```

### Multi-Node Configuration

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LocalModelNode
metadata:
  name: gpu-node-1
spec:
  resources:
  - gpu: 2
    gpuType: nvidia-a100-80gb
---
apiVersion: serving.kserve.io/v1alpha1
kind: LocalModelNode
metadata:
  name: gpu-node-2
spec:
  resources:
  - gpu: 2
    gpuType: nvidia-a100-80gb
---
apiVersion: serving.kserve.io/v1alpha1
kind: LocalModel
metadata:
  name: llama-70b-distributed
spec:
  storageUri: hf://meta-llama/Llama-2-70b-hf
  modelName: llama-2-70b
  resources:
    requests:
      storage: 150Gi
  scaling:
    minInstances: 1
    maxInstances: 1
  runtimeOptions:
    tensorParallelSize: 4  # Split across 4 GPUs
    pipelineParallelSize: 1
```

---

## Intelligent Autoscaling

### What is LLM-D Autoscaling?

**Simple Explanation**: Automatic scaling based on actual workload, not just CPU/memory

Unlike basic HPA (Horizontal Pod Autoscaler), LLM-D uses **intelligent, workload-aware autoscaling** that considers:
- Request queue depth
- Token processing rate
- KV-cache utilization
- GPU memory usage
- Prefill vs Decode ratios

```mermaid
flowchart TB
    subgraph "Traditional HPA (Basic)"
        CPU[CPU > 80%] --> Scale1[Add Pod]
        Mem[Memory > 75%] --> Scale1
        Scale1 --> Wait1[Wait 30s]
        Wait1 --> CPU
    end
    
    subgraph "LLM-D Intelligent Autoscaling (Advanced)"
        Monitor[Continuous<br/>Monitoring] --> Collect[Collect Metrics:<br/>- Queue depth<br/>- Token rate<br/>- Cache hits<br/>- GPU mem<br/>- Latency]
        
        Collect --> Analyze[Analyze<br/>Patterns]
        
        Analyze --> Decide{Decision<br/>Engine}
        
        Decide -->|Need Prefill| ScalePrefill[Add Prefill<br/>Worker]
        Decide -->|Need Decode| ScaleDecode[Add Decode<br/>Worker]
        Decide -->|High Cache Misses| ScaleCache[Optimize<br/>Cache Pool]
        Decide -->|Balanced| NoAction[No Action]
        
        ScalePrefill --> Monitor
        ScaleDecode --> Monitor
        ScaleCache --> Monitor
        NoAction --> Monitor
    end
    
    style CPU fill:#ffccbc
    style Scale1 fill:#ffccbc
    style Monitor fill:#c8e6c9
    style Analyze fill:#fff9c4
    style Decide fill:#ffe0b2
```

### Autoscaling Architecture

```mermaid
flowchart TB
    subgraph "Metrics Collection"
        vLLM[vLLM Workers] -->|Metrics| Prometheus[Prometheus]
        Sidecar[Routing Sidecar] -->|Metrics| Prometheus
        EPP[EPP Scheduler] -->|Metrics| Prometheus
        KVMgr[KV-Cache Manager] -->|Metrics| Prometheus
    end
    
    subgraph "Autoscaler Decision Engine"
        Prometheus --> Scraper[Metric Scraper]
        
        Scraper --> Analysis[Workload<br/>Analysis]
        
        Analysis --> Factors{Analyze:<br/>Multiple Factors}
        
        Factors --> Q[Queue Depth<br/>pending_requests]
        Factors --> T[Token Rate<br/>tokens/sec]
        Factors --> C[Cache Hit %<br/>hit_ratio]
        Factors --> G[GPU Memory<br/>utilization]
        Factors --> L[Latency<br/>p99_latency]
        
        Q --> Calculate[Calculate<br/>Optimal Replicas]
        T --> Calculate
        C --> Calculate
        G --> Calculate
        L --> Calculate
        
        Calculate --> Decision{Scale<br/>Decision}
    end
    
    subgraph "Scaling Actions"
        Decision -->|Scale Up| CreatePod[Create New<br/>Pod/Worker]
        Decision -->|Scale Down| RemovePod[Remove<br/>Pod/Worker]
        Decision -->|Optimize| Rebalance[Rebalance<br/>Workload]
        
        CreatePod --> Type{Worker<br/>Type}
        
        Type -->|Prefill| AddPrefill[Add Prefill<br/>Worker]
        Type -->|Decode| AddDecode[Add Decode<br/>Worker]
        Type -->|Unified| AddUnified[Add Unified<br/>Worker]
        
        AddPrefill --> Update[Update<br/>InferencePool]
        AddDecode --> Update
        AddUnified --> Update
        RemovePod --> Update
        Rebalance --> Update
        
        Update --> KServe[KServe<br/>Controller]
        KServe --> Pods[Update<br/>Pods]
    end
    
    Pods --> vLLM
    
    style Prometheus fill:#fff4e1
    style Analysis fill:#c8e6c9
    style Calculate fill:#fff9c4
    style Decision fill:#ffe0b2
    style Update fill:#c8e6c9
```

### Key Autoscaling Metrics

| Metric | Description | Threshold | Action |
|--------|-------------|-----------|--------|
| **queue_depth** | Pending requests in queue | > 10 | Scale up prefill workers |
| **avg_tokens_per_sec** | Token generation rate | < 50% capacity | Consider scaling down |
| **cache_hit_ratio** | % of cache hits | < 30% | Scale up for better cache distribution |
| **gpu_memory_util** | GPU memory usage | > 85% | Add workers or optimize batch size |
| **p99_latency_ms** | 99th percentile latency | > SLA threshold | Scale up immediately |
| **prefill_vs_decode_ratio** | Request type ratio | Imbalanced | Adjust P/D worker ratio |

### Autoscaling Decision Flow

```mermaid
flowchart TB
    Start[Monitor Metrics] --> Check[Check Every<br/>10 seconds]
    
    Check --> Eval{Evaluate<br/>Conditions}
    
    Eval -->|Queue > 10| HighQueue[High Queue<br/>Detected]
    Eval -->|Latency > SLA| HighLatency[High Latency<br/>Detected]
    Eval -->|GPU > 85%| HighGPU[GPU Pressure<br/>Detected]
    Eval -->|All OK| Monitor[Continue<br/>Monitoring]
    
    HighQueue --> QueueReason{Why?}
    QueueReason -->|Prefill Slow| NeedPrefill[Need More<br/>Prefill Workers]
    QueueReason -->|Decode Slow| NeedDecode[Need More<br/>Decode Workers]
    
    HighLatency --> LatencyReason{Why?}
    LatencyReason -->|Cold Cache| WarmCache[Warm Up<br/>Cache]
    LatencyReason -->|Overload| ScaleGeneral[Scale Up<br/>All Workers]
    
    HighGPU --> GPUReason{Why?}
    GPUReason -->|Large Models| OptimizeBatch[Optimize<br/>Batch Size]
    GPUReason -->|Too Many Requests| ScaleOut[Scale Out<br/>New Nodes]
    
    NeedPrefill --> Execute1[Scale Action:<br/>Add Prefill Pod]
    NeedDecode --> Execute2[Scale Action:<br/>Add Decode Pod]
    WarmCache --> Execute3[Optimize Action:<br/>Cache Warming]
    ScaleGeneral --> Execute4[Scale Action:<br/>Add Unified Pod]
    OptimizeBatch --> Execute5[Config Action:<br/>Adjust Batch]
    ScaleOut --> Execute6[Infra Action:<br/>Add Node]
    
    Execute1 --> Wait[Wait 30s<br/>Stabilize]
    Execute2 --> Wait
    Execute3 --> Wait
    Execute4 --> Wait
    Execute5 --> Wait
    Execute6 --> Wait
    
    Wait --> Start
    Monitor --> Start
    
    style Start fill:#e1f5ff
    style HighQueue fill:#ffccbc
    style HighLatency fill:#ffccbc
    style HighGPU fill:#ffccbc
    style Execute1 fill:#c8e6c9
    style Execute2 fill:#c8e6c9
    style Execute3 fill:#fff9c4
    style Execute4 fill:#c8e6c9
    style Monitor fill:#a5d6a7
```

### Configuration Example

```yaml
apiVersion: serving.kubeflow.org/v1alpha1
kind: InferencePool
metadata:
  name: llama2-pool
spec:
  minInstances: 2  # Minimum always-on workers
  maxInstances: 10  # Maximum scale limit
  
  # Autoscaling configuration
  autoscaling:
    enabled: true
    metrics:
    - type: queue_depth
      target: 5  # Target average queue depth per pod
    - type: gpu_memory
      target: 75  # Target 75% GPU memory utilization
    - type: tokens_per_second
      target: 100  # Target 100 tokens/sec per pod
    
    # Scaling behavior
    scaleUpPeriod: 30s  # Wait 30s before scaling up
    scaleDownPeriod: 300s  # Wait 5min before scaling down
    scaleUpStabilization: 60s  # Stabilization window
    
    # Advanced policies
    policies:
    - type: prefill_decode_ratio
      enabled: true
      targetRatio: "1:3"  # 1 prefill worker for every 3 decode workers
    
    - type: cache_aware
      enabled: true
      minCacheHitRate: 0.4  # Maintain 40% cache hit rate
```

### Autoscaling Benefits

**Performance**:
- ⚡ **Faster scaling**: Scales in 30s vs 2-3min for HPA
- 🎯 **Workload-aware**: Scales based on actual LLM metrics
- 📊 **Predictive**: Anticipates load based on patterns

**Cost**:
- 💰 **60% cost savings**: Scale down during low traffic
- 🎯 **Right-sizing**: Optimal worker count at all times
- ⚖️ **P/D optimization**: Efficient prefill/decode ratio

**Operational**:
- 🔄 **Automated**: No manual intervention
- 📈 **Intelligent**: Considers multiple factors
- 🛡️ **Safe**: Gradual scaling with stabilization

### vs Traditional Autoscaling

| Feature | HPA (Basic) | LLM-D Autoscaling |
|---------|-------------|-------------------|
| **Metrics** | CPU/Memory only | Queue, tokens/sec, cache, GPU |
| **Scale Speed** | 2-3 minutes | 30 seconds |
| **Awareness** | Resource-based | Workload-based |
| **P/D Support** | ❌ No | ✅ Yes - separate scaling |
| **Cache-Aware** | ❌ No | ✅ Yes - optimizes placement |
| **Predictive** | ❌ No | ✅ Yes - pattern-based |
| **Cost Optimization** | ⭐⭐ Good | ⭐⭐⭐ Excellent |

### Monitoring Autoscaling

**Key Metrics to Watch**:
```bash
# Check autoscaling decisions
kubectl logs -n llm-serving deployment/autoscaler -f

# View scaling events
kubectl get events --field-selector reason=ScalingReplicaSet

# Check current replicas
kubectl get inferencepool llama2-pool -o jsonpath='{.status.replicas}'

# Monitor queue depth
curl http://prometheus:9090/api/v1/query?query=vllm_queue_depth
```

**Grafana Dashboard Panels**:
- Replicas over time
- Queue depth trend
- Token rate per worker
- Cache hit rate
- GPU utilization
- Scaling events timeline

---

## Complete Request Flows

### Flow 1: Simple Request (No P/D)

```mermaid
flowchart TB
    User[User Request] --> Gateway[Gateway + Envoy]
    Gateway -->|ext-proc| EPP[EPP Scheduler]
    
    EPP --> Filter[Filter Pods]
    Filter --> Score[Score Pods:<br/>- Cache<br/>- Load]
    Score --> Select[Select Pod 2]
    
    Select --> Router[Router Sidecar]
    Router --> Cache{Check Cache}
    Cache -->|Miss| Forward[Forward to<br/>vLLM Pod 2]
    
    Forward --> Process[Process<br/>Inference]
    Process --> Response[Generate<br/>Response]
    Response --> Router
    Router --> SaveCache[Save to Cache]
    SaveCache --> User
    
    style User fill:#e1f5ff
    style Gateway fill:#c5cae9
    style EPP fill:#ffe0b2
    style Select fill:#c8e6c9
    style Router fill:#fff9c4
    style Process fill:#b2dfdb
    style Response fill:#a5d6a7
```

### Flow 2: P/D Disaggregated Request

```mermaid
flowchart TB
    User[User Request] --> Gateway[Gateway]
    Gateway --> EPP[EPP]
    
    EPP --> PrefillFilter[Filter:<br/>Prefill Only]
    PrefillFilter --> ScoreP[Score Prefill<br/>Pods]
    ScoreP --> SelectP[Select<br/>Prefill Pod 3]
    
    SelectP --> Router[Router]
    Router --> PrefillPod[Prefill Pod 3]
    
    PrefillPod --> BuildKV[Build KV<br/>Cache]
    BuildKV --> Header[Add<br/>x-prefiller header]
    
    Header --> EPP2[EPP Again]
    EPP2 --> DecodeFilter[Filter:<br/>Decode Only]
    DecodeFilter --> ScoreD[Score Decode<br/>Pods]
    ScoreD --> SelectD[Select<br/>Decode Pod 7]
    
    SelectD --> DecodePod[Decode Pod 7]
    DecodePod --> Validate[Validate<br/>SSRF]
    Validate --> Transfer[Transfer KV<br/>NIXLv2]
    Transfer --> Generate[Generate<br/>Tokens]
    Generate --> User
    
    style User fill:#e1f5ff
    style Gateway fill:#c5cae9
    style EPP fill:#ffe0b2
    style PrefillPod fill:#c8e6c9
    style BuildKV fill:#fff4e1
    style DecodePod fill:#a5d6a7
    style Transfer fill:#ffccbc
    style Generate fill:#81c784
```

---

## Configuration Examples

### Example 1: Basic LLM-D

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: InferencePool
metadata:
  name: llama-7b-pool
spec:
  modelName: meta-llama/Llama-2-7b-hf
  selector:
    matchLabels:
      model: llama-7b
  routingPolicy:
    type: Dynamic
    schedulerProfile: default
  healthCheck:
    enabled: true
```

### Example 2: P/D Enabled

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: InferencePool
metadata:
  name: llama-70b-pd
spec:
  modelName: meta-llama/Llama-2-70b-hf
  disaggregation:
    enabled: true
    prefillSelector:
      matchLabels:
        llm-d.ai/role: prefill
    decodeSelector:
      matchLabels:
        llm-d.ai/role: decode
    connector:
      type: nixlv2
```

### Example 3: Multi-Node

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LocalModel
metadata:
  name: llama-70b-multi-node
spec:
  storageUri: hf://meta-llama/Llama-2-70b-hf
  modelName: llama-2-70b
  runtimeOptions:
    tensorParallelSize: 4
    pipelineParallelSize: 1
  scaling:
    minInstances: 1
    maxInstances: 1
```

---

## Performance & Cost Benefits

### Performance Comparison

| Scenario | Without LLM-D | With LLM-D | Improvement |
|----------|---------------|------------|-------------|
| **First Request** | 2000ms | 2000ms | - |
| **Cached Repeat** | 2000ms | 200ms | **10x faster** |
| **Similar Prompt** | 2000ms | 400ms | **5x faster** |
| **Multi-turn Chat** | 2000ms/turn | 300ms/turn | **6.7x faster** |

### Cost Savings

```mermaid
flowchart LR
    subgraph "Without LLM-D"
        W1[10 GPUs<br/>Random routing<br/>Low efficiency<br/>$30/hour]
    end
    
    subgraph "With LLM-D"
        L1[6 GPUs<br/>Cache-aware routing<br/>High efficiency<br/>$18/hour]
    end
    
    W1 -->|Optimize| L1
    
    L1 --> Savings[Savings:<br/>$12/hour<br/>$8,640/month<br/>40% reduction]
    
    style W1 fill:#ffccbc
    style L1 fill:#a5d6a7
    style Savings fill:#81c784
```

---

## Troubleshooting

### Issue 1: KV-Cache Manager Not Working

```mermaid
flowchart TB
    Problem[Cache Manager<br/>Not Tracking] --> Check1{vLLM Pods<br/>Sending Events?}
    
    Check1 -->|No| Fix1[Enable ZMQ:<br/>--kv-cache-events-zmq<br/>--kv-cache-events-port=5555]
    
    Check1 -->|Yes| Check2{Manager<br/>Receiving?}
    
    Check2 -->|No| Fix2[Check Network:<br/>- Firewall<br/>- Service discovery]
    
    Check2 -->|Yes| Check3{Index<br/>Updating?}
    
    Check3 -->|No| Fix3[Check Logs:<br/>kubectl logs kv-cache-manager]
    
    Fix1 --> Retry[Restart Pods]
    Fix2 --> Retry
    Fix3 --> Retry
    Retry --> Success[✅ Working]
    
    style Problem fill:#ffcdd2
    style Check1 fill:#fff4e1
    style Check2 fill:#fff4e1
    style Check3 fill:#fff4e1
    style Success fill:#a5d6a7
```

### Issue 2: P/D Transfer Failing

```mermaid
flowchart TB
    Problem[KV Transfer<br/>Failing] --> Check1{SSRF<br/>Protection?}
    
    Check1 -->|Blocking| Fix1[Add to Allowlist:<br/>allowed_prefiller_cidrs]
    
    Check1 -->|OK| Check2{NIXLv2<br/>Configured?}
    
    Check2 -->|No| Fix2[Enable NIXLv2:<br/>--connector=nixlv2]
    
    Check2 -->|Yes| Check3{Side Channel<br/>Port?}
    
    Check3 -->|Blocked| Fix3[Open Ports:<br/>5555-5556]
    
    Fix1 --> Test[Test Transfer]
    Fix2 --> Test
    Fix3 --> Test
    Test --> Success[✅ Working]
    
    style Problem fill:#ffcdd2
    style Success fill:#a5d6a7
```

### Commands

```bash
# Check InferencePool
kubectl get inferencepool -n <namespace>

# Check KV-Cache Manager
kubectl logs -n llm-serving kv-cache-manager

# Check EPP Scheduler
kubectl logs -n llm-serving epp-scheduler

# Check Router
kubectl logs -n llm-serving routing-sidecar

# Check vLLM pod metrics
kubectl port-forward <pod> 8001:8001
curl http://localhost:8001/metrics

# Check KV-Cache Manager API
kubectl port-forward kv-cache-manager 8080:8080
curl "http://localhost:8080/score?prompt=test"
```

---

## Summary

### Why Choose LLM-D?

✅ **10x speedup** for cached prompts  
✅ **40-60% cost savings** through optimization  
✅ **Multi-node support** for 70B+ models  
✅ **P/D disaggregation** for better utilization  
✅ **Production-ready** with full observability  
✅ **Cache-aware** routing for efficiency  
✅ **Load-aware** balancing for performance  

### Key Components Recap

1. **Routing Sidecar** - Smart proxy with caching
2. **EPP Scheduler** - Pluggable pod selection
3. **KV-Cache Manager** - Global cache tracking
4. **Load Monitor** - Metrics aggregation
5. **vLLM Workers** - Inference execution

### When to Use LLM-D

| Scenario | Recommendation |
|----------|----------------|
| **LLM 7B-70B** | ✅ Highly Recommended |
| **LLM > 70B** | ✅ Required (multi-node) |
| **Multi-turn chats** | ✅ Essential (cache) |
| **Cost-sensitive** | ✅ 40% savings |
| **Production LLMs** | ✅ Production-ready |

---

**Document Version**: 1.0  
**Last Updated**: October 27, 2025  
**Status**: ✅ 100% Complete - All LLM-D Features Covered  
**Coverage**: 5 Components, P/D, KV-Cache, Multi-Node, Complete Flows

