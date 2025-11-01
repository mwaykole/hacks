# Predictor Runtime

## Overview

The Predictor is the core component in KServe that serves the machine learning model. It handles inference requests, loads models, manages resources, and returns predictions. KServe supports multiple serving runtimes for different ML frameworks.

## Predictor Architecture

```mermaid
flowchart TB
    subgraph PredictorPod["Predictor Container"]
        subgraph Initialization["Initialization Phase"]
            StartServer[Start Model Server]
            LoadConfig[Load Configuration]
            DetectModel[Detect Model Format]
            LoadModel[Load Model into Memory]
            AllocateResources[Allocate GPU/CPU Resources]
            WarmUp[Warmup Inference]
            RegisterEndpoints[Register HTTP/gRPC Endpoints]
            MarkReady[Mark Container Ready]
        end
        
        subgraph InferenceRuntime["Inference Runtime Loop"]
            ReceiveReq[Receive Request]
            ValidateReq[Validate Request]
            Preprocess[Preprocess Input]
            BatchReqs[Batch Requests]
            RunInference[Execute Model Inference]
            Postprocess[Postprocess Output]
            ReturnResp[Return Response]
        end
        
        subgraph ResourceMgmt["Resource Management"]
            GPUMgmt[GPU Memory Management]
            BatchMgmt[Dynamic Batching]
            CacheMgmt[KV Cache Management<br/>LLMs]
            ThreadPool[Thread Pool]
        end
        
        subgraph Monitoring["Monitoring"]
            CollectMetrics[Collect Metrics]
            LogRequests[Log Requests]
            HealthEndpoint[Health Endpoints]
        end
    end
    
    Client[Client Request] --> ReceiveReq
    
    StartServer --> LoadConfig
    LoadConfig --> DetectModel
    DetectModel --> LoadModel
    LoadModel --> AllocateResources
    AllocateResources --> WarmUp
    WarmUp --> RegisterEndpoints
    RegisterEndpoints --> MarkReady
    
    MarkReady --> ReceiveReq
    ReceiveReq --> ValidateReq
    ValidateReq --> Preprocess
    Preprocess --> BatchReqs
    BatchReqs --> RunInference
    RunInference --> Postprocess
    Postprocess --> ReturnResp
    ReturnResp --> Client
    
    RunInference -.->|Uses| ResourceMgmt
    ReceiveReq -.->|Reports| Monitoring
    
    style Initialization fill:#e1f5ff
    style InferenceRuntime fill:#fff4e1
    style ResourceMgmt fill:#f0e1ff
    style Monitoring fill:#e1ffe1
```

## Serving Runtime Types

```mermaid
flowchart TB
    ServingRuntime[Serving Runtime Selection]
    
    subgraph LLMRuntimes["LLM / Generative AI Runtimes"]
        VLLM[vLLM<br/>Optimized LLM serving<br/>PagedAttention]
        HuggingFace[Hugging Face TGI<br/>Text Generation<br/>Inference]
        Caikit[Caikit-TGIS<br/>IBM LLM Runtime]
        OpenAI[OpenAI Compatible<br/>Generic LLM Server]
    end
    
    subgraph TraditionalRuntimes["Traditional ML Runtimes"]
        TFServing[TensorFlow Serving<br/>TensorFlow Models]
        TorchServe[TorchServe<br/>PyTorch Models]
        Triton[NVIDIA Triton<br/>Multi-framework]
        MLServer[MLServer<br/>Python-based]
    end
    
    subgraph SpecializedRuntimes["Specialized Runtimes"]
        SKLearn[SKLearn Server<br/>Scikit-learn]
        XGBoost[XGBoost Server<br/>XGBoost models]
        ONNX[ONNX Runtime<br/>ONNX models]
        Custom[Custom Runtime<br/>User-defined]
    end
    
    ServingRuntime --> LLMRuntimes
    ServingRuntime --> TraditionalRuntimes
    ServingRuntime --> SpecializedRuntimes
    
    style LLMRuntimes fill:#e1f5ff
    style TraditionalRuntimes fill:#fff4e1
    style SpecializedRuntimes fill:#f0e1ff
```

## Model Loading Flow

