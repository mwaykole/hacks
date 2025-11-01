# KServe Overall Architecture

## Overview

KServe is a standardized distributed generative and predictive AI inference platform for scalable, multi-framework deployment on Kubernetes. It provides a unified platform for both Generative AI (LLMs) and Predictive AI (traditional ML models) inference workloads.

## High-Level Architecture Flow

```mermaid
flowchart TB
    subgraph User["User Layer"]
        Client[API Client/User]
        SDK[KServe Python SDK]
    end

    subgraph K8s["Kubernetes API Server"]
        API[K8s API Server]
        Webhook[KServe Webhooks]
    end

    subgraph ControlPlane["KServe Control Plane"]
        Controller[KServe Controller Manager]
        ISVCController[InferenceService Controller]
        TMController[TrainedModel Controller]
        LMController[LocalModel Controller]
        SRController[ServingRuntime Controller]
    end

    subgraph DataPlane["KServe Data Plane"]
        direction TB
        subgraph Serving["Inference Service Pod"]
            StorageInit[Storage Initializer]
            Agent[KServe Agent]
            Transformer[Transformer Container]
            Predictor[Predictor Container]
            Explainer[Explainer Container]
        end
        Router[InferenceGraph Router]
    end

    subgraph Integration["Integration Layer"]
        Knative[Knative Serving]
        ModelMesh[ModelMesh]
        Istio[Istio Service Mesh]
        HPA[Horizontal Pod Autoscaler]
    end

    subgraph Storage["Storage Layer"]
        S3[S3/MinIO]
        PVC[Persistent Volume]
        ModelCache[Model Cache]
    end

    Client -->|1. Create InferenceService| API
    SDK -->|1. Create InferenceService| API
    API -->|2. Validate| Webhook
    Webhook -->|3. Validated| API
    API -->|4. Store CRD| Controller
    
    Controller -->|5. Reconcile| ISVCController
    ISVCController -->|6a. Serverless Mode| Knative
    ISVCController -->|6b. RawDeployment Mode| K8s
    ISVCController -->|6c. ModelMesh Mode| ModelMesh
    
    Knative -->|7. Create Deployment| Serving
    ModelMesh -->|7. Create Deployment| Serving
    
    StorageInit -->|8. Download Model| Storage
    Agent -->|9. Monitor| Predictor
    
    Client -->|10. Inference Request| Istio
    Istio -->|11. Route| Router
    Router -->|12. Pre-process| Transformer
    Transformer -->|13. Inference| Predictor
    Predictor -->|14. Explain| Explainer
    Explainer -->|15. Response| Client
    
    HPA -->|Scale| Serving
    Predictor -.->|Metrics| HPA

    style ControlPlane fill:#e1f5ff
    style DataPlane fill:#fff4e1
    style Integration fill:#f0e1ff
    style Storage fill:#e1ffe1
```

## Core Components Overview

### 1. Control Plane Components

The control plane manages the lifecycle of inference services through various controllers:

- **KServe Controller Manager**: Main orchestrator that coordinates all controllers
- **InferenceService Controller**: Manages InferenceService CRD lifecycle
- **TrainedModel Controller**: Handles TrainedModel resources
- **LocalModel Controller**: Manages local model deployments
- **ServingRuntime Controller**: Controls runtime configurations

### 2. Data Plane Components

The data plane handles actual inference requests and model serving:

- **Storage Initializer**: Downloads models from storage (S3, PVC, etc.)
- **KServe Agent**: Sidecar container for monitoring and logging
- **Predictor**: Core container that serves the ML model
- **Transformer**: Optional pre/post-processing component
- **Explainer**: Optional component for model explanations
- **Router**: Routes requests in InferenceGraph pipelines

### 3. Integration Components

KServe integrates with various Kubernetes ecosystem components:

- **Knative Serving**: Enables serverless deployment with scale-to-zero
- **ModelMesh**: Provides high-density model serving
- **Istio**: Service mesh for networking and traffic management
- **HPA**: Autoscaling based on metrics

### 4. Storage Layer

Models can be stored in various backends:

- **S3/MinIO**: Object storage for model artifacts
- **PVC**: Kubernetes persistent volumes
- **Model Cache**: In-memory caching for faster loading

## Deployment Modes

```mermaid
flowchart LR
    ISVC[InferenceService CRD]
    
    subgraph ServerlessMode["Serverless Mode"]
        Knative[Knative Serving]
        ScaleZero[Scale to Zero]
        AutoScale[Request-based Autoscaling]
    end
    
    subgraph RawMode["Raw Deployment Mode"]
        K8sDeploy[Kubernetes Deployment]
        K8sService[Kubernetes Service]
        BasicHPA[HPA Autoscaling]
    end
    
    subgraph ModelMeshMode["ModelMesh Mode"]
        MMServing[ModelMesh Serving]
        HighDensity[High-Density Packing]
        ModelRouter[Intelligent Routing]
    end
    
    ISVC -->|Default| ServerlessMode
    ISVC -->|Lightweight| RawMode
    ISVC -->|High-Scale| ModelMeshMode
    
    style ServerlessMode fill:#e1f5ff
    style RawMode fill:#fff4e1
    style ModelMeshMode fill:#f0e1ff
```

