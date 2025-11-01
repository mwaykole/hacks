# Data Plane Components

## Overview

The data plane in KServe handles the actual inference workload. It consists of multiple components that work together to receive requests, process them, serve predictions, and return responses. These components run as containers within Kubernetes pods.

## Data Plane Architecture

```mermaid
flowchart TB
    subgraph IngressLayer["Ingress Layer"]
        Gateway[Istio Gateway]
        VirtualService[Virtual Service]
    end
    
    subgraph InferenceServicePod["InferenceService Pod"]
        subgraph InitContainers["Init Containers"]
            StorageInit[Storage Initializer]
        end
        
        subgraph RuntimeContainers["Runtime Containers"]
            Agent[KServe Agent<br/>Sidecar]
            Queue[Queue Proxy<br/>Knative]
        end
        
        subgraph ComponentContainers["Component Containers"]
            Transformer[Transformer<br/>Container]
            Predictor[Predictor<br/>Container]
            Explainer[Explainer<br/>Container]
        end
        
        subgraph Storage["Pod Storage"]
            ModelCache[Model Cache<br/>emptyDir]
            SharedMem[Shared Memory<br/>shm]
        end
    end
    
    subgraph Backend["Backend Storage"]
        S3[S3/MinIO]
        PVC[PVC]
        HTTP[HTTP Server]
    end
    
    Gateway --> VirtualService
    VirtualService --> Queue
    
    StorageInit -->|Download| Backend
    StorageInit -->|Save| ModelCache
    
    Queue --> Agent
    Agent --> Transformer
    Transformer --> Predictor
    Predictor --> Explainer
    Explainer --> Agent
    Agent --> Queue
    Queue --> Gateway
    
    Predictor -.->|Load Model| ModelCache
    Predictor -.->|GPU Memory| SharedMem
    
    style IngressLayer fill:#e1f5ff
    style InitContainers fill:#fff4e1
    style RuntimeContainers fill:#f0e1ff
    style ComponentContainers fill:#e1ffe1
    style Storage fill:#ffe1f5
```

## Component Request Flow

```mermaid
flowchart LR
    Client[Client]
    
    subgraph Pod["InferenceService Pod"]
        direction LR
        QueueProxy[Queue Proxy]
        Agent[Agent]
        
        subgraph Optional["Optional Components"]
            Transformer[Transformer]
            Explainer[Explainer]
        end
        
        Predictor[Predictor]
    end
    
    Response[Response]
    
    Client -->|1. HTTP/gRPC| QueueProxy
    QueueProxy -->|2. Forward| Agent
    Agent -->|3. Route| Transformer
    Transformer -->|4. Transformed| Predictor
    Predictor -->|5. Prediction| Explainer
    Explainer -->|6. With Explanation| Agent
    Agent -->|7. Collect| QueueProxy
    QueueProxy -->|8. Return| Response
    
    style Pod fill:#e1f5ff
    style Optional fill:#fff4e1
```

## Storage Initializer

```mermaid
flowchart TB
    Start([Pod Starting])
    
    subgraph InitContainer["Init Container: Storage Initializer"]
        ParseURI[Parse Storage URI]
        DetectProtocol{Protocol Type?}
        
        subgraph S3Download["S3 Download"]
            ConfigureS3[Configure S3 Client]
            AuthenticateS3[Authenticate]
            DownloadS3[Download from Bucket]
        end
        
        subgraph PVCCopy["PVC Copy"]
            MountPVC[Mount PVC]
            CopyFiles[Copy Files]
        end
        
        subgraph HTTPDownload["HTTP Download"]
            ConfigureHTTP[Configure HTTP Client]
            DownloadHTTP[Download via HTTP]
        end
        
        subgraph GCSDownload["GCS Download"]
            ConfigureGCS[Configure GCS Client]
            AuthenticateGCS[Authenticate]
            DownloadGCS[Download from GCS]
        end
        
        ExtractModel[Extract Model Files]
        ValidateModel[Validate Model]
        SaveToCache[Save to /mnt/models]
    end
    
    Complete([Init Complete])
    StartMain[Start Main Container]
    
    Start --> ParseURI
    ParseURI --> DetectProtocol
    
    DetectProtocol -->|s3://| ConfigureS3
    DetectProtocol -->|pvc://| MountPVC
    DetectProtocol -->|http(s)://| ConfigureHTTP
    DetectProtocol -->|gs://| ConfigureGCS
    
    ConfigureS3 --> AuthenticateS3
    AuthenticateS3 --> DownloadS3
    DownloadS3 --> ExtractModel
    
    MountPVC --> CopyFiles
    CopyFiles --> ExtractModel
    
    ConfigureHTTP --> DownloadHTTP
    DownloadHTTP --> ExtractModel
    
    ConfigureGCS --> AuthenticateGCS
    AuthenticateGCS --> DownloadGCS
    DownloadGCS --> ExtractModel
    
    ExtractModel --> ValidateModel
    ValidateModel --> SaveToCache
    SaveToCache --> Complete
    Complete --> StartMain
    
    style InitContainer fill:#e1f5ff
    style S3Download fill:#fff4e1
    style PVCCopy fill:#f0e1ff
    style HTTPDownload fill:#e1ffe1
    style GCSDownload fill:#ffe1f5
```