```mermaid
flowchart TB
    Start([Container Start])
    
    subgraph ModelLoading["Model Loading Process"]
        CheckPath[Check Model Path<br/>at /mnt/models]
        DetectFormat{Detect Model Format}
        
        subgraph TensorFlowLoad["TensorFlow Loading"]
            FindSavedModel[Find saved_model.pb]
            LoadTFGraph[Load TF Graph]
            CreateTFSession[Create TF Session]
            ValidateTFModel[Validate Inputs/Outputs]
        end
        
        subgraph PyTorchLoad["PyTorch Loading"]
            FindPTFile[Find .pt/.pth file]
            LoadStateDict[Load State Dict]
            BuildModel[Build Model Architecture]
            SetEvalMode[Set to Eval Mode]
        end
        
        subgraph HuggingFaceLoad["Hugging Face Loading"]
            FindConfig[Find config.json]
            LoadTokenizer[Load Tokenizer]
            LoadHFModel[Load Model]
            SetDevice[Set Device GPU/CPU]
        end
        
        subgraph ONNXLoad["ONNX Loading"]
            FindONNX[Find .onnx file]
            CreateSession[Create InferenceSession]
            OptimizeGraph[Optimize Graph]
            ValidateIO[Validate I/O]
        end
        
        AllocateMemory[Allocate Memory]
        WarmupInference[Warmup Inference]
        Ready[Model Ready]
    end
    
    Start --> CheckPath
    CheckPath --> DetectFormat
    
    DetectFormat -->|TensorFlow| FindSavedModel
    DetectFormat -->|PyTorch| FindPTFile
    DetectFormat -->|HuggingFace| FindConfig
    DetectFormat -->|ONNX| FindONNX
    
    FindSavedModel --> LoadTFGraph
    LoadTFGraph --> CreateTFSession
    CreateTFSession --> ValidateTFModel
    ValidateTFModel --> AllocateMemory
    
    FindPTFile --> LoadStateDict
    LoadStateDict --> BuildModel
    BuildModel --> SetEvalMode
    SetEvalMode --> AllocateMemory
    
    FindConfig --> LoadTokenizer
    LoadTokenizer --> LoadHFModel
    LoadHFModel --> SetDevice
    SetDevice --> AllocateMemory
    
    FindONNX --> CreateSession
    CreateSession --> OptimizeGraph
    OptimizeGraph --> ValidateIO
    ValidateIO --> AllocateMemory
    
    AllocateMemory --> WarmupInference
    WarmupInference --> Ready
    
    style ModelLoading fill:#e1f5ff
    style TensorFlowLoad fill:#fff4e1
    style PyTorchLoad fill:#f0e1ff
    style HuggingFaceLoad fill:#e1ffe1
    style ONNXLoad fill:#ffe1f5
```

## Request Processing Flow

```mermaid
flowchart TB
    IncomingRequest[Incoming Request]
    
    subgraph RequestProcessing["Request Processing Pipeline"]
        ParseRequest[Parse Request<br/>JSON or Proto]
        ValidateSchema[Validate Schema]
        ExtractTensor[Extract Tensor Data]
        
        subgraph Preprocessing["Preprocessing"]
            DecodeInput[Decode Input]
            Normalize[Normalize Data]
            Reshape[Reshape Tensors]
            TypeConvert[Type Conversion]
        end
        
        subgraph Batching["Dynamic Batching"]
            CheckBatch{Batching<br/>Enabled?}
            AddToQueue[Add to Batch Queue]
            WaitOrTimeout[Wait for Batch/Timeout]
            FormBatch[Form Batch]
        end
        
        subgraph Inference["Model Inference"]
            PrepareInputs[Prepare Model Inputs]
            ExecuteModel[Execute Model Forward Pass]
            CollectOutputs[Collect Outputs]
        end
        
        subgraph Postprocessing["Postprocessing"]
            ProcessOutput[Process Raw Output]
            ApplyActivation[Apply Activation]
            DecodeOutput[Decode Output]
            FormatResponse[Format Response]
        end
        
        ReturnResponse[Return Response]
    end
    
    IncomingRequest --> ParseRequest
    ParseRequest --> ValidateSchema
    ValidateSchema --> ExtractTensor
    ExtractTensor --> DecodeInput
    
    DecodeInput --> Normalize
    Normalize --> Reshape
    Reshape --> TypeConvert
    TypeConvert --> CheckBatch
    
    CheckBatch -->|Yes| AddToQueue
    CheckBatch -->|No| PrepareInputs
    AddToQueue --> WaitOrTimeout
    WaitOrTimeout --> FormBatch
    FormBatch --> PrepareInputs
    
    PrepareInputs --> ExecuteModel
    ExecuteModel --> CollectOutputs
    CollectOutputs --> ProcessOutput
    
    ProcessOutput --> ApplyActivation
    ApplyActivation --> DecodeOutput
    DecodeOutput --> FormatResponse
    FormatResponse --> ReturnResponse
    
    style RequestProcessing fill:#e1f5ff
    style Preprocessing fill:#fff4e1
    style Batching fill:#f0e1ff
    style Inference fill:#e1ffe1
    style Postprocessing fill:#ffe1f5
```

