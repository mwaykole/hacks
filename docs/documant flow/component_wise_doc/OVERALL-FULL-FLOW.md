# Overall Full Flow - Complete System Architecture

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [All Components Explained](#all-components-explained)
3. [Deployment Mode Comparison](#deployment-mode-comparison)
4. [Complete End-to-End Flow](#complete-end-to-end-flow)
5. [Component Interaction Flows](#component-interaction-flows)
6. [Decision Trees](#decision-trees)

---

## System Overview

### What is OpenDataHub ML Serving?

OpenDataHub ML Serving is a complete platform for deploying and managing machine learning models in production. It supports three deployment modes and handles everything from model storage to auto-scaling.

### High-Level Architecture

```mermaid
flowchart TB
    subgraph "Users & Applications"
        EndUser[End Users<br/>API Consumers]
        DataSci[Data Scientists<br/>Model Creators]
        PlatAdmin[Platform Admins<br/>Operators]
    end
    
    subgraph "Management Layer"
        ODH[ODH Model Controller<br/>Model Lifecycle Management]
        Registry[Model Registry<br/>Catalog & Metadata]
        Dashboard[ODH Dashboard<br/>Web Interface]
    end
    
    subgraph "Serving Platform - KServe"
        Controller[KServe Controller<br/>Deployment Manager]
        Webhook[Validation Webhook<br/>Config Validation]
        
        subgraph "Deployment Modes"
            direction LR
            Raw[Raw K8s<br/>Standard Deployment]
            Serverless[Serverless<br/>Knative-based]
            LLMD[LLM-D<br/>Advanced LLM]
        end
    end
    
    subgraph "LLM-D Components" 
        Router[Routing Sidecar<br/>Smart Load Balancer]
        Scheduler[Inference Scheduler<br/>Task Manager]
        KVCache[KV-Cache Manager<br/>Cache Coordinator]
        Monitor[Load Monitor<br/>Metrics Collector]
    end
    
    subgraph "Data Plane"
        Pods[Model Pods<br/>Running Models]
        Storage[Storage Layer<br/>S3, PVC, HF, OCI]
        GPUs[GPU Resources<br/>NVIDIA A100, L40]
    end
    
    subgraph "Infrastructure"
        K8s[Kubernetes<br/>Orchestration]
        Knative[Knative Serving<br/>Serverless Runtime]
        Istio[Istio<br/>Service Mesh]
        Prometheus[Prometheus<br/>Metrics]
    end
    
    EndUser -->|Inference Requests| Router
    DataSci -->|Deploy Models| ODH
    PlatAdmin -->|Configure| Dashboard
    
    ODH --> Registry
    ODH --> Controller
    Dashboard --> ODH
    
    Controller --> Webhook
    Controller --> Raw
    Controller --> Serverless
    Controller --> LLMD
    
    Router --> Scheduler
    Router --> KVCache
    Scheduler --> Monitor
    
    Raw --> K8s
    Serverless --> Knative
    LLMD --> Scheduler
    
    K8s --> Pods
    Knative --> Pods
    Scheduler --> Pods
    
    Pods --> Storage
    Pods --> GPUs
    
    Pods --> Prometheus
    Router --> Prometheus
    Scheduler --> Prometheus
    
    style EndUser fill:#e1f5ff
    style DataSci fill:#e1bee7
    style PlatAdmin fill:#ffccbc
    style ODH fill:#fff4e1
    style Controller fill:#c8e6c9
    style Router fill:#fff9c4
    style Scheduler fill:#ffe0b2
    style Pods fill:#b2dfdb
```

---

## All Components Explained

### Component 1: KServe Controller

**What it does**: Core serving platform that manages model deployments

```mermaid
flowchart TB
    Start[User Creates<br/>InferenceService] --> Webhook{Validate<br/>Configuration}
    
    Webhook -->|Invalid| Reject[❌ Reject with Error]
    Webhook -->|Valid| Defaults[Apply Defaults<br/>& Best Practices]
    
    Defaults --> Runtime{Resolve<br/>ServingRuntime}
    
    Runtime --> Match[Match Framework<br/>TensorFlow → TF Serving<br/>PyTorch → TorchServe<br/>SKLearn → MLServer<br/>LLM → vLLM/HuggingFace]
    
    Match --> Mode{Deployment<br/>Mode?}
    
    Mode -->|Raw K8s| CreateDepl[Create K8s<br/>Deployment]
    Mode -->|Serverless| CreateKsvc[Create Knative<br/>Service]
    Mode -->|LLM-D| CreateLLMD[Create LLM-D<br/>Resources]
    
    CreateDepl --> Resources[Create Supporting<br/>Resources]
    CreateKsvc --> Resources
    CreateLLMD --> Resources
    
    Resources --> ConfigMap[ConfigMap]
    Resources --> Secret[Secrets]
    Resources --> Service[K8s Service]
    Resources --> RBAC[RBAC Rules]
    
    ConfigMap --> Monitor[Monitor Status]
    Secret --> Monitor
    Service --> Monitor
    RBAC --> Monitor
    
    Monitor --> Ready{Pods<br/>Ready?}
    
    Ready -->|No| Wait[Wait & Retry]
    Ready -->|Yes| UpdateStatus[✅ Update Status<br/>Ready=True]
    
    Wait --> Monitor
    
    UpdateStatus --> Complete[InferenceService<br/>LIVE]
    
    style Start fill:#e1f5ff
    style Webhook fill:#fff4e1
    style Reject fill:#ffcdd2
    style Defaults fill:#c8e6c9
    style Runtime fill:#ffe0b2
    style Match fill:#fff9c4
    style Mode fill:#c5cae9
    style CreateDepl fill:#bbdefb
    style CreateKsvc fill:#c8e6c9
    style CreateLLMD fill:#ffe0b2
    style Resources fill:#b2dfdb
    style Monitor fill:#c5cae9
    style Ready fill:#fff4e1
    style UpdateStatus fill:#a5d6a7
    style Complete fill:#81c784
```

**Key Responsibilities**:
- Validates InferenceService configurations
- Resolves appropriate serving runtime
- Creates Kubernetes resources
- Monitors deployment health
- Updates status conditions

---

### Component 2: ODH Model Controller

**What it does**: Manages model lifecycle and deployment automation

```mermaid
flowchart TB
    DS[Data Scientist<br/>Has Trained Model] --> Register[Register Model<br/>in Registry]
    
    Register --> Validate[Validate Model<br/>Metadata]
    
    Validate --> Check{Model<br/>Valid?}
    
    Check -->|No| Fix[Return Errors<br/>to Fix]
    Check -->|Yes| Store[Store Metadata<br/>in Registry]
    
    Store --> Config[Load Serving<br/>Configuration]
    
    Config --> Apply{Apply<br/>Policies}
    
    Apply --> Resources[Calculate Resources<br/>CPU, Memory, GPU]
    Apply --> Scaling[Configure Autoscaling<br/>Min/Max Replicas]
    Apply --> Network[Setup Networking<br/>Routes & Policies]
    
    Resources --> CreateISVC[Create<br/>InferenceService]
    Scaling --> CreateISVC
    Network --> CreateISVC
    
    CreateISVC --> KServe[Hand off to<br/>KServe Controller]
    
    KServe --> MonitorLoop[Monitor Deployment]
    
    MonitorLoop --> Health{Health<br/>Check}
    
    Health -->|Unhealthy| Alert[Send Alerts]
    Health -->|Healthy| Metrics[Collect Metrics]
    
    Alert --> MonitorLoop
    Metrics --> MonitorLoop
    
    Metrics --> UpdateReg[Update Registry<br/>Status & Stats]
    
    UpdateReg --> Lifecycle{Lifecycle<br/>Event?}
    
    Lifecycle -->|Update| Version[New Version<br/>Deployment]
    Lifecycle -->|Retire| Cleanup[Cleanup<br/>Resources]
    Lifecycle -->|Scale| Adjust[Adjust<br/>Replicas]
    
    Version --> CreateISVC
    Cleanup --> End[Model Retired]
    Adjust --> KServe
    
    style DS fill:#e1bee7
    style Register fill:#c5cae9
    style Validate fill:#fff4e1
    style Check fill:#ffe0b2
    style Fix fill:#ffccbc
    style Store fill:#c8e6c9
    style CreateISVC fill:#b2dfdb
    style MonitorLoop fill:#c5cae9
    style UpdateReg fill:#c8e6c9
```

**Key Responsibilities**:
- Model registration and cataloging
- Automated deployment workflows
- Configuration management
- Version control
- Monitoring and alerting
- Multi-tenancy support

---

### Component 3: LLM-D Routing Sidecar

**What it does**: Intelligent request routing and load balancing for LLMs

```mermaid
flowchart TB
    Request[Incoming<br/>Request] --> Auth{Authenticate<br/>& Classify}
    
    Auth -->|Failed| Reject[❌ 401 Unauthorized]
    Auth -->|Success| Extract[Extract Metadata<br/>- User tier<br/>- Priority<br/>- Prompt]
    
    Extract --> Hash[Calculate<br/>Prompt Hash]
    
    Hash --> CacheCheck{Check<br/>Cache}
    
    CacheCheck -->|Hit| Return1[⚡ Return Cached<br/>5-10ms]
    CacheCheck -->|Miss| LoadCheck[Query Load<br/>Monitor]
    
    LoadCheck --> Backends[Get Backend<br/>Status]
    
    Backends --> Score[Calculate Scores<br/>Based On:<br/>- Load %<br/>- Queue Length<br/>- Latency<br/>- Cache Hit Rate]
    
    Score --> Select{Select Best<br/>Backend}
    
    Select --> Primary[Primary Backend<br/>Lowest Load]
    Select --> Secondary[Secondary Backend<br/>Medium Load]
    Select --> Fallback[Fallback Backend<br/>Last Resort]
    
    Primary --> Schedule[Send to<br/>Scheduler]
    Secondary --> Schedule
    Fallback --> Schedule
    
    Schedule --> Execute[Execute<br/>Inference]
    
    Execute --> CheckResp{Response<br/>OK?}
    
    CheckResp -->|Success| SaveCache[Save to<br/>Cache]
    CheckResp -->|Error| Retry{Retry<br/>Allowed?}
    
    Retry -->|Yes| Select
    Retry -->|No| Error[❌ Return Error]
    
    SaveCache --> Return2[✅ Return Response<br/>Record Metrics]
    
    Return2 --> Metrics[Update:<br/>- Latency<br/>- Cache Stats<br/>- Backend Load]
    
    style Request fill:#e1f5ff
    style Auth fill:#fff4e1
    style Reject fill:#ffcdd2
    style Extract fill:#c8e6c9
    style CacheCheck fill:#ffe0b2
    style Return1 fill:#a5d6a7
    style LoadCheck fill:#c5cae9
    style Score fill:#fff9c4
    style Select fill:#ffe0b2
    style Execute fill:#b2dfdb
    style SaveCache fill:#c8e6c9
    style Return2 fill:#a5d6a7
    style Metrics fill:#c5cae9
```

**Key Features**:
- Multi-level caching (local + shared)
- Cache-aware routing
- Load-aware distribution
- QoS-based prioritization
- Automatic failover
- Circuit breaker pattern

---

### Component 4: LLM-D Inference Scheduler

**What it does**: Schedules and manages LLM inference tasks

```mermaid
flowchart TB
    Task[Task<br/>Submitted] --> Classify{Classify<br/>Task Type}
    
    Classify -->|Interactive| HighQ[High Priority<br/>Queue]
    Classify -->|Batch| BatchQ[Batch<br/>Queue]
    Classify -->|Streaming| StreamQ[Stream<br/>Queue]
    Classify -->|Fine-tune| FTQ[Training<br/>Queue]
    
    HighQ --> Schedule[Scheduling<br/>Engine]
    BatchQ --> Schedule
    StreamQ --> Schedule
    FTQ --> Schedule
    
    Schedule --> CheckRes{Resources<br/>Available?}
    
    CheckRes -->|Yes| AllocNode[Select Best<br/>Node]
    CheckRes -->|No| Preempt{Can<br/>Preempt?}
    
    Preempt -->|Yes| PreemptTask[Preempt Low<br/>Priority Task]
    Preempt -->|No| WaitQ[Add to<br/>Wait Queue]
    
    PreemptTask --> AllocNode
    
    AllocNode --> Score[Score Nodes<br/>Based On:<br/>- GPU Availability<br/>- Memory<br/>- Network<br/>- Affinity Rules]
    
    Score --> Allocate[Allocate<br/>Resources]
    
    Allocate --> DispatchType{Task<br/>Type?}
    
    DispatchType -->|Single GPU| SingleGPU[Single GPU<br/>Execution]
    DispatchType -->|Multi-GPU| MultiGPU[Tensor Parallel<br/>Execution]
    DispatchType -->|Batch| BatchExec[Batch<br/>Processing]
    
    SingleGPU --> Execute[Execute<br/>Task]
    MultiGPU --> Execute
    BatchExec --> Execute
    
    Execute --> Monitor[Monitor<br/>Progress]
    
    Monitor --> Check{Task<br/>Complete?}
    
    Check -->|No| Timeout{Timeout?}
    Check -->|Yes| Release[Release<br/>Resources]
    
    Timeout -->|No| Monitor
    Timeout -->|Yes| Terminate[Terminate &<br/>Release]
    
    Release --> UpdateMetrics[Update<br/>Metrics]
    Terminate --> UpdateMetrics
    
    UpdateMetrics --> Done[Task<br/>Complete]
    
    WaitQ --> Periodic[Periodic<br/>Re-evaluation]
    Periodic --> CheckRes
    
    style Task fill:#e1f5ff
    style Classify fill:#fff4e1
    style HighQ fill:#ffccbc
    style BatchQ fill:#c8e6c9
    style Schedule fill:#ffe0b2
    style CheckRes fill:#fff4e1
    style AllocNode fill:#c5cae9
    style Score fill:#fff9c4
    style Execute fill:#b2dfdb
    style Monitor fill:#c5cae9
    style Release fill:#c8e6c9
    style Done fill:#a5d6a7
```

**Key Features**:
- Multiple scheduling policies
- GPU sharing (MIG, time-slicing)
- Dynamic batching
- Preemption support
- Resource optimization
- Multi-tenancy quotas

---

### Component 5: KV-Cache Manager

**What it does**: Manages distributed KV-cache state for LLMs

```mermaid
flowchart TB
    subgraph "vLLM Fleet"
        Pod1[vLLM Pod 1<br/>Local KV Cache]
        Pod2[vLLM Pod 2<br/>Local KV Cache]
        Pod3[vLLM Pod 3<br/>Local KV Cache]
    end
    
    subgraph "KV-Cache Manager"
        EventSub[Event Subscriber<br/>ZMQ Listener]
        Processor[Event Processor]
        Index[Global Index<br/>Block → Pod Mapping]
        API[HTTP API<br/>Query Interface]
    end
    
    subgraph "Scheduler"
        EPP[EPP Scheduler<br/>Makes Routing Decisions]
    end
    
    Pod1 -->|Stream KVEvents| EventSub
    Pod2 -->|Stream KVEvents| EventSub
    Pod3 -->|Stream KVEvents| EventSub
    
    EventSub --> Processor
    Processor --> Index
    
    EPP -->|Query: Which pod<br/>has cache for prompt X?| API
    API --> Index
    Index -->|Pod 2 has<br/>80% cache hit| API
    API -->|Score: Pod2=90<br/>Pod1=60, Pod3=50| EPP
    
    EPP -->|Route to Pod 2| Pod2
    
    style Pod1 fill:#c8e6c9
    style Pod2 fill:#a5d6a7
    style Pod3 fill:#c8e6c9
    style EventSub fill:#c5cae9
    style Processor fill:#fff9c4
    style Index fill:#ffe0b2
    style API fill:#fff4e1
    style EPP fill:#bbdefb
```

**Key Features**:
- Real-time cache state tracking
- ZMQ event streaming from vLLM
- Global cache block index
- Cache-aware routing scores
- HTTP API for EPP
- 10x speedup for cached prompts

---

## Deployment Mode Comparison

**Note on ModelMesh**: KServe also supports **ModelMesh** mode for extreme high-density multi-model serving (100s-1000s of models). This specialized mode is for specific use cases and is not covered here. See [KServe ModelMesh docs](https://kserve.github.io/website/docs/admin-guide/overview#modelmesh-deployment).

### Decision Flowchart

```mermaid
flowchart TB
    Start([Need to Deploy<br/>ML Model]) --> Type{Model<br/>Type?}
    
    Type -->|LLM 7B+| LLMPath[Large Language<br/>Model Path]
    Type -->|Traditional ML| MLPath[Traditional ML<br/>Path]
    
    LLMPath --> LLMSize{Model<br/>Size?}
    
    LLMSize -->|< 20GB| LLMSmall[Consider<br/>Serverless or Raw]
    LLMSize -->|20-70GB| LLMFits[LLM-D<br/>Single Node]
    LLMSize -->|> 70GB| LLMDistrib[LLM-D<br/>Distributed]
    
    MLPath --> Traffic{Traffic<br/>Pattern?}
    
    Traffic -->|Variable/Bursty| Serverless1[✅ Serverless Mode]
    Traffic -->|Steady| CheckScale{Need<br/>Scale-to-Zero?}
    Traffic -->|Predictable| Raw1[✅ Raw K8s Mode]
    
    CheckScale -->|Yes| Serverless2[✅ Serverless Mode]
    CheckScale -->|No| Raw2[✅ Raw K8s Mode]
    
    LLMSmall --> CacheNeed{Need Cache<br/>Optimization?}
    
    CacheNeed -->|Yes| LLMD1[✅ LLM-D Mode]
    CacheNeed -->|No| Serverless3[✅ Serverless Mode]
    
    LLMFits --> LLMD2[✅ LLM-D Mode<br/>Tensor Parallel]
    LLMDistrib --> LLMD3[✅ LLM-D Mode<br/>Multi-Node]
    
    Serverless1 --> Features1[Scale-to-Zero<br/>Auto-scaling<br/>Traffic Splitting]
    Serverless2 --> Features1
    Serverless3 --> Features1
    
    Raw1 --> Features2[HPA Scaling<br/>Simple Setup<br/>Predictable Cost]
    Raw2 --> Features2
    
    LLMD1 --> Features3[Cache-Aware Routing<br/>Load Balancing<br/>P/D Disaggregation]
    LLMD2 --> Features3
    LLMD3 --> Features3
    
    style Start fill:#e1f5ff
    style Type fill:#fff4e1
    style LLMPath fill:#ffe0b2
    style MLPath fill:#c8e6c9
    style Serverless1 fill:#a5d6a7
    style Serverless2 fill:#a5d6a7
    style Serverless3 fill:#a5d6a7
    style Raw1 fill:#81c784
    style Raw2 fill:#81c784
    style LLMD1 fill:#ffd93d
    style LLMD2 fill:#ffd93d
    style LLMD3 fill:#ffd93d
```

### Feature Comparison Matrix

| Feature | Raw K8s | Serverless | LLM-D |
|---------|---------|------------|-------|
| **Scale-to-Zero** | ❌ No | ✅ Yes | ✅ Yes |
| **GPU Support** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Auto-scaling** | ✅ HPA | ✅ KPA | ✅ Custom |
| **Cache-Aware Routing** | ❌ No | ❌ No | ✅ Yes |
| **Distributed Inference** | ⚠️ Manual | ⚠️ Manual | ✅ Built-in |
| **Traffic Splitting** | ⚠️ Manual | ✅ Built-in | ✅ Built-in |
| **InferenceGraph** | ✅ Yes | ✅ Yes | ❌ No |
| **Multi-Model Serving** | ✅ Yes | ✅ Yes | ⚠️ Limited |
| **P/D Disaggregation** | ❌ No | ❌ No | ✅ Yes |
| **Setup Complexity** | ⭐ Simple | ⭐⭐ Moderate | ⭐⭐⭐ Advanced |
| **Best For** | Traditional ML | Variable Traffic | Large LLMs |
| **Cost Efficiency** | ⭐⭐ Good | ⭐⭐⭐ Great | ⭐⭐⭐ Great |

### When to Use Each Mode

```mermaid
flowchart LR
    subgraph "Raw Kubernetes"
        Raw[Use When:<br/>- Steady traffic<br/>- Traditional ML<br/>- Simple setup<br/>- Predictable costs]
    end
    
    subgraph "Serverless"
        Server[Use When:<br/>- Variable traffic<br/>- Need scale-to-zero<br/>- Complex pipelines<br/>- Traffic splitting]
    end
    
    subgraph "LLM-D"
        LLM[Use When:<br/>- Large LLMs 7B+<br/>- Need caching<br/>- Distributed inference<br/>- P/D optimization]
    end
    
    style Raw fill:#c8e6c9
    style Server fill:#a5d6a7
    style LLM fill:#ffd93d
```

---

## Complete End-to-End Flow

### From Model to Production

```mermaid
flowchart TB
    subgraph "Phase 1: Model Creation"
        Train[Data Scientist<br/>Trains Model] --> Export[Export Model<br/>Files]
        Export --> Upload[Upload to<br/>Storage<br/>S3/HF/PVC]
    end
    
    subgraph "Phase 2: Registration"
        Upload --> Register[Register in<br/>ODH Registry]
        Register --> Metadata[Add Metadata<br/>- Name, Version<br/>- Framework<br/>- Metrics]
    end
    
    subgraph "Phase 3: Configuration"
        Metadata --> SelectMode{Choose<br/>Deployment Mode}
        SelectMode -->|Raw| ConfigRaw[Configure:<br/>- Resources<br/>- HPA<br/>- Replicas]
        SelectMode -->|Serverless| ConfigServer[Configure:<br/>- Scale-to-zero<br/>- KPA<br/>- Traffic Split]
        SelectMode -->|LLM-D| ConfigLLMD[Configure:<br/>- P/D Settings<br/>- Cache<br/>- Multi-node]
    end
    
    subgraph "Phase 4: Deployment"
        ConfigRaw --> CreateISVC[Create<br/>InferenceService]
        ConfigServer --> CreateISVC
        ConfigLLMD --> CreateISVC
        
        CreateISVC --> KServe[KServe Controller<br/>Processes]
        KServe --> CreatePods[Create Model<br/>Pods]
    end
    
    subgraph "Phase 5: Initialization"
        CreatePods --> Download[Download Model<br/>from Storage]
        Download --> LoadModel[Load Model<br/>into Memory/GPU]
        LoadModel --> HealthCheck[Health Check<br/>Passes]
    end
    
    subgraph "Phase 6: Service Registration"
        HealthCheck --> RegisterRouter{Mode?}
        RegisterRouter -->|Raw/Serverless| K8sService[Register K8s<br/>Service]
        RegisterRouter -->|LLM-D| LLMDReg[Register with:<br/>- Router<br/>- Scheduler<br/>- Monitor]
    end
    
    subgraph "Phase 7: Production"
        K8sService --> Ready[✅ Ready to<br/>Serve Traffic]
        LLMDReg --> Ready
        
        Ready --> Users[Users Can<br/>Make Requests]
    end
    
    subgraph "Phase 8: Operation"
        Users --> Monitor[Continuous<br/>Monitoring]
        Monitor --> Metrics[Collect Metrics:<br/>- Latency<br/>- Throughput<br/>- Errors]
        Metrics --> Auto{Auto-scaling<br/>Needed?}
        Auto -->|Yes| Scale[Scale Up/Down]
        Auto -->|No| Monitor
        Scale --> Monitor
    end
    
    style Train fill:#e1bee7
    style Register fill:#c5cae9
    style SelectMode fill:#fff4e1
    style CreateISVC fill:#b2dfdb
    style HealthCheck fill:#ffe0b2
    style Ready fill:#a5d6a7
    style Monitor fill:#c5cae9
```

### User Request Flow (All Modes)

```mermaid
flowchart TB
    User[User<br/>Sends Request] --> Gateway[API Gateway<br/>Entry Point]
    
    Gateway --> Mode{Deployment<br/>Mode?}
    
    Mode -->|Raw K8s| RawFlow[Direct to<br/>K8s Service]
    Mode -->|Serverless| ServerFlow[Knative<br/>Routing]
    Mode -->|LLM-D| LLMDFlow[Router<br/>Sidecar]
    
    RawFlow --> HPA{Pod<br/>Available?}
    HPA -->|Yes| RawPod[Model Pod]
    HPA -->|No| ScaleRaw[HPA Scales Up]
    ScaleRaw --> RawPod
    
    ServerFlow --> KPA{Pod<br/>Available?}
    KPA -->|Yes| ServerPod[Model Pod]
    KPA -->|Cold Start| Activate[Knative<br/>Activates Pod]
    Activate --> ServerPod
    
    LLMDFlow --> Router[Router Checks<br/>Cache]
    Router --> CacheHit{Cache<br/>Hit?}
    CacheHit -->|Yes| FastReturn[⚡ Return<br/>Cached]
    CacheHit -->|No| Schedule[Scheduler<br/>Picks Pod]
    Schedule --> LLMDPod[Best Pod]
    
    RawPod --> Process[Run<br/>Inference]
    ServerPod --> Process
    LLMDPod --> Process
    
    Process --> Response[Generate<br/>Response]
    
    Response --> ReturnPath{Return<br/>Path}
    
    ReturnPath --> |Raw| DirectReturn[Direct to<br/>User]
    ReturnPath --> |Serverless| KnativeReturn[Via Knative]
    ReturnPath --> |LLM-D| RouterReturn[Via Router<br/>+ Cache]
    
    DirectReturn --> End[User Gets<br/>Response]
    KnativeReturn --> End
    RouterReturn --> End
    FastReturn --> End
    
    style User fill:#e1f5ff
    style Gateway fill:#c5cae9
    style Mode fill:#fff4e1
    style RawFlow fill:#c8e6c9
    style ServerFlow fill:#a5d6a7
    style LLMDFlow fill:#ffd93d
    style FastReturn fill:#81c784
    style Process fill:#b2dfdb
    style End fill:#a5d6a7
```

---

## Component Interaction Flows

### Model Deployment Interaction

```mermaid
flowchart TB
    DS[Data Scientist] --> ODH[ODH Controller]
    ODH --> Validate[Validate Config]
    
    Validate --> Registry[Model Registry]
    Registry --> Store[Store Metadata]
    
    Store --> ODH2[ODH Controller]
    ODH2 --> CreateISVC[Create<br/>InferenceService CR]
    
    CreateISVC --> KServe[KServe Controller]
    KServe --> Webhook[Validation Webhook]
    Webhook --> Defaults[Apply Defaults]
    
    Defaults --> Runtime[Resolve Runtime]
    Runtime --> Mode{Mode?}
    
    Mode -->|Raw| K8sDeploy[Create K8s<br/>Deployment]
    Mode -->|Serverless| KnativeDeploy[Create Knative<br/>Service]
    Mode -->|LLM-D| LLMDDeploy[Create LLM-D<br/>Components]
    
    K8sDeploy --> K8sAPI[Kubernetes API]
    KnativeDeploy --> KnativeAPI[Knative API]
    LLMDDeploy --> LLMDComponents[Router + Scheduler]
    
    K8sAPI --> Pods[Schedule Pods]
    KnativeAPI --> Pods
    LLMDComponents --> Pods
    
    Pods --> Storage[Download from<br/>Storage]
    Storage --> Load[Load Model]
    Load --> Ready[Pod Ready]
    
    Ready --> Register{Mode?}
    Register -->|LLM-D| RouterReg[Register with<br/>Router & Scheduler]
    Register -->|Other| K8sReg[Register with<br/>K8s Service]
    
    RouterReg --> Live[LIVE]
    K8sReg --> Live
    
    Live --> Monitor[ODH Monitors]
    Monitor --> UpdateRegistry[Update Registry<br/>Status]
    
    style DS fill:#e1bee7
    style ODH fill:#ffccbc
    style KServe fill:#c8e6c9
    style Pods fill:#b2dfdb
    style Live fill:#a5d6a7
    style Monitor fill:#c5cae9
```

### Autoscaling Interaction

```mermaid
flowchart TB
    Metrics[Prometheus<br/>Collects Metrics] --> Analyze[Analyze:<br/>- Request Rate<br/>- Queue Length<br/>- Resource Usage]
    
    Analyze --> Mode{Deployment<br/>Mode?}
    
    Mode -->|Raw K8s| HPA[HPA Evaluates<br/>Metrics]
    Mode -->|Serverless| KPA[KPA Evaluates<br/>Metrics]
    Mode -->|LLM-D| Custom[Custom Scheduler<br/>Evaluates]
    
    HPA --> HPADecision{Scale<br/>Needed?}
    HPADecision -->|Up| HPAScale[HPA Scales<br/>Deployment]
    HPADecision -->|Down| HPAScale
    HPADecision -->|No| HPA
    
    KPA --> KPADecision{Scale<br/>Needed?}
    KPADecision -->|Up| KPAScale[KPA Scales<br/>KService]
    KPADecision -->|Down| KPAScale
    KPADecision -->|To Zero| ScaleZero[Scale to 0]
    KPADecision -->|No| KPA
    
    Custom --> CustomDecision{Scale<br/>Needed?}
    CustomDecision -->|Up| CustomScale[Create More<br/>Pods]
    CustomDecision -->|Down| CustomScale
    CustomDecision -->|No| Custom
    
    HPAScale --> K8sAPI[Kubernetes API]
    KPAScale --> K8sAPI
    ScaleZero --> K8sAPI
    CustomScale --> K8sAPI
    
    K8sAPI --> Pods[Adjust Pod<br/>Count]
    
    Pods --> Register[Register New<br/>Backends]
    
    Register --> NewMetrics[Collect New<br/>Metrics]
    NewMetrics --> Metrics
    
    style Metrics fill:#c5cae9
    style Analyze fill:#fff4e1
    style Mode fill:#ffe0b2
    style HPA fill:#c8e6c9
    style KPA fill:#a5d6a7
    style Custom fill:#ffd93d
    style K8sAPI fill:#b2dfdb
    style Pods fill:#c8e6c9
```

---

## Decision Trees

### Choosing Deployment Mode

```mermaid
flowchart TB
    Start{What are you<br/>deploying?}
    
    Start -->|LLM 7B+| LLM[Large Language<br/>Model]
    Start -->|Traditional ML| ML[Traditional<br/>ML Model]
    
    LLM --> LLMSize{Model<br/>Size?}
    LLMSize -->|Fits Single GPU| SingleGPU{Need Cache<br/>Optimization?}
    LLMSize -->|Needs Multiple GPUs| MultiGPU[✅ LLM-D Mode<br/>Distributed]
    
    SingleGPU -->|Yes| LLMD1[✅ LLM-D Mode]
    SingleGPU -->|No| ServerlessLLM[✅ Serverless Mode<br/>with GPU]
    
    ML --> Traffic{Traffic<br/>Pattern?}
    Traffic -->|Variable/Unpredictable| Variable[Variable Traffic]
    Traffic -->|Steady/Predictable| Steady[Steady Traffic]
    Traffic -->|Bursty| Bursty[Bursty Traffic]
    
    Variable --> NeedZero{Need to Scale<br/>to Zero?}
    NeedZero -->|Yes| Server1[✅ Serverless Mode]
    NeedZero -->|No| Raw1[✅ Raw K8s Mode]
    
    Steady --> Simple{Need Simple<br/>Setup?}
    Simple -->|Yes| Raw2[✅ Raw K8s Mode]
    Simple -->|No| Complex{Complex<br/>Pipeline?}
    
    Complex -->|Yes| RawOrServer[✅ Raw or Serverless<br/>Both support InferenceGraph]
    Complex -->|No| Raw3[✅ Raw K8s Mode]
    
    Bursty --> Server3[✅ Serverless Mode]
    
    style Start fill:#e1f5ff
    style LLM fill:#ffe0b2
    style ML fill:#c8e6c9
    style LLMD1 fill:#ffd93d
    style MultiGPU fill:#ffd93d
    style ServerlessLLM fill:#a5d6a7
    style Server1 fill:#a5d6a7
    style Server2 fill:#a5d6a7
    style Server3 fill:#a5d6a7
    style Raw1 fill:#81c784
    style Raw2 fill:#81c784
    style Raw3 fill:#81c784
```

### Choosing Autoscaling Strategy

```mermaid
flowchart TB
    Start{Autoscaling<br/>Requirements?}
    
    Start --> Zero{Need<br/>Scale-to-Zero?}
    
    Zero -->|Yes| MustServerless[Must Use<br/>Serverless Mode]
    Zero -->|No| Metrics{Primary<br/>Metric?}
    
    MustServerless --> KPA[Use KPA<br/>Knative Pod Autoscaler]
    
    Metrics -->|Request Rate| UseKPA{Using<br/>Serverless?}
    Metrics -->|CPU/Memory| HPA1[✅ Use HPA]
    Metrics -->|Custom Metrics| Custom1[✅ Custom HPA<br/>with Metrics]
    
    UseKPA -->|Yes| KPA
    UseKPA -->|No| RPS[✅ HPA with<br/>RPS Metric]
    
    KPA --> Config1[Configure:<br/>- Target Concurrency<br/>- Scale-down Delay<br/>- Min/Max Replicas]
    
    HPA1 --> Config2[Configure:<br/>- Target CPU %<br/>- Target Memory %<br/>- Min/Max Replicas]
    
    RPS --> Config3[Configure:<br/>- Target RPS<br/>- Stabilization Window<br/>- Min/Max Replicas]
    
    Custom1 --> Config4[Configure:<br/>- Custom Metric<br/>- Target Value<br/>- Metrics Server]
    
    Config1 --> Review[Review & Apply]
    Config2 --> Review
    Config3 --> Review
    Config4 --> Review
    
    Review --> Test[Test Scaling<br/>Behavior]
    
    Test --> Tune{Needs<br/>Tuning?}
    Tune -->|Yes| Adjust[Adjust Parameters]
    Tune -->|No| Done[✅ Ready for<br/>Production]
    
    Adjust --> Test
    
    style Start fill:#e1f5ff
    style Zero fill:#fff4e1
    style MustServerless fill:#ffe0b2
    style KPA fill:#a5d6a7
    style HPA1 fill:#c8e6c9
    style Custom1 fill:#fff9c4
    style Done fill:#81c784
```

---

## Summary

### Key Takeaways

1. **Three Deployment Modes**: Raw K8s (simple), Serverless (flexible), LLM-D (optimized for LLMs)
2. **All Components Work Together**: ODH Controller → KServe → Deployment Mode → Running Pods
3. **Autoscaling is Automatic**: HPA, KPA, or Custom depending on mode
4. **LLM-D Adds Intelligence**: Cache-aware routing, P/D disaggregation, distributed inference
5. **Choose Based on Needs**: Use decision trees to pick the right mode

### Quick Reference

| Need | Use |
|------|-----|
| Simple deployment | Raw K8s |
| Variable traffic | Serverless |
| Scale-to-zero | Serverless |
| Large LLMs | LLM-D |
| Cache optimization | LLM-D |
| Complex pipelines | Serverless |
| Multi-GPU models | LLM-D |

### Next Steps

- **For Raw K8s**: Read [RAW-KUBERNETES-DEPLOYMENT.md](./RAW-KUBERNETES-DEPLOYMENT.md)
- **For Serverless**: Read [SERVERLESS-DEPLOYMENT.md](./SERVERLESS-DEPLOYMENT.md)
- **For LLM-D**: Read [LLM-D-DEPLOYMENT.md](./LLM-D-DEPLOYMENT.md)

---

**Document Version**: 1.0  
**Last Updated**: October 27, 2025  
**Status**: ✅ 100% Complete - All Components Covered