## KServe Agent (Sidecar)

```mermaid
flowchart TB
    subgraph Agent["KServe Agent"]
        HTTPServer[HTTP Server]
        
        subgraph RequestHandling["Request Handling"]
            ReceiveReq[Receive Request]
            ParseReq[Parse Request]
            RouteReq[Route to Component]
            ValidateResp[Validate Response]
            ReturnResp[Return Response]
        end
        
        subgraph Monitoring["Monitoring"]
            CollectMetrics[Collect Metrics]
            LogPayload[Log Payloads]
            TraceRequest[Trace Requests]
            HealthCheck[Health Checks]
        end
        
        subgraph ModelManagement["Model Management"]
            WatchModels[Watch Model Changes]
            ReloadModel[Trigger Reload]
            CacheManage[Manage Cache]
        end
    end
    
    subgraph Components["Target Components"]
        PredictorComp[Predictor]
        TransformerComp[Transformer]
        ExplainerComp[Explainer]
    end
    
    subgraph Observability["Observability Stack"]
        Prometheus[Prometheus]
        Logging[Log Collector]
        Jaeger[Jaeger Tracing]
    end
    
    HTTPServer --> ReceiveReq
    ReceiveReq --> ParseReq
    ParseReq --> RouteReq
    RouteReq --> PredictorComp
    RouteReq --> TransformerComp
    RouteReq --> ExplainerComp
    
    PredictorComp --> ValidateResp
    TransformerComp --> ValidateResp
    ExplainerComp --> ValidateResp
    ValidateResp --> ReturnResp
    
    ReceiveReq --> CollectMetrics
    ReceiveReq --> LogPayload
    ReceiveReq --> TraceRequest
    
    CollectMetrics --> Prometheus
    LogPayload --> Logging
    TraceRequest --> Jaeger
    
    WatchModels --> ReloadModel
    ReloadModel --> PredictorComp
    
    HealthCheck -.->|Probe| PredictorComp
    
    style Agent fill:#e1f5ff
    style Components fill:#fff4e1
    style Observability fill:#f0e1ff
```

## Queue Proxy (Knative)

```mermaid
flowchart TB
    subgraph QueueProxy["Queue Proxy Container"]
        Receiver[Request Receiver]
        
        subgraph Queueing["Request Queueing"]
            Buffer[Request Buffer]
            Throttle[Throttling]
            Priority[Priority Queue]
        end
        
        subgraph Metrics["Metrics Collection"]
            Concurrency[Concurrency Metrics]
            RequestRate[Request Rate]
            Latency[Latency Metrics]
            QueueDepth[Queue Depth]
        end
        
        subgraph ScalingSignals["Scaling Signals"]
            ReportMetrics[Report to Autoscaler]
            ScaleDecision[Scale Decision]
        end
        
        Forward[Forward to Agent]
    end
    
    subgraph Autoscaler["Knative Autoscaler"]
        KPA[Knative Pod Autoscaler]
        HPA[HPA]
    end
    
    Client[Client] --> Receiver
    Receiver --> Buffer
    Buffer --> Throttle
    Throttle --> Priority
    Priority --> Forward
    Forward --> Agent[KServe Agent]
    
    Receiver --> Concurrency
    Receiver --> RequestRate
    Forward --> Latency
    Buffer --> QueueDepth
    
    Concurrency --> ReportMetrics
    RequestRate --> ReportMetrics
    QueueDepth --> ReportMetrics
    
    ReportMetrics --> KPA
    ReportMetrics --> HPA
    KPA --> ScaleDecision
    HPA --> ScaleDecision
    
    style QueueProxy fill:#e1f5ff
    style Queueing fill:#fff4e1
    style Metrics fill:#f0e1ff
    style ScalingSignals fill:#e1ffe1
```