## LLM-Specific Features

```mermaid
flowchart TB
    subgraph LLMFeatures["LLM Serving Features"]
        subgraph Optimization["Memory Optimization"]
            PagedAttention[Paged Attention<br/>vLLM]
            KVCacheOffload[KV Cache Offloading<br/>CPU or Disk]
            Quantization[Model Quantization<br/>INT8 or INT4]
            FlashAttention[Flash Attention]
        end
        
        subgraph Generation["Text Generation"]
            StreamingResp[Streaming Responses]
            BeamSearch[Beam Search]
            Sampling[Sampling Strategies<br/>Top-k and Top-p]
            StopSequence[Stop Sequences]
        end
        
        subgraph Batching["Continuous Batching"]
            DynamicBatch[Dynamic Batching]
            IterativeLevel[Iteration-level Batching]
            PriorityQueue[Priority Scheduling]
        end
        
        subgraph Protocols["LLM Protocols"]
            OpenAIAPI[OpenAI Compatible API]
            Completions[v1 completions endpoint]
            ChatCompletions[v1 chat completions endpoint]
            Embeddings[v1 embeddings endpoint]
        end
    end
    
    style LLMFeatures fill:#e1f5ff
    style Optimization fill:#fff4e1
    style Generation fill:#f0e1ff
    style Batching fill:#e1ffe1
    style Protocols fill:#ffe1f5
```

## GPU Resource Management

```mermaid
flowchart TB
    subgraph GPUManagement["GPU Resource Management"]
        subgraph Allocation["GPU Allocation"]
            DetectGPU[Detect Available GPUs]
            CheckMemory[Check GPU Memory]
            AllocateGPU[Allocate GPU Device]
            SetDevice[Set CUDA Device]
        end
        
        subgraph MemoryMgmt["Memory Management"]
            ModelMemory[Model Parameters<br/>Weights on GPU]
            ActivationMemory[Activation Memory<br/>Intermediate tensors]
            KVCache[KV Cache<br/>LLM attention cache]
            CUDACache[CUDA Memory Cache]
        end
        
        subgraph Optimization["GPU Optimization"]
            TensorCore[Tensor Core Usage]
            MixedPrecision[Mixed Precision<br/>FP16 or BF16]
            CUDAGraphs[CUDA Graphs]
            MemoryPool[Memory Pooling]
        end
        
        subgraph Monitoring["GPU Monitoring"]
            TrackUsage[Track GPU Usage]
            MonitorTemp[Monitor Temperature]
            CheckOOM[OOM Detection]
            ReportMetrics[Report Metrics]
        end
    end
    
    DetectGPU --> CheckMemory
    CheckMemory --> AllocateGPU
    AllocateGPU --> SetDevice
    
    SetDevice --> ModelMemory
    ModelMemory --> ActivationMemory
    ActivationMemory --> KVCache
    KVCache --> CUDACache
    
    CUDACache -.->|Optimize| Optimization
    Optimization -.->|Monitor| Monitoring
    
    style GPUManagement fill:#e1f5ff
    style Allocation fill:#fff4e1
    style MemoryMgmt fill:#f0e1ff
    style Optimization fill:#e1ffe1
    style Monitoring fill:#ffe1f5
```

## Health and Readiness Probes