## Request Flow

### Standard Inference Request Flow

```mermaid
flowchart TB
    Client[Client Application]
    
    subgraph Ingress["Ingress Layer"]
        Gateway[Istio Gateway]
        VirtualService[Virtual Service]
    end
    
    subgraph ServiceMesh["Service Mesh"]
        IngressRoute[Ingress Routing]
        TrafficSplit[Traffic Splitting]
    end
    
    subgraph InferenceService["Inference Service"]
        Transformer[Transformer<br/>Pre-processing]
        Predictor[Predictor<br/>Model Serving]
        Explainer[Explainer<br/>Explanation]
    end
    
    subgraph Response["Response Path"]
        PostProcess[Post-processing]
        ResponseAgg[Response Aggregation]
    end
    
    Client -->|HTTP/gRPC Request| Gateway
    Gateway --> VirtualService
    VirtualService --> IngressRoute
    IngressRoute --> TrafficSplit
    
    TrafficSplit -->|Canary/Shadow| Transformer
    Transformer -->|Transformed Input| Predictor
    Predictor -->|Prediction| Explainer
    Explainer -->|With Explanation| PostProcess
    PostProcess --> ResponseAgg
    ResponseAgg -->|Final Response| Client
    
    style Ingress fill:#e1f5ff
    style ServiceMesh fill:#fff4e1
    style InferenceService fill:#f0e1ff
    style Response fill:#e1ffe1
```

## Feature Categories

### Generative AI Features

```mermaid
flowchart TB
    GenAI[Generative AI Support]
    
    GenAI --> LLMOpt[LLM Optimization]
    GenAI --> GPUAccel[GPU Acceleration]
    GenAI --> ModelCache[Model Caching]
    GenAI --> KVCache[KV Cache Offloading]
    GenAI --> GenAutoScale[Autoscaling]
    GenAI --> HFSupport[Hugging Face Integration]
    
    LLMOpt --> OpenAI[OpenAI Protocol]
    GPUAccel --> MemOpt[Memory Management]
    ModelCache --> FastLoad[Faster Loading]
    KVCache --> LongSeq[Long Sequence Support]
    GenAutoScale --> RequestBased[Request-based Scaling]
    HFSupport --> StreamDeploy[Streamlined Deployment]
    
    style GenAI fill:#ff9999
    style LLMOpt fill:#ffcc99
    style GPUAccel fill:#ffff99
    style ModelCache fill:#99ff99
    style KVCache fill:#99ccff
    style GenAutoScale fill:#cc99ff
    style HFSupport fill:#ff99ff
```

### Predictive AI Features

```mermaid
flowchart TB
    PredAI[Predictive AI Support]
    
    PredAI --> MultiFramework[Multi-Framework Support]
    PredAI --> IntelligentRoute[Intelligent Routing]
    PredAI --> AdvDeploy[Advanced Deployments]
    PredAI --> PredAutoScale[Autoscaling]
    PredAI --> Explain[Model Explainability]
    PredAI --> Monitor[Advanced Monitoring]
    
    MultiFramework --> TF[TensorFlow]
    MultiFramework --> PyTorch[PyTorch]
    MultiFramework --> SKLearn[Scikit-learn]
    MultiFramework --> XGB[XGBoost]
    
    IntelligentRoute --> PTE[Predictor-Transformer-Explainer]
    
    AdvDeploy --> Canary[Canary Rollouts]
    AdvDeploy --> Pipeline[Inference Pipelines]
    AdvDeploy --> Ensemble[Ensembles]
    
    PredAutoScale --> ScaleZero[Scale to Zero]
    
    Explain --> FeatureAttr[Feature Attribution]
    
    Monitor --> PayloadLog[Payload Logging]
    Monitor --> OutlierDet[Outlier Detection]
    Monitor --> DriftDet[Drift Detection]
    
    style PredAI fill:#99ccff
    style MultiFramework fill:#99ff99
    style IntelligentRoute fill:#ffcc99
    style AdvDeploy fill:#ff99cc
    style PredAutoScale fill:#ccff99
    style Explain fill:#ffff99
    style Monitor fill:#cc99ff
```

## Custom Resource Definitions (CRDs)

```mermaid
flowchart TB
    subgraph CRDs["KServe CRDs"]
        ISVC[InferenceService]
        TM[TrainedModel]
        IG[InferenceGraph]
        CSR[ClusterServingRuntime]
        SR[ServingRuntime]
        LM[LocalModel]
    end
    
    subgraph ISVCSpec["InferenceService Spec"]
        Predictor[predictor]
        Transformer[transformer]
        Explainer[explainer]
    end
    
    subgraph RuntimeSpec["Runtime Spec"]
        Container[containers]
        SupportedFrameworks[supportedModelFormats]
        Resources[resources]
    end
    
    ISVC --> ISVCSpec
    ISVC --> SR
    ISVC --> IG
    
    CSR --> RuntimeSpec
    SR --> RuntimeSpec
    
    TM --> ISVC
    LM --> ISVC
    
    style CRDs fill:#e1f5ff
    style ISVCSpec fill:#fff4e1
    style RuntimeSpec fill:#f0e1ff
```