## Predictor Container

```mermaid
flowchart TB
    subgraph Predictor["Predictor Container"]
        ModelServer[Model Server Process]
        
        subgraph Initialization["Initialization"]
            LoadModel[Load Model from Cache]
            AllocateGPU[Allocate GPU Memory]
            WarmUp[Warm-up Inference]
            Ready[Mark Ready]
        end
        
        subgraph InferenceLoop["Inference Loop"]
            ReceiveRequest[Receive Request]
            ValidateInput[Validate Input]
            PreProcess[Preprocess]
            RunInference[Run Inference]
            PostProcess[Postprocess]
            ReturnPrediction[Return Prediction]
        end
        
        subgraph ModelTypes["Model Server Types"]
            VLLM[vLLM Server<br/>LLM]
            TorchServe[TorchServe<br/>PyTorch]
            TFServing[TF Serving<br/>TensorFlow]
            Triton[Triton<br/>Multi-framework]
            SKLearn[SKLearn Server]
            Custom[Custom Server]
        end
        
        subgraph Resources["Resource Management"]
            GPUMem[GPU Memory]
            CPUMem[CPU Memory]
            BatchSize[Batch Size]
            Threading[Threading]
        end
    end
    
    ModelServer --> LoadModel
    LoadModel --> AllocateGPU
    AllocateGPU --> WarmUp
    WarmUp --> Ready
    
    Ready --> ReceiveRequest
    ReceiveRequest --> ValidateInput
    ValidateInput --> PreProcess
    PreProcess --> RunInference
    RunInference --> PostProcess
    PostProcess --> ReturnPrediction
    ReturnPrediction --> ReceiveRequest
    
    ModelServer -.->|Implementation| ModelTypes
    RunInference -.->|Uses| Resources
    
    style Predictor fill:#e1f5ff
    style Initialization fill:#fff4e1
    style InferenceLoop fill:#f0e1ff
    style ModelTypes fill:#e1ffe1
    style Resources fill:#ffe1f5
```

## Transformer Container

```mermaid
flowchart TB
    subgraph Transformer["Transformer Container"]
        HTTPEndpoint[HTTP/gRPC Endpoint]
        
        subgraph PreProcessing["Pre-processing"]
            ReceiveRaw[Receive Raw Request]
            ParseFormat[Parse Input Format]
            FeatureExtract[Feature Extraction]
            Normalize[Normalize Data]
            Transform[Transform to Model Format]
            SendToPredictor[Send to Predictor]
        end
        
        subgraph PostProcessing["Post-processing"]
            ReceivePred[Receive Prediction]
            Decode[Decode Output]
            Format[Format Response]
            Aggregate[Aggregate Results]
            EnrichResponse[Enrich Response]
            ReturnToClient[Return to Client]
        end
        
        subgraph CustomLogic["Custom Logic"]
            BusinessRules[Business Rules]
            DataValidation[Data Validation]
            Filtering[Response Filtering]
            Enrichment[Data Enrichment]
        end
    end
    
    subgraph ExternalServices["External Services"]
        FeatureStore[Feature Store]
        Database[Database]
        Cache[Cache]
    end
    
    HTTPEndpoint --> ReceiveRaw
    ReceiveRaw --> ParseFormat
    ParseFormat --> FeatureExtract
    
    FeatureExtract -.->|Fetch| FeatureStore
    FeatureExtract --> Normalize
    Normalize --> Transform
    Transform --> SendToPredictor
    
    SendToPredictor --> Predictor[Predictor]
    Predictor --> ReceivePred
    ReceivePred --> Decode
    Decode --> Format
    Format --> Aggregate
    Aggregate --> EnrichResponse
    
    EnrichResponse -.->|Query| Database
    EnrichResponse -.->|Lookup| Cache
    EnrichResponse --> ReturnToClient
    
    ParseFormat -.->|Apply| CustomLogic
    Format -.->|Apply| CustomLogic
    
    style Transformer fill:#e1f5ff
    style PreProcessing fill:#fff4e1
    style PostProcessing fill:#f0e1ff
    style CustomLogic fill:#e1ffe1
```

## Explainer Container

