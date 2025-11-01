# Raw Kubernetes Deployment - Complete Guide

## 📋 Table of Contents
1. [What is Raw K8s Mode](#what-is-raw-k8s-mode)
2. [When to Use Raw K8s](#when-to-use-raw-k8s)
3. [Architecture & Components](#architecture--components)
4. [Complete Deployment Flow](#complete-deployment-flow)
5. [All Features Explained](#all-features-explained)
   - Feature 1: HPA Autoscaling
   - Feature 2: Storage Backends
   - Feature 3: Multi-Model Serving
   - Feature 4: GPU Support
   - Feature 5: Health Checks
   - Feature 6: Resource Management
   - Feature 7: Transformer & Explainer (NEW!)
   - Feature 8: InferenceGraph Support (NEW!)
6. [Configuration Examples](#configuration-examples)
7. [Troubleshooting](#troubleshooting)

---

## What is Raw K8s Mode

### Simple Explanation

Raw Kubernetes mode means deploying your model as a **standard Kubernetes Deployment** - no serverless, no special features, just straightforward K8s resources. Think of it as the "traditional" way.

### Key Characteristics

```mermaid
flowchart LR
    subgraph "Raw K8s Mode"
        Simple[✅ Simple Setup]
        Predict[✅ Predictable]
        Always[✅ Always Running]
        Basic[✅ Basic Autoscaling]
        NoZero[❌ No Scale-to-Zero]
    end
    
    style Simple fill:#c8e6c9
    style Predict fill:#c8e6c9
    style Always fill:#c8e6c9
    style Basic fill:#fff9c4
    style NoZero fill:#ffccbc
```

### What You Get

- Standard Kubernetes **Deployment**
- Standard Kubernetes **Service**
- Horizontal Pod Autoscaler (**HPA**)
- ConfigMaps and Secrets
- Resource limits and requests
- Node selectors and tolerations
- Health checks (liveness & readiness)

### What You Don't Get

- Scale-to-zero (pods always running)
- Advanced autoscaling (only HPA, no KPA)
- Automatic traffic splitting (Canary/Blue-Green)
- Knative Serving features

---

## When to Use Raw K8s

### Decision Flowchart

```mermaid
flowchart TB
    Start{Do you need<br/>Raw K8s?} --> Traffic{Traffic<br/>Pattern?}
    
    Traffic -->|Steady & Predictable| Yes1[✅ Good Fit]
    Traffic -->|Variable| Check1{Can you afford<br/>always-on pods?}
    Traffic -->|Bursty| No1[❌ Use Serverless]
    
    Check1 -->|Yes| Yes2[✅ Can Use]
    Check1 -->|No| No2[❌ Use Serverless]
    
    Yes1 --> Setup{Need Simple<br/>Setup?}
    Yes2 --> Setup
    
    Setup -->|Yes| Perfect[✅ Perfect Fit<br/>Raw K8s]
    Setup -->|No| Complex{Need Scale<br/>to Zero?}
    
    Complex -->|Yes| UseServerless[❌ Use Serverless]
    Complex -->|No| Perfect
    
    No1 --> End1[Use Serverless Mode]
    No2 --> End1
    UseServerless --> End1
    
    Perfect --> End2[✅ Use Raw K8s]
    
    style Yes1 fill:#c8e6c9
    style Yes2 fill:#c8e6c9
    style Perfect fill:#a5d6a7
    style No1 fill:#ffccbc
    style No2 fill:#ffccbc
    style UseServerless fill:#ffccbc
    style End2 fill:#81c784
```

### Use Cases

| Scenario | Why Raw K8s? |
|----------|--------------|
| **Production API** with steady traffic | Predictable load, always-on is fine |
| **Internal ML service** used 24/7 | No need for scale-to-zero |
| **Traditional ML models** (SKLearn, XGBoost) | Simple deployment sufficient |
| **Cost-predictable** workloads | Know exact pod count |
| **Simple architecture** preferred | No complexity needed |

### Don't Use When

| Scenario | Use Instead |
|----------|-------------|
| Variable/bursty traffic | **Serverless Mode** |
| Need scale-to-zero | **Serverless Mode** |
| Need traffic splitting (Canary) | **Serverless Mode** |
| Large LLMs needing optimization | **LLM-D Mode** |

---

## Architecture & Components

### Raw K8s Architecture

```mermaid
flowchart TB
    subgraph "User Layer"
        User[Users/Applications]
    end
    
    subgraph "Network Layer"
        Ingress[Ingress Controller]
        Service[Kubernetes Service]
    end
    
    subgraph "Control Plane"
        KServe[KServe Controller]
        HPA[Horizontal Pod<br/>Autoscaler]
    end
    
    subgraph "Data Plane"
        Deployment[Kubernetes<br/>Deployment]
        Pod1[Pod 1<br/>Model Container]
        Pod2[Pod 2<br/>Model Container]
        Pod3[Pod 3<br/>Model Container]
    end
    
    subgraph "Storage"
        S3[S3/MinIO]
        PVC[Persistent Volume]
        HuggingFace[HuggingFace Hub]
    end
    
    subgraph "Monitoring"
        Prometheus[Prometheus]
        Metrics[Metrics]
    end
    
    User -->|HTTP Request| Ingress
    Ingress --> Service
    Service --> Pod1
    Service --> Pod2
    Service --> Pod3
    
    KServe -->|Creates| Deployment
    KServe -->|Creates| Service
    
    Deployment -->|Manages| Pod1
    Deployment -->|Manages| Pod2
    Deployment -->|Manages| Pod3
    
    HPA -->|Monitors| Deployment
    HPA -->|Scales| Deployment
    
    Pod1 -->|Download Model| S3
    Pod2 -->|Download Model| PVC
    Pod3 -->|Download Model| HuggingFace
    
    Pod1 -->|Export| Metrics
    Pod2 -->|Export| Metrics
    Pod3 -->|Export| Metrics
    
    Metrics --> Prometheus
    Prometheus --> HPA
    
    style User fill:#e1f5ff
    style KServe fill:#c8e6c9
    style HPA fill:#fff9c4
    style Deployment fill:#b2dfdb
    style Pod1 fill:#c8e6c9
    style Pod2 fill:#c8e6c9
    style Pod3 fill:#c8e6c9
    style Service fill:#ffe0b2
```

### Resources Created

```mermaid
flowchart TB
    ISVC[InferenceService<br/>Your YAML] --> Controller[KServe Controller<br/>Processes]
    
    Controller --> Creates{Creates<br/>Resources}
    
    Creates --> Deployment[Kubernetes<br/>Deployment]
    Creates --> Service[Kubernetes<br/>Service]
    Creates --> ConfigMap[ConfigMap<br/>Configuration]
    Creates --> Secret[Secret<br/>Credentials]
    Creates --> SA[ServiceAccount<br/>Permissions]
    Creates --> HPA[HorizontalPodAutoscaler<br/>Scaling Rules]
    
    Deployment --> Pods[Pods<br/>1 to N replicas]
    
    style ISVC fill:#e1f5ff
    style Controller fill:#c8e6c9
    style Creates fill:#fff4e1
    style Deployment fill:#b2dfdb
    style Service fill:#ffe0b2
    style ConfigMap fill:#c5cae9
    style Secret fill:#ffccbc
    style SA fill:#fff9c4
    style HPA fill:#a5d6a7
    style Pods fill:#c8e6c9
```

---

## Complete Deployment Flow

### Step-by-Step Process

```mermaid
flowchart TB
    Start([Start:<br/>Create InferenceService]) --> Upload[Upload Model<br/>to Storage]
    
    Upload --> CreateYAML[Write YAML<br/>Configuration]
    
    CreateYAML --> Apply[kubectl apply<br/>-f isvc.yaml]
    
    Apply --> Webhook[KServe Webhook<br/>Validates]
    
    Webhook --> Valid{Valid<br/>Config?}
    
    Valid -->|No| Error1[❌ Show Errors<br/>Fix & Retry]
    Valid -->|Yes| Controller[KServe Controller<br/>Starts Work]
    
    Error1 --> CreateYAML
    
    Controller --> Defaults[Apply Defaults:<br/>- Resources<br/>- Annotations<br/>- Labels]
    
    Defaults --> Runtime[Resolve<br/>ServingRuntime]
    
    Runtime --> CreateK8s[Create K8s<br/>Resources]
    
    CreateK8s --> Depl[1. Deployment]
    CreateK8s --> Svc[2. Service]
    CreateK8s --> CM[3. ConfigMap]
    CreateK8s --> Sec[4. Secret]
    CreateK8s --> HPACreate[5. HPA]
    
    Depl --> Schedule[K8s Scheduler<br/>Assigns Nodes]
    
    Schedule --> CreatePods[Create Pods]
    
    CreatePods --> Init[Init Container<br/>storage-initializer]
    
    Init --> Download{Download<br/>Model}
    
    Download -->|S3| DL1[Download from S3]
    Download -->|PVC| DL2[Mount PVC]
    Download -->|HF| DL3[Download from HuggingFace]
    
    DL1 --> Extract[Extract to<br/>/mnt/models]
    DL2 --> Extract
    DL3 --> Extract
    
    Extract --> MainContainer[Start Main<br/>Container]
    
    MainContainer --> LoadModel[Load Model<br/>into Memory]
    
    LoadModel --> GPU{GPU<br/>Requested?}
    
    GPU -->|Yes| LoadGPU[Load to<br/>GPU Memory]
    GPU -->|No| LoadCPU[Keep in<br/>RAM]
    
    LoadGPU --> Warmup[Warmup<br/>Inference]
    LoadCPU --> Warmup
    
    Warmup --> Health[Health Check]
    
    Health --> Ready{Ready?}
    
    Ready -->|No| Wait[Wait & Retry]
    Ready -->|Yes| UpdateStatus[Update Status<br/>Ready=True]
    
    Wait --> Health
    
    UpdateStatus --> RegisterSvc[Register with<br/>K8s Service]
    
    RegisterSvc --> Live[✅ LIVE!<br/>Accepting Traffic]
    
    Live --> Monitor[HPA Monitors<br/>Metrics]
    
    Monitor --> Scale{Scaling<br/>Needed?}
    
    Scale -->|Up| ScaleUp[Add Pods]
    Scale -->|Down| ScaleDown[Remove Pods]
    Scale -->|No Change| Monitor
    
    ScaleUp --> Monitor
    ScaleDown --> Monitor
    
    style Start fill:#e1f5ff
    style Upload fill:#c5cae9
    style Apply fill:#fff9c4
    style Valid fill:#fff4e1
    style Error1 fill:#ffcdd2
    style Controller fill:#c8e6c9
    style CreateK8s fill:#b2dfdb
    style Download fill:#ffe0b2
    style Extract fill:#c5cae9
    style LoadModel fill:#fff9c4
    style Health fill:#ffe0b2
    style Ready fill:#fff4e1
    style UpdateStatus fill:#c8e6c9
    style Live fill:#a5d6a7
    style Monitor fill:#c5cae9
```

### Example: Deploying SKLearn Model

**Time**: ~2-3 minutes

**Step 1**: Upload model to S3
```bash
aws s3 cp my-model.pkl s3://my-bucket/models/sklearn/my-model/
```

**Step 2**: Create InferenceService YAML
```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sklearn-iris
  namespace: models
  annotations:
    serving.kserve.io/deploymentMode: "RawDeployment"
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: s3://my-bucket/models/sklearn/my-model
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
        limits:
          cpu: "1"
          memory: "2Gi"
    minReplicas: 2
    maxReplicas: 5
```

**Step 3**: Apply
```bash
kubectl apply -f sklearn-iris.yaml
```

**Step 4**: Wait for Ready
```bash
kubectl wait --for=condition=Ready inferenceservice/sklearn-iris -n models
```

**Step 5**: Test
```bash
kubectl port-forward svc/sklearn-iris-predictor-default 8080:80 -n models

curl -X POST http://localhost:8080/v1/models/sklearn-iris:predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [[5.1, 3.5, 1.4, 0.2]]}'
```

---

## All Features Explained

### Feature 1: HPA Autoscaling

**What it does**: Automatically adds/removes pods based on metrics

```mermaid
flowchart TB
    Start[HPA Monitors<br/>Metrics] --> Check[Check Every<br/>15 seconds]
    
    Check --> Metrics{Current<br/>Metrics}
    
    Metrics --> CPU[CPU Usage:<br/>Current vs Target]
    Metrics --> Memory[Memory Usage:<br/>Current vs Target]
    Metrics --> Custom[Custom Metrics:<br/>If configured]
    
    CPU --> Calculate[Calculate Desired<br/>Replicas]
    Memory --> Calculate
    Custom --> Calculate
    
    Calculate --> Formula[Formula:<br/>desiredReplicas = <br/>currentReplicas × <br/>(currentMetric / targetMetric)]
    
    Formula --> Compare{Compare<br/>to Current}
    
    Compare -->|Need More| ScaleUp[Scale UP]
    Compare -->|Need Less| ScaleDown[Scale DOWN]
    Compare -->|Just Right| NoChange[No Change]
    
    ScaleUp --> Within{Within<br/>min/max?}
    ScaleDown --> Within
    
    Within -->|Yes| Apply[Apply Change]
    Within -->|No| Limit[Apply at<br/>Limit]
    
    Apply --> Update[Update<br/>Deployment]
    Limit --> Update
    
    Update --> Wait[Wait Stabilization<br/>Window: 3 min]
    NoChange --> Start
    
    Wait --> Start
    
    style Start fill:#c5cae9
    style Metrics fill:#fff4e1
    style Calculate fill:#fff9c4
    style Compare fill:#ffe0b2
    style ScaleUp fill:#ffccbc
    style ScaleDown fill:#c8e6c9
    style Apply fill:#a5d6a7
    style Update fill:#b2dfdb
```

**Configuration Example**:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: model-with-hpa
  annotations:
    serving.kserve.io/deploymentMode: "RawDeployment"
    autoscaling.knative.dev/class: "hpa.autoscaling.knative.dev"
    autoscaling.knative.dev/metric: "cpu"
    autoscaling.knative.dev/target: "70"
spec:
  predictor:
    minReplicas: 2
    maxReplicas: 10
    model:
      modelFormat:
        name: sklearn
      storageUri: s3://bucket/model
```

**What happens**:
1. HPA monitors CPU usage
2. Target: 70% CPU
3. If CPU > 70%: Scale up
4. If CPU < 70%: Scale down
5. Min 2 pods, Max 10 pods

---

### Feature 2: Storage Backends

**What it does**: Load models from various storage systems

```mermaid
flowchart TB
    Model[Your Model<br/>Files] --> Choose{Choose<br/>Storage}
    
    Choose --> S3Option[☁️ S3/MinIO<br/>Cloud Storage]
    Choose --> PVCOption[💾 PersistentVolume<br/>K8s Storage]
    Choose --> HFOption[🤗 HuggingFace<br/>Model Hub]
    Choose --> AzureOption[🔷 Azure Blob<br/>Azure Storage]
    Choose --> GCSOption[🌐 Google Cloud<br/>Storage]
    Choose --> HTTPOption[📥 HTTP/HTTPS<br/>Direct Download]
    
    S3Option --> Config1[storageUri:<br/>s3://bucket/model]
    PVCOption --> Config2[storageUri:<br/>pvc://pvc-name/path]
    HFOption --> Config3[storageUri:<br/>hf://org/model-name]
    AzureOption --> Config4[storageUri:<br/>https://account.blob...]
    GCSOption --> Config5[storageUri:<br/>gs://bucket/model]
    HTTPOption --> Config6[storageUri:<br/>https://server/model.tar.gz]
    
    Config1 --> Init[storage-initializer<br/>Downloads]
    Config2 --> Mount[Direct Mount<br/>No Download]
    Config3 --> Init
    Config4 --> Init
    Config5 --> Init
    Config6 --> Init
    
    Init --> Extract[Extract to<br/>/mnt/models]
    Mount --> Ready[Model Ready]
    Extract --> Ready
    
    Ready --> Container[Main Container<br/>Loads Model]
    
    style Model fill:#e1f5ff
    style Choose fill:#fff4e1
    style S3Option fill:#bbdefb
    style PVCOption fill:#c8e6c9
    style HFOption fill:#fff9c4
    style Init fill:#c5cae9
    style Mount fill:#a5d6a7
    style Ready fill:#b2dfdb
```

**Example Configurations**:

**S3/MinIO**:
```yaml
spec:
  predictor:
    model:
      storageUri: s3://my-bucket/models/my-model
      env:
      - name: AWS_ACCESS_KEY_ID
        valueFrom:
          secretKeyRef:
            name: s3-creds
            key: AWS_ACCESS_KEY_ID
      - name: AWS_SECRET_ACCESS_KEY
        valueFrom:
          secretKeyRef:
            name: s3-creds
            key: AWS_SECRET_ACCESS_KEY
```

**PersistentVolumeClaim**:
```yaml
spec:
  predictor:
    model:
      storageUri: pvc://model-storage/my-model
```

**HuggingFace**:
```yaml
spec:
  predictor:
    model:
      storageUri: hf://meta-llama/Llama-2-7b-hf
      env:
      - name: HUGGING_FACE_HUB_TOKEN
        valueFrom:
          secretKeyRef:
            name: hf-token
            key: token
```

---

### Feature 3: Multi-Model Serving

**What it does**: Serve multiple models from a single server instance

```mermaid
flowchart TB
    Start[Deploy Empty<br/>Model Server] --> ISVC[Create InferenceService<br/>NO storageUri]
    
    ISVC --> Server[Model Server<br/>Running Empty]
    
    Server --> Ready[Server Ready<br/>Waiting for Models]
    
    Ready --> Deploy1[Deploy Model 1<br/>TrainedModel CR]
    Ready --> Deploy2[Deploy Model 2<br/>TrainedModel CR]
    Ready --> Deploy3[Deploy Model 3<br/>TrainedModel CR]
    
    Deploy1 --> CM1[Update ConfigMap]
    Deploy2 --> CM2[Update ConfigMap]
    Deploy3 --> CM3[Update ConfigMap]
    
    CM1 --> Agent[Model Agent<br/>Watches ConfigMap]
    CM2 --> Agent
    CM3 --> Agent
    
    Agent --> DL{Download<br/>Models}
    
    DL --> DL1[Download Model 1]
    DL --> DL2[Download Model 2]
    DL --> DL3[Download Model 3]
    
    DL1 --> Load[Load into<br/>Server]
    DL2 --> Load
    DL3 --> Load
    
    Load --> Endpoints[Multiple Endpoints:<br/>/v2/models/model1/infer<br/>/v2/models/model2/infer<br/>/v2/models/model3/infer]
    
    Endpoints --> Usage[Track Usage]
    
    Usage --> Monitor{Monitor<br/>Usage}
    
    Monitor -->|Unused| Unload[Auto-unload<br/>Model]
    Monitor -->|Active| Keep[Keep Loaded]
    
    Unload --> FreeMemory[Free Memory]
    FreeMemory --> Agent
    
    Keep --> Monitor
    
    style Start fill:#e1f5ff
    style ISVC fill:#c5cae9
    style Server fill:#b2dfdb
    style Ready fill:#fff9c4
    style Deploy1 fill:#bbdefb
    style Deploy2 fill:#c8e6c9
    style Deploy3 fill:#ffe0b2
    style Agent fill:#c5cae9
    style Load fill:#fff9c4
    style Endpoints fill:#a5d6a7
    style Usage fill:#c5cae9
```

**Configuration**:

**Step 1**: Create empty InferenceService
```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: multi-model-server
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      protocolVersion: v2
      runtime: kserve-mlserver
      # NO storageUri - empty server
```

**Step 2**: Deploy individual models
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: TrainedModel
metadata:
  name: fraud-model
spec:
  inferenceService: multi-model-server
  model:
    modelFormat:
      name: sklearn
    storageUri: s3://bucket/fraud-model
    memory: 1Gi
---
apiVersion: serving.kserve.io/v1alpha1
kind: TrainedModel
metadata:
  name: churn-model
spec:
  inferenceService: multi-model-server
  model:
    modelFormat:
      name: sklearn
    storageUri: s3://bucket/churn-model
    memory: 1Gi
```

**Benefits**:
- **Resource Efficiency**: One server, multiple models
- **Cost Reduction**: Shared overhead
- **Dynamic Loading**: Load/unload on demand
- **Higher Density**: More models per node

---

### Feature 4: GPU Support

**What it does**: Schedule models on GPU nodes

```mermaid
flowchart TB
    Request[Request GPU<br/>in YAML] --> Check[K8s Scheduler<br/>Checks]
    
    Check --> Available{GPU<br/>Available?}
    
    Available -->|Yes| Assign[Assign GPU<br/>to Pod]
    Available -->|No| Queue[Wait in<br/>Pending]
    
    Queue --> Retry[Retry when<br/>GPU Free]
    Retry --> Available
    
    Assign --> Bind[Bind to<br/>GPU Node]
    
    Bind --> Exclusive{GPU<br/>Mode?}
    
    Exclusive -->|Exclusive| FullGPU[Entire GPU<br/>for Pod]
    Exclusive -->|Shared| SharedGPU[Shared GPU<br/>Time-slicing]
    Exclusive -->|MIG| MIGSlice[MIG Partition<br/>Fixed Slice]
    
    FullGPU --> LoadModel[Load Model<br/>to GPU]
    SharedGPU --> LoadModel
    MIGSlice --> LoadModel
    
    LoadModel --> Ready[Ready to<br/>Infer]
    
    Ready --> Monitor[Monitor<br/>GPU Usage]
    
    Monitor --> Metrics[GPU Metrics:<br/>- Utilization %<br/>- Memory Usage<br/>- Temperature]
    
    Metrics --> Prometheus[Export to<br/>Prometheus]
    
    style Request fill:#e1f5ff
    style Check fill:#fff4e1
    style Available fill:#ffe0b2
    style Queue fill:#ffccbc
    style Assign fill:#c8e6c9
    style Exclusive fill:#fff9c4
    style FullGPU fill:#bbdefb
    style SharedGPU fill:#c8e6c9
    style MIGSlice fill:#ffe0b2
    style LoadModel fill:#b2dfdb
    style Ready fill:#a5d6a7
    style Monitor fill:#c5cae9
```

**Configuration**:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: gpu-model
spec:
  predictor:
    model:
      modelFormat:
        name: pytorch
      storageUri: s3://bucket/pytorch-model
      resources:
        requests:
          cpu: "4"
          memory: "8Gi"
          nvidia.com/gpu: "1"      # Request 1 GPU
        limits:
          cpu: "8"
          memory: "16Gi"
          nvidia.com/gpu: "1"       # Limit 1 GPU
      nodeSelector:
        nvidia.com/gpu.product: NVIDIA-A100-SXM4-80GB  # Specific GPU
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
```

**GPU Selection**:
- Use `nodeSelector` to pick specific GPU types
- Use `tolerations` for GPU taints
- Request exact GPU count needed
- Monitor GPU utilization

---

### Feature 5: Health Checks

**What it does**: Monitors pod health and restarts if needed

```mermaid
flowchart TB
    Pod[Pod Running] --> Probes{Health<br/>Probes}
    
    Probes --> Liveness[Liveness Probe<br/>Is process alive?]
    Probes --> Readiness[Readiness Probe<br/>Ready for traffic?]
    Probes --> Startup[Startup Probe<br/>Has started?]
    
    Liveness --> LiveCheck[Check Every<br/>10 seconds]
    LiveCheck --> LiveTest[GET /health/live]
    
    LiveTest --> LiveResult{Response?}
    LiveResult -->|200 OK| LivePass[✅ Pass]
    LiveResult -->|Error/Timeout| LiveFail{Failures?}
    
    LiveFail -->|< Threshold| Retry1[Retry]
    LiveFail -->|≥ Threshold| Kill[❌ Kill Pod]
    
    Retry1 --> LiveCheck
    Kill --> Restart[Restart Pod]
    Restart --> Pod
    
    Readiness --> ReadyCheck[Check Every<br/>5 seconds]
    ReadyCheck --> ReadyTest[GET /health/ready]
    
    ReadyTest --> ReadyResult{Response?}
    ReadyResult -->|200 OK| ReadyPass[✅ Ready<br/>Serve Traffic]
    ReadyResult -->|Error| ReadyFail[❌ Not Ready<br/>Remove from Service]
    
    ReadyFail --> ReadyCheck
    
    Startup --> StartCheck[Check Every<br/>5 seconds]
    StartCheck --> StartTest[GET /health/startup]
    
    StartTest --> StartResult{Response?}
    StartResult -->|200 OK| StartPass[✅ Started<br/>Enable Other Probes]
    StartResult -->|Timeout| StartFail[❌ Failed to Start]
    
    StartFail --> Restart
    
    LivePass --> Continue[Continue<br/>Monitoring]
    ReadyPass --> Continue
    StartPass --> Continue
    
    Continue --> Probes
    
    style Pod fill:#c8e6c9
    style Probes fill:#fff4e1
    style Liveness fill:#bbdefb
    style Readiness fill:#c8e6c9
    style Startup fill:#ffe0b2
    style LivePass fill:#a5d6a7
    style ReadyPass fill:#a5d6a7
    style StartPass fill:#a5d6a7
    style LiveFail fill:#ffccbc
    style Kill fill:#ffcdd2
    style Restart fill:#ffe0b2
```

**Configuration**:

```yaml
spec:
  predictor:
    containers:
    - name: kserve-container
      livenessProbe:
        httpGet:
          path: /v1/models/<model-name>
          port: 8080
        initialDelaySeconds: 30
        periodSeconds: 10
        timeoutSeconds: 5
        failureThreshold: 3
      readinessProbe:
        httpGet:
          path: /v1/models/<model-name>
          port: 8080
        initialDelaySeconds: 10
        periodSeconds: 5
        timeoutSeconds: 5
        successThreshold: 1
      startupProbe:
        httpGet:
          path: /v1/models/<model-name>
          port: 8080
        initialDelaySeconds: 0
        periodSeconds: 5
        timeoutSeconds: 5
        failureThreshold: 60  # 5 min total
```

---

### Feature 6: Resource Management

**What it does**: Controls CPU, memory, and GPU allocation

```mermaid
flowchart TB
    Define[Define Resources<br/>in YAML] --> Types{Resource<br/>Types}
    
    Types --> CPU[CPU<br/>Requests & Limits]
    Types --> Memory[Memory<br/>Requests & Limits]
    Types --> GPU[GPU<br/>Count]
    
    CPU --> Request1[Request:<br/>Guaranteed minimum]
    CPU --> Limit1[Limit:<br/>Maximum allowed]
    
    Memory --> Request2[Request:<br/>Guaranteed minimum]
    Memory --> Limit2[Limit:<br/>Maximum allowed]
    
    GPU --> Count[Count:<br/>Exact number]
    
    Request1 --> Schedule[K8s Scheduler]
    Request2 --> Schedule
    Count --> Schedule
    
    Schedule --> FitNode{Node has<br/>resources?}
    
    FitNode -->|Yes| Assign[Assign to Node]
    FitNode -->|No| Wait[Wait for<br/>Resources]
    
    Assign --> Allocate[Allocate<br/>Resources]
    
    Allocate --> Runtime[Pod Running]
    
    Runtime --> Monitor[Monitor Usage]
    
    Monitor --> OverLimit{Exceeds<br/>Limits?}
    
    OverLimit -->|CPU| Throttle[CPU Throttled]
    OverLimit -->|Memory| OOM[OOMKilled<br/>Pod Restarted]
    OverLimit -->|No| Good[Within Limits]
    
    Throttle --> Monitor
    OOM --> Schedule
    Good --> Monitor
    
    style Define fill:#e1f5ff
    style Types fill:#fff4e1
    style CPU fill:#bbdefb
    style Memory fill:#c8e6c9
    style GPU fill:#ffe0b2
    style Schedule fill:#c5cae9
    style Assign fill:#fff9c4
    style Runtime fill:#b2dfdb
    style Monitor fill:#c5cae9
    style Good fill:#a5d6a7
    style Throttle fill:#fff9c4
    style OOM fill:#ffcdd2
```

**Configuration**:

```yaml
spec:
  predictor:
    model:
      resources:
        requests:
          cpu: "2"          # 2 CPU cores guaranteed
          memory: "4Gi"     # 4GB memory guaranteed
          nvidia.com/gpu: "1"
        limits:
          cpu: "4"          # Maximum 4 CPU cores
          memory: "8Gi"     # Maximum 8GB memory
          nvidia.com/gpu: "1"
```

**Best Practices**:
- **Requests**: Set based on typical load
- **Limits**: Set 1.5-2x requests
- **GPU**: Requests = Limits (exclusive)
- **Memory Limits**: Always set (prevent OOM)
- **CPU Limits**: Optional (allows bursting)

---

### Feature 7: Transformer & Explainer Components

**What they do**: Add preprocessing, postprocessing, and explainability to models

KServe InferenceService has 3 optional components:
1. **Predictor** (Required) - The actual model inference
2. **Transformer** (Optional) - Pre/post-processing
3. **Explainer** (Optional) - Model explanations

```mermaid
flowchart LR
    Request[User Request] --> Transform{Has<br/>Transformer?}
    
    Transform -->|Yes| Preprocess[Transformer<br/>Preprocess]
    Transform -->|No| Predictor
    
    Preprocess --> Predictor[Predictor<br/>Model Inference]
    
    Predictor --> Postprocess{Has<br/>Transformer?}
    
    Postprocess -->|Yes| PostTrans[Transformer<br/>Postprocess]
    Postprocess -->|No| Explain
    
    PostTrans --> Explain{Has<br/>Explainer?}
    
    Explain -->|Yes| Explainer[Explainer<br/>Generate Explanation]
    Explain -->|No| Response
    
    Explainer --> Response[Response with<br/>Prediction + Explanation]
    
    style Request fill:#e1f5ff
    style Preprocess fill:#fff9c4
    style Predictor fill:#c8e6c9
    style PostTrans fill:#ffe0b2
    style Explainer fill:#e1bee7
    style Response fill:#a5d6a7
```

#### Transformer Component

**Purpose**: Preprocess inputs and postprocess outputs

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sklearn-transformer
spec:
  # Transformer (optional)
  transformer:
    containers:
    - name: kserve-container
      image: myorg/image-transformer:v1
      env:
      - name: STORAGE_URI
        value: s3://bucket/transformer
  
  # Predictor (required)
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: s3://bucket/model
```

**Use Cases**:
- Image preprocessing (resize, normalize)
- Text tokenization
- Feature engineering
- Output formatting
- Protocol conversion

**Example Flow**:
```
User → [Transformer: Resize Image] → [Predictor: Classify] → [Transformer: Format JSON] → User
```

#### Explainer Component

**Purpose**: Provide model explanations for predictions

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sklearn-explainer
spec:
  # Predictor
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: s3://bucket/model
  
  # Explainer (optional)
  explainer:
    alibi:
      type: AnchorTabular
      storageUri: s3://bucket/explainer
```

**Explainer Types**:
| Type | Description | Use Case |
|------|-------------|----------|
| **AnchorTabular** | Rule-based explanations for tabular data | Credit scoring, fraud detection |
| **AnchorImages** | Image region explanations | Medical imaging, object detection |
| **AnchorText** | Text token explanations | NLP, sentiment analysis |
| **Contrastive** | What-if explanations | Decision support systems |

**Benefits**:
- 🔍 **Interpretability**: Understand model decisions
- 🛡️ **Trust**: Validate predictions
- 📊 **Debugging**: Identify model issues
- ⚖️ **Compliance**: Meet regulatory requirements (e.g., GDPR)

#### Complete Example with All Components

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: complete-pipeline
  annotations:
    serving.kserve.io/deploymentMode: "RawDeployment"
spec:
  # 1. Transformer - Preprocessing
  transformer:
    containers:
    - name: kserve-container
      image: myorg/preprocessor:v1
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
  
  # 2. Predictor - Model
  predictor:
    model:
      modelFormat:
        name: tensorflow
      storageUri: s3://models/my-model
      resources:
        requests:
          cpu: "2"
          memory: "4Gi"
        limits:
          nvidia.com/gpu: "1"
    minReplicas: 2
    maxReplicas: 5
  
  # 3. Explainer - Explanations
  explainer:
    alibi:
      type: AnchorTabular
      storageUri: s3://models/explainer
      resources:
        requests:
          cpu: "1"
          memory: "2Gi"
```

**Request Flow**:
```
1. User sends: {"data": [raw_input]}
2. Transformer: Preprocesses → {"features": [processed]}
3. Predictor: Inference → {"prediction": 0.95}
4. Explainer: Analyzes → {"explanation": "feature_x > 0.5 AND feature_y < 0.3"}
5. User receives: {
     "prediction": 0.95,
     "explanation": "feature_x > 0.5 AND feature_y < 0.3",
     "confidence": 0.95
   }
```

#### When to Use

| Component | Use When |
|-----------|----------|
| **Transformer** | Need custom preprocessing/postprocessing |
| **Explainer** | Need model interpretability |
| **Both** | Regulated industries (finance, healthcare) |
| **Neither** | Simple models with standard input/output |

---

### Feature 8: InferenceGraph Support

**What it does**: Chain multiple models into inference pipelines

**Important**: InferenceGraph works in Raw K8s mode! It uses a KServe router component deployed alongside your models.

```mermaid
flowchart TB
    Request[User Request] --> Router[KServe Router<br/>Raw Deployment]
    
    Router --> Parse[Parse Graph<br/>Nodes]
    
    Parse --> Type{Node<br/>Type}
    
    Type -->|Sequence| Seq[Sequential<br/>Execution]
    Type -->|Switch| Switch[Conditional<br/>Routing]
    Type -->|Ensemble| Ens[Parallel<br/>Execution]
    Type -->|Splitter| Split[Split &<br/>Aggregate]
    
    Seq --> Model1[Model 1]
    Seq --> Model2[Model 2]
    Model2 --> Response
    
    Switch --> Cond{Condition}
    Cond -->|Match| ModelA[Model A]
    Cond -->|No Match| ModelB[Model B]
    ModelA --> Response
    ModelB --> Response
    
    Ens --> Parallel1[Model X]
    Ens --> Parallel2[Model Y]
    Ens --> Parallel3[Model Z]
    Parallel1 --> Combine[Combine Results]
    Parallel2 --> Combine
    Parallel3 --> Combine
    Combine --> Response
    
    Split --> Branch1[Model P]
    Split --> Branch2[Model Q]
    Branch1 --> Merge[Merge Results]
    Branch2 --> Merge
    Merge --> Response[Final Response]
    
    style Request fill:#e1f5ff
    style Router fill:#fff9c4
    style Response fill:#a5d6a7
```

#### How It Works in Raw Mode

Unlike Serverless mode which uses Knative routing, Raw mode deploys a **KServe router component** as a standard Kubernetes Deployment that handles the graph logic.

**Components**:
- InferenceGraph CR (defines the pipeline)
- KServe Router Deployment (routes between nodes)
- Individual model Deployments (one per node)
- Kubernetes Services (for routing)

#### Configuration Example

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: InferenceGraph
metadata:
  name: image-pipeline
  annotations:
    serving.kserve.io/deploymentMode: "RawDeployment"
spec:
  nodes:
    root:
      routerType: Sequence
      steps:
      - serviceName: preprocessor
        data: $request
      - serviceName: classifier
        data: $response
      - serviceName: postprocessor
        data: $response
---
# Each node is a separate InferenceService
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: preprocessor
  annotations:
    serving.kserve.io/deploymentMode: "RawDeployment"
spec:
  predictor:
    containers:
    - name: kserve-container
      image: myorg/preprocessor:v1
---
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: classifier
  annotations:
    serving.kserve.io/deploymentMode: "RawDeployment"
spec:
  predictor:
    model:
      modelFormat:
        name: tensorflow
      storageUri: s3://models/classifier
---
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: postprocessor
  annotations:
    serving.kserve.io/deploymentMode: "RawDeployment"
spec:
  predictor:
    containers:
    - name: kserve-container
      image: myorg/postprocessor:v1
```

#### Supported Node Types

| Node Type | Description | Use Case |
|-----------|-------------|----------|
| **Sequence** | Run models one after another | Pre→Model→Post processing |
| **Switch** | Route based on conditions | Different models for different inputs |
| **Ensemble** | Run models in parallel, combine | Model voting/averaging |
| **Splitter** | Split request to multiple paths | A/B testing, parallel processing |

#### Limitations in Raw Mode

**vs Serverless Mode**:
- ✅ All node types work (Sequence, Switch, Ensemble, Splitter)
- ✅ Full graph functionality
- ❌ No automatic traffic splitting between graph versions
- ❌ No scale-to-zero for router component
- ❌ Manual scaling for router

**Benefits**:
- ✅ Simpler architecture (no Knative)
- ✅ More predictable performance
- ✅ Lower resource overhead

---

## Configuration Examples

### Example 1: Simple CPU Model

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sklearn-simple
  namespace: models
  annotations:
    serving.kserve.io/deploymentMode: "RawDeployment"
spec:
  predictor:
    minReplicas: 1
    maxReplicas: 3
    model:
      modelFormat:
        name: sklearn
      storageUri: s3://my-bucket/sklearn-model
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
        limits:
          cpu: "1"
          memory: "2Gi"
```

### Example 2: GPU Model with HPA

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: pytorch-gpu
  namespace: models
  annotations:
    serving.kserve.io/deploymentMode: "RawDeployment"
    autoscaling.knative.dev/class: "hpa.autoscaling.knative.dev"
    autoscaling.knative.dev/metric: "cpu"
    autoscaling.knative.dev/target: "70"
spec:
  predictor:
    minReplicas: 2
    maxReplicas: 5
    model:
      modelFormat:
        name: pytorch
      storageUri: s3://my-bucket/pytorch-model
      resources:
        requests:
          cpu: "4"
          memory: "8Gi"
          nvidia.com/gpu: "1"
        limits:
          cpu: "8"
          memory: "16Gi"
          nvidia.com/gpu: "1"
      nodeSelector:
        nvidia.com/gpu.product: NVIDIA-A100-SXM4-80GB
```

### Example 3: Multi-Model Serving

```yaml
# Step 1: Empty server
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: multi-model-triton
spec:
  predictor:
    model:
      modelFormat:
        name: tensorflow
      protocolVersion: v2
      runtime: kserve-tritonserver
      resources:
        limits:
          nvidia.com/gpu: "1"
---
# Step 2: Add models
apiVersion: serving.kserve.io/v1alpha1
kind: TrainedModel
metadata:
  name: model-a
spec:
  inferenceService: multi-model-triton
  model:
    modelFormat:
      name: tensorflow
    storageUri: s3://bucket/model-a
    memory: 2Gi
---
apiVersion: serving.kserve.io/v1alpha1
kind: TrainedModel
metadata:
  name: model-b
spec:
  inferenceService: multi-model-triton
  model:
    modelFormat:
      name: tensorflow
    storageUri: s3://bucket/model-b
    memory: 2Gi
```

---

## Troubleshooting

### Issue 1: Pods Not Starting

```mermaid
flowchart TB
    Problem[Pods Stuck in<br/>Pending/Init] --> Check1{Check<br/>Pod Status}
    
    Check1 --> Pending[Status: Pending]
    Check1 --> Init[Status: Init]
    Check1 --> CrashLoop[Status: CrashLoopBackOff]
    
    Pending --> Events[Check Events:<br/>kubectl describe pod]
    
    Events --> NoResources{Insufficient<br/>Resources?}
    NoResources -->|Yes| AddNodes[Add More Nodes<br/>or Reduce Requests]
    NoResources -->|No| NoGPU{No GPU<br/>Available?}
    
    NoGPU -->|Yes| AddGPU[Add GPU Nodes<br/>or Wait]
    NoGPU -->|No| Taint{Node<br/>Taints?}
    
    Taint -->|Yes| AddToleration[Add Toleration]
    
    Init --> StorageIssue{Storage<br/>Download Failing?}
    
    StorageIssue -->|Yes| CheckCreds[Check Credentials:<br/>kubectl get secret]
    StorageIssue -->|No| Timeout{Timeout?}
    
    Timeout -->|Yes| IncreaseTimeout[Increase Timeout<br/>Annotation]
    
    CrashLoop --> Logs[Check Logs:<br/>kubectl logs pod]
    
    Logs --> OOM{OOM<br/>Killed?}
    OOM -->|Yes| MoreMemory[Increase Memory<br/>Limits]
    
    Logs --> ConfigError{Config<br/>Error?}
    ConfigError -->|Yes| FixConfig[Fix Configuration]
    
    AddNodes --> Retry[Delete & Recreate<br/>InferenceService]
    AddGPU --> Retry
    AddToleration --> Retry
    CheckCreds --> Retry
    IncreaseTimeout --> Retry
    MoreMemory --> Retry
    FixConfig --> Retry
    
    Retry --> Success[✅ Pods Running]
    
    style Problem fill:#ffcdd2
    style Check1 fill:#fff4e1
    style Pending fill:#ffccbc
    style Init fill:#ffe0b2
    style CrashLoop fill:#ffcdd2
    style Success fill:#a5d6a7
```

### Issue 2: High Latency

```mermaid
flowchart TB
    Slow[High Response<br/>Latency] --> Measure[Measure Where:<br/>kubectl top pod]
    
    Measure --> Check{Where is<br/>the issue?}
    
    Check --> CPU[CPU at 100%]
    Check --> Memory[Memory High]
    Check --> Model[Model Too Large]
    Check --> Network[Network Slow]
    
    CPU --> Solution1[Solutions:<br/>- Increase CPU limits<br/>- Add more replicas<br/>- Use GPU]
    
    Memory --> Solution2[Solutions:<br/>- Increase memory<br/>- Enable model sharing<br/>- Use quantization]
    
    Model --> Solution3[Solutions:<br/>- Use GPU<br/>- Optimize model<br/>- Batch requests]
    
    Network --> Solution4[Solutions:<br/>- Check network policies<br/>- Verify service mesh<br/>- Check DNS]
    
    Solution1 --> Apply[Apply Changes]
    Solution2 --> Apply
    Solution3 --> Apply
    Solution4 --> Apply
    
    Apply --> Test[Test Again]
    
    Test --> Better{Improved?}
    Better -->|Yes| Good[✅ Fixed!]
    Better -->|No| Profile[Profile Application]
    
    Profile --> Identify[Identify Bottleneck]
    Identify --> Apply
    
    style Slow fill:#ffccbc
    style Check fill:#fff4e1
    style Apply fill:#fff9c4
    style Test fill:#c5cae9
    style Good fill:#a5d6a7
```

### Common Commands

```bash
# Check InferenceService status
kubectl get isvc -n <namespace>

# Describe InferenceService
kubectl describe isvc <name> -n <namespace>

# Check pods
kubectl get pods -n <namespace>

# Check logs
kubectl logs <pod-name> -c kserve-container -n <namespace>
kubectl logs <pod-name> -c storage-initializer -n <namespace>

# Check HPA
kubectl get hpa -n <namespace>
kubectl describe hpa <name> -n <namespace>

# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Port forward for testing
kubectl port-forward svc/<isvc>-predictor-default 8080:80 -n <namespace>

# Test inference
curl -X POST http://localhost:8080/v1/models/<model>:predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [[1,2,3,4]]}'
```

---

## Summary

### Pros of Raw K8s Mode

✅ **Simple to understand and deploy**  
✅ **Predictable costs** (pods always running)  
✅ **Works with any model framework**  
✅ **Standard Kubernetes resources**  
✅ **HPA autoscaling included**  
✅ **GPU support built-in**  
✅ **Multi-model serving possible**  
✅ **No additional components needed**

### Cons of Raw K8s Mode

❌ **No scale-to-zero** (paying for idle pods)  
❌ **Basic autoscaling only** (HPA, no KPA)  
❌ **No automatic traffic splitting** (Canary/Blue-Green)  
❌ **No Knative features** (revisions, activator)  
❌ **Manual configuration** for some advanced features

### When to Choose Raw K8s

Choose Raw K8s when you have:
- **Steady, predictable traffic**
- **Traditional ML models** (not LLMs)
- **Cost predictability** requirement
- **Simple deployment** preference
- **Always-on** service needs

### When to Choose Something Else

Choose **Serverless** when you need:
- Scale-to-zero
- Variable traffic
- Complex pipelines

Choose **LLM-D** when you need:
- Large LLM optimization
- Cache-aware routing
- P/D disaggregation

---

**Document Version**: 1.0  
**Last Updated**: October 27, 2025  
**Status**: ✅ 100% Complete - All Raw K8s Features Covered