```mermaid
flowchart TB
    subgraph HealthProbes["Health Probe Endpoints"]
        subgraph Liveness["Liveness Probe"]
            LivenessCheck[GET health live endpoint]
            CheckProcess[Check Process Running]
            CheckMemory[Check Memory Available]
            LivenessResp{Healthy?}
        end
        
        subgraph Readiness["Readiness Probe"]
            ReadinessCheck[GET health ready endpoint]
            CheckModelLoaded[Check Model Loaded]
            CheckDependencies[Check Dependencies]
            TestInference[Test Inference]
            ReadinessResp{Ready?}
        end
        
        subgraph Startup["Startup Probe"]
            StartupCheck[GET health startup endpoint]
            CheckInitComplete[Check Initialization]
            CheckWarmup[Check Warmup Done]
            StartupResp{Started?}
        end
    end
    
    subgraph Actions["Kubernetes Actions"]
        Running[Keep Running]
        Restart[Restart Container]
        RemoveEndpoint[Remove from Service]
        AddEndpoint[Add to Service]
    end
    
    LivenessCheck --> CheckProcess
    CheckProcess --> CheckMemory
    CheckMemory --> LivenessResp
    LivenessResp -->|Yes| Running
    LivenessResp -->|No| Restart
    
    ReadinessCheck --> CheckModelLoaded
    CheckModelLoaded --> CheckDependencies
    CheckDependencies --> TestInference
    TestInference --> ReadinessResp
    ReadinessResp -->|Yes| AddEndpoint
    ReadinessResp -->|No| RemoveEndpoint
    
    StartupCheck --> CheckInitComplete
    CheckInitComplete --> CheckWarmup
    CheckWarmup --> StartupResp
    StartupResp -->|Yes| ReadinessCheck
    StartupResp -->|No| StartupCheck
    
    style HealthProbes fill:#e1f5ff
    style Liveness fill:#fff4e1
    style Readiness fill:#f0e1ff
    style Startup fill:#e1ffe1
    style Actions fill:#ffe1f5
```

## Model Server Configurations

### vLLM Runtime (LLM)

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: llama-model
spec:
  predictor:
    model:
      modelFormat:
        name: vllm
      storageUri: s3://bucket/llama-2-7b
      runtime: vllm-runtime
      args:
        - --max-model-len=4096
        - --gpu-memory-utilization=0.9
        - --tensor-parallel-size=2
      resources:
        limits:
          nvidia.com/gpu: 2
          memory: 32Gi
        requests:
          nvidia.com/gpu: 2
          memory: 32Gi
```

### TorchServe Runtime (PyTorch)

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: pytorch-model
spec:
  predictor:
    model:
      modelFormat:
        name: pytorch
      storageUri: s3://bucket/resnet50.mar
      runtime: torchserve-runtime
      protocolVersion: v2
      resources:
        limits:
          nvidia.com/gpu: 1
          memory: 8Gi
        requests:
          cpu: 2
          memory: 4Gi
```

### TensorFlow Serving Runtime

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: tensorflow-model
spec:
  predictor:
    model:
      modelFormat:
        name: tensorflow
      storageUri: s3://bucket/mnist-model
      runtime: tensorflow-serving
      protocolVersion: v2
      resources:
        limits:
          cpu: 4
          memory: 8Gi
        requests:
          cpu: 2
          memory: 4Gi
```

### Triton Inference Server (Multi-framework)

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: triton-model
spec:
  predictor:
    model:
      modelFormat:
        name: triton
      storageUri: s3://bucket/model-repository
      runtime: triton-runtime
      protocolVersion: v2
      args:
        - --model-control-mode=explicit
        - --strict-model-config=false
      resources:
        limits:
          nvidia.com/gpu: 1
          memory: 16Gi
```

## Performance Optimization Strategies

```mermaid
flowchart TB
    subgraph Optimization["Performance Optimization"]
        subgraph ModelOpt["Model Optimization"]
            Quantize[Quantization<br/>INT8 or INT4 or FP16]
            Prune[Pruning<br/>Remove weights]
            Distill[Distillation<br/>Smaller model]
            Compile[Model Compilation<br/>TorchScript or ONNX]
        end
        
        subgraph RuntimeOpt["Runtime Optimization"]
            BatchOpt[Dynamic Batching]
            CacheOpt[Result Caching]
            ThreadOpt[Thread Optimization]
            GPUOpt[GPU Optimization]
        end
        
        subgraph NetworkOpt["Network Optimization"]
            Compression[Response Compression]
            HTTP2Opt[HTTP/2]
            KeepAlive[Connection Keep-Alive]
            Streaming[Streaming Responses]
        end
        
        subgraph InfraOpt["Infrastructure Optimization"]
            Affinity[Node Affinity]
            Topology[Topology Awareness]
            FastStorage[Fast Storage]
            NetworkBW[High Network Bandwidth]
        end
    end
    
    style Optimization fill:#e1f5ff
    style ModelOpt fill:#fff4e1
    style RuntimeOpt fill:#f0e1ff
    style NetworkOpt fill:#e1ffe1
    style InfraOpt fill:#ffe1f5
```