## Key Features Summary

### Core Capabilities

1. **Unified Platform**: Single platform for both Generative and Predictive AI
2. **Multi-Framework Support**: TensorFlow, PyTorch, XGBoost, Scikit-learn, Hugging Face, ONNX
3. **Flexible Deployment**: Serverless, Raw K8s, and ModelMesh modes
4. **Auto-scaling**: Request-based scaling with scale-to-zero capability
5. **Advanced Traffic Management**: Canary rollouts, A/B testing, shadow deployments
6. **Model Explainability**: Built-in support for model interpretability
7. **GPU Optimization**: Efficient GPU utilization with memory management
8. **Cost Efficiency**: Scale-to-zero reduces infrastructure costs

### Deployment Flexibility

| Mode | Use Case | Features |
|------|----------|----------|
| **Serverless** | Variable workloads | Scale-to-zero, autoscaling, canary |
| **Raw K8s** | Consistent workloads | Lightweight, simple, predictable |
| **ModelMesh** | High-density serving | Many models, intelligent routing |

### Protocol Support

- **V1 Protocol**: Original KServe inference protocol
- **V2 Protocol**: Open Inference Protocol (standard across frameworks)
- **OpenAI Protocol**: For LLM and generative AI workloads
- **gRPC**: High-performance binary protocol
- **HTTP/REST**: Standard web protocol

## Installation Options

```mermaid
flowchart TB
    Start[Choose Installation Type]
    
    Start -->|Quick Start| Local[Local Machine<br/>Quick Installation]
    Start -->|Production| Cloud[Cloud/Cluster Installation]
    
    Cloud --> ServerlessInst[Serverless<br/>with Knative]
    Cloud --> RawInst[Raw Kubernetes<br/>Lightweight]
    Cloud --> MMInst[ModelMesh<br/>High-Density]
    Cloud --> KubeflowInst[Kubeflow<br/>Integration]
    
    ServerlessInst --> Features1[Scale-to-zero<br/>Autoscaling<br/>Canary]
    RawInst --> Features2[Lightweight<br/>Simple<br/>HPA]
    MMInst --> Features3[High-density<br/>Multi-model<br/>Smart routing]
    KubeflowInst --> Features4[Full ML platform<br/>Pipelines<br/>Notebooks]
    
    style ServerlessInst fill:#e1f5ff
    style RawInst fill:#fff4e1
    style MMInst fill:#f0e1ff
    style KubeflowInst fill:#e1ffe1
```

## Security and Isolation

```mermaid
flowchart TB
    subgraph Security["Security Features"]
        AuthN[Authentication]
        AuthZ[Authorization]
        TLS[TLS Encryption]
        NetworkPolicy[Network Policies]
    end
    
    subgraph Isolation["Multi-tenancy"]
        Namespace[Namespace Isolation]
        RBAC[RBAC Controls]
        ResourceQuota[Resource Quotas]
    end
    
    subgraph Monitoring["Observability"]
        Metrics[Prometheus Metrics]
        Logging[Centralized Logging]
        Tracing[Distributed Tracing]
    end
    
    Security --> Isolation
    Isolation --> Monitoring
    
    AuthN --> ServiceAccount[Service Account]
    AuthZ --> K8sRBAC[K8s RBAC]
    TLS --> MutualTLS[mTLS with Istio]
    
    style Security fill:#ff9999
    style Isolation fill:#99ff99
    style Monitoring fill:#99ccff
```

## Next Steps

For detailed component-specific information, refer to:

- [InferenceService Controller](./02-INFERENCESERVICE-CONTROLLER.md)
- [Data Plane Components](./03-DATA-PLANE-COMPONENTS.md)
- [Storage Initializer](./04-STORAGE-INITIALIZER.md)
- [Predictor Runtime](./05-PREDICTOR-RUNTIME.md)
- [Transformer Component](./06-TRANSFORMER-COMPONENT.md)
- [Explainer Component](./07-EXPLAINER-COMPONENT.md)
- [InferenceGraph Router](./08-INFERENCEGRAPH-ROUTER.md)
- [ModelMesh Integration](./09-MODELMESH-INTEGRATION.md)
- [Knative Integration](./10-KNATIVE-INTEGRATION.md)
- [Autoscaling Mechanisms](./11-AUTOSCALING-MECHANISMS.md)
- [Model Protocols](./12-MODEL-PROTOCOLS.md)

## References

- [KServe Official Website](https://kserve.github.io/website/)
- [KServe GitHub Repository](https://github.com/kserve/kserve)
- [OpenDataHub KServe Fork](https://github.com/opendatahub-io/kserve)
- [KServe API Reference](https://kserve.github.io/website/docs/reference/crd-api)