```mermaid
flowchart TB
    subgraph Explainer["Explainer Container"]
        ExplainerServer[Explainer Server]
        
        subgraph ExplanationMethods["Explanation Methods"]
            LIME[LIME<br/>Local Interpretable]
            SHAP[SHAP<br/>Shapley Values]
            Anchors[Anchors<br/>Rule-based]
            IntegratedGrad[Integrated Gradients]
            Custom[Custom Explainer]
        end
        
        subgraph Process["Explanation Process"]
            ReceivePred[Receive Prediction]
            GetModel[Get Model Reference]
            GenerateExplanation[Generate Explanation]
            CalculateFeatureImportance[Feature Importance]
            VisualizeResults[Visualize]
            AttachToPrediction[Attach to Prediction]
        end
        
        subgraph Output["Explanation Output"]
            FeatureScores[Feature Scores]
            Visualizations[Visualizations]
            RuleSet[Rule Set]
            Confidence[Confidence Scores]
        end
    end
    
    Predictor[Predictor] --> ReceivePred
    ReceivePred --> GetModel
    GetModel --> GenerateExplanation
    
    GenerateExplanation -.->|Method| ExplanationMethods
    
    GenerateExplanation --> CalculateFeatureImportance
    CalculateFeatureImportance --> VisualizeResults
    VisualizeResults --> AttachToPrediction
    
    AttachToPrediction --> FeatureScores
    AttachToPrediction --> Visualizations
    AttachToPrediction --> RuleSet
    AttachToPrediction --> Confidence
    
    AttachToPrediction --> Client[Client Response]
    
    style Explainer fill:#e1f5ff
    style ExplanationMethods fill:#fff4e1
    style Process fill:#f0e1ff
    style Output fill:#e1ffe1
```

## Pod Resource Configuration

```mermaid
flowchart TB
    subgraph PodSpec["Pod Specification"]
        subgraph Volumes["Volume Mounts"]
            ModelVol[Model Volume<br/>emptyDir: 5Gi]
            ShmVol[Shared Memory<br/>emptyDir: 2Gi]
            ConfigVol[Config Volume<br/>configMap]
            SecretVol[Secret Volume<br/>secret]
        end
        
        subgraph Resources["Resource Requests/Limits"]
            CPU[CPU: 2 cores]
            Memory[Memory: 8Gi]
            GPU[GPU: 1x NVIDIA]
            EphemeralStorage[Ephemeral: 10Gi]
        end
        
        subgraph Security["Security Context"]
            RunAsUser[runAsUser: 1000]
            FSGroup[fsGroup: 1000]
            ReadOnlyFS[readOnlyRootFilesystem]
            Capabilities[drop: ALL]
        end
        
        subgraph Probes["Health Probes"]
            Liveness[Liveness Probe<br/>/health/live]
            Readiness[Readiness Probe<br/>/health/ready]
            Startup[Startup Probe<br/>/health/startup]
        end
    end
    
    PodSpec --> Volumes
    PodSpec --> Resources
    PodSpec --> Security
    PodSpec --> Probes
    
    style PodSpec fill:#e1f5ff
    style Volumes fill:#fff4e1
    style Resources fill:#f0e1ff
    style Security fill:#e1ffe1
    style Probes fill:#ffe1f5
```

## Multi-Container Coordination

```mermaid
flowchart TB
    subgraph Coordination["Container Coordination"]
        subgraph Startup["Startup Sequence"]
            Init1[1. Storage Initializer]
            Init2[2. Wait for Model Download]
            Main1[3. Start Predictor]
            Main2[4. Start Agent]
            Main3[5. Start Queue Proxy]
            Ready[6. Pod Ready]
        end
        
        subgraph Communication["Inter-Container Communication"]
            Localhost[Localhost Network]
            SharedVolume[Shared Volumes]
            UnixSocket[Unix Sockets]
        end
        
        subgraph Lifecycle["Lifecycle Management"]
            PreStop[PreStop Hooks]
            GracefulShutdown[Graceful Shutdown]
            SignalHandling[Signal Handling]
        end
    end
    
    Init1 --> Init2
    Init2 --> Main1
    Main1 --> Main2
    Main2 --> Main3
    Main3 --> Ready
    
    Main1 -.->|127.0.0.1:8080| Main2
    Main2 -.->|127.0.0.1:9000| Main3
    
    Main1 -.->|/mnt/models| SharedVolume
    Main2 -.->|/mnt/models| SharedVolume
    
    style Coordination fill:#e1f5ff
    style Startup fill:#fff4e1
    style Communication fill:#f0e1ff
    style Lifecycle fill:#e1ffe1
```