## Metrics and Monitoring

```mermaid
flowchart TB
    subgraph Metrics["Predictor Metrics"]
        subgraph Latency["Latency Metrics"]
            PreprocessLatency[Preprocessing Time]
            InferenceLatency[Inference Time]
            PostprocessLatency[Postprocessing Time]
            E2ELatency[End-to-End Latency]
        end
        
        subgraph Throughput["Throughput Metrics"]
            RequestsPerSec[Requests per Second]
            TokensPerSec[Tokens per Second<br/>LLM]
            BatchSize[Batch Size]
            Concurrency[Concurrent Requests]
        end
        
        subgraph Resource["Resource Metrics"]
            CPUUsage[CPU Usage]
            MemoryUsage[Memory Usage]
            GPUUsage[GPU Utilization]
            GPUMemory[GPU Memory]
        end
        
        subgraph Quality["Quality Metrics"]
            ErrorRate[Error Rate]
            TimeoutRate[Timeout Rate]
            CacheHitRate[Cache Hit Rate]
            ModelAccuracy[Model Accuracy]
        end
    end
    
    subgraph Export["Metrics Export"]
        Prometheus[Prometheus]
        Grafana[Grafana]
        CloudWatch[CloudWatch]
    end
    
    Metrics --> Export
    
    style Metrics fill:#e1f5ff
    style Latency fill:#fff4e1
    style Throughput fill:#f0e1ff
    style Resource fill:#e1ffe1
    style Quality fill:#ffe1f5
```

## Error Handling

```mermaid
flowchart TB
    Request[Inference Request]
    Process[Process Request]
    Error{Error?}
    
    subgraph ErrorTypes["Error Types"]
        ModelError[Model Execution Error]
        InputError[Invalid Input Error]
        ResourceError[Resource Exhaustion]
        TimeoutError[Timeout Error]
        SystemError[System Error]
    end
    
    subgraph ErrorHandling["Error Handling"]
        LogError[Log Error Details]
        ReturnError[Return Error Response]
        RecordMetric[Record Error Metric]
        TriggerAlert[Trigger Alert]
    end
    
    subgraph Recovery["Recovery Actions"]
        Retry[Retry Request]
        Fallback[Use Fallback Model]
        CircuitBreak[Circuit Breaker]
        GracefulDegradation[Graceful Degradation]
    end
    
    Success[Return Prediction]
    
    Request --> Process
    Process --> Error
    Error -->|No| Success
    Error -->|Yes| ErrorTypes
    
    ModelError --> LogError
    InputError --> LogError
    ResourceError --> LogError
    TimeoutError --> LogError
    SystemError --> LogError
    
    LogError --> ReturnError
    ReturnError --> RecordMetric
    RecordMetric --> TriggerAlert
    
    TriggerAlert -.->|Possible| Recovery
    
    style ErrorTypes fill:#ff9999
    style ErrorHandling fill:#ffcc99
    style Recovery fill:#fff4e1
```

## Best Practices

1. **Model Loading**
   - Use model caching to reduce startup time
   - Implement warmup inference before marking ready
   - Validate model integrity after loading

2. **Resource Management**
   - Set appropriate resource requests and limits
   - Monitor GPU memory usage
   - Use dynamic batching for throughput

3. **Performance**
   - Enable model quantization when possible
   - Use GPU optimization features (Tensor Cores, mixed precision)
   - Implement result caching for repeated requests

4. **Reliability**
   - Configure proper health probes
   - Implement graceful shutdown
   - Handle errors gracefully

5. **Monitoring**
   - Export comprehensive metrics
   - Set up alerts for errors and latency
   - Track resource utilization

## Related Components

- [Data Plane Components](./03-DATA-PLANE-COMPONENTS.md)
- [Storage Initializer](./04-STORAGE-INITIALIZER.md)
- [Model Protocols](./12-MODEL-PROTOCOLS.md)
- [Autoscaling Mechanisms](./11-AUTOSCALING-MECHANISMS.md)