## Container Specifications

### Storage Initializer Container

```yaml
initContainers:
- name: storage-initializer
  image: kserve/storage-initializer:v0.11.0
  args:
    - srcURI
    - s3://my-bucket/model
    - /mnt/models
  env:
    - name: AWS_ACCESS_KEY_ID
      valueFrom:
        secretKeyRef:
          name: s3-secret
          key: access_key
  volumeMounts:
    - name: model-dir
      mountPath: /mnt/models
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 1
      memory: 1Gi
```

### Predictor Container

```yaml
containers:
- name: kserve-container
  image: pytorch/torchserve:latest
  command:
    - python
    - -m
    - kserve.model_server
  env:
    - name: STORAGE_URI
      value: pvc://my-pvc/model
    - name: PROTOCOL
      value: v2
  ports:
    - containerPort: 8080
      protocol: TCP
  resources:
    requests:
      cpu: 2
      memory: 8Gi
      nvidia.com/gpu: 1
    limits:
      cpu: 4
      memory: 16Gi
      nvidia.com/gpu: 1
  volumeMounts:
    - name: model-dir
      mountPath: /mnt/models
    - name: shm
      mountPath: /dev/shm
```

### Agent Container

```yaml
containers:
- name: agent
  image: kserve/agent:v0.11.0
  ports:
    - containerPort: 9000
      protocol: TCP
  env:
    - name: MODEL_NAME
      value: my-model
    - name: ENABLE_LATENCY_LOGGING
      value: "true"
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 1
      memory: 512Mi
```

## Performance Considerations

```mermaid
flowchart TB
    subgraph Performance["Performance Optimization"]
        subgraph ModelLoading["Model Loading"]
            CacheWarm[Cache Warming]
            LazyLoad[Lazy Loading]
            Preload[Preloading]
        end
        
        subgraph Inference["Inference Optimization"]
            Batching[Dynamic Batching]
            GPUOpt[GPU Optimization]
            Quantization[Model Quantization]
            Caching[Result Caching]
        end
        
        subgraph Networking["Network Optimization"]
            KeepAlive[Keep-Alive]
            Compression[Response Compression]
            HTTP2[HTTP/2]
        end
        
        subgraph Monitoring["Performance Monitoring"]
            Latency[Latency Tracking]
            Throughput[Throughput Metrics]
            ResourceUtil[Resource Utilization]
        end
    end
    
    style Performance fill:#e1f5ff
    style ModelLoading fill:#fff4e1
    style Inference fill:#f0e1ff
    style Networking fill:#e1ffe1
    style Monitoring fill:#ffe1f5
```

## Data Plane Scaling

```mermaid
flowchart LR
    Metrics[Metrics]
    
    subgraph AutoscalingTriggers["Autoscaling Triggers"]
        RequestRate[Request Rate]
        Concurrency[Concurrency]
        CPUUsage[CPU Usage]
        GPUUsage[GPU Usage]
        QueueLength[Queue Length]
        CustomMetric[Custom Metrics]
    end
    
    subgraph Autoscalers["Autoscalers"]
        KPA[Knative Pod Autoscaler]
        HPA[Horizontal Pod Autoscaler]
        CustomScaler[Custom Scaler]
    end
    
    subgraph Actions["Scaling Actions"]
        ScaleUp[Scale Up]
        ScaleDown[Scale Down]
        ScaleToZero[Scale to Zero]
    end
    
    Metrics --> AutoscalingTriggers
    RequestRate --> KPA
    Concurrency --> KPA
    CPUUsage --> HPA
    GPUUsage --> CustomScaler
    
    KPA --> Actions
    HPA --> Actions
    CustomScaler --> Actions
    
    style AutoscalingTriggers fill:#e1f5ff
    style Autoscalers fill:#fff4e1
    style Actions fill:#f0e1ff
```

## Related Components

- [Storage Initializer](./04-STORAGE-INITIALIZER.md)
- [Predictor Runtime](./05-PREDICTOR-RUNTIME.md)
- [Transformer Component](./06-TRANSFORMER-COMPONENT.md)
- [Explainer Component](./07-EXPLAINER-COMPONENT.md)
- [Autoscaling Mechanisms](./11-AUTOSCALING-MECHANISMS.md)

