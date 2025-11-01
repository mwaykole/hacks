# InferenceService Controller

## Overview

The InferenceService Controller is the core component of KServe's control plane. It manages the complete lifecycle of InferenceService resources, from creation to deletion, handling reconciliation loops and coordinating with other Kubernetes resources.

## Controller Architecture

```mermaid
flowchart TB
    subgraph User["User Input"]
        YAML[InferenceService YAML]
        SDK[Python SDK]
        CLI[kubectl]
    end

    subgraph K8sAPI["Kubernetes API"]
        APIServer[API Server]
        Webhook[Validating/Mutating Webhooks]
        Etcd[(etcd)]
    end

    subgraph Controller["InferenceService Controller"]
        Watch[Watch InferenceService]
        Queue[Work Queue]
        Reconciler[Reconcile Loop]
        
        subgraph ReconcileLogic["Reconcile Logic"]
            Validate[Validate Spec]
            CreateResources[Create Resources]
            UpdateStatus[Update Status]
            HandleErrors[Error Handling]
        end
    end

    subgraph Resources["Created Resources"]
        Service[Kubernetes Service]
        Deployment[Deployment/KNative]
        ConfigMap[ConfigMaps]
        VirtualService[Istio VirtualService]
    end

    User --> APIServer
    APIServer --> Webhook
    Webhook -->|Validated| Etcd
    Etcd -->|Event| Watch
    Watch --> Queue
    Queue --> Reconciler
    
    Reconciler --> Validate
    Validate --> CreateResources
    CreateResources --> UpdateStatus
    UpdateStatus --> HandleErrors
    HandleErrors -.->|Retry| Queue
    
    CreateResources --> Resources
    UpdateStatus -->|Status Patch| APIServer
    
    style Controller fill:#e1f5ff
    style ReconcileLogic fill:#fff4e1
    style Resources fill:#f0e1ff
```

## Reconciliation Flow

```mermaid
flowchart TB
    Start([Event Received])
    GetISVC[Get InferenceService from Cache]
    Deleted{Is Deleted?}
    Finalize[Run Finalizers]
    CheckSpec{Validate Spec}
    DetermineMode{Deployment Mode?}
    
    subgraph ServerlessPath["Serverless Path"]
        CreateKNService[Create Knative Service]
        ConfigureRevision[Configure Revision]
        SetupRouting[Setup Routing]
    end
    
    subgraph RawPath["Raw Deployment Path"]
        CreateDeployment[Create K8s Deployment]
        CreateService[Create K8s Service]
        CreateIngress[Create Ingress/Route]
    end
    
    subgraph ModelMeshPath["ModelMesh Path"]
        RegisterModel[Register with ModelMesh]
        ConfigureServing[Configure Serving Runtime]
    end
    
    UpdateStatus[Update InferenceService Status]
    SetConditions[Set Status Conditions]
    RecordEvent[Record Kubernetes Event]
    End([Reconcile Complete])
    
    Start --> GetISVC
    GetISVC --> Deleted
    Deleted -->|Yes| Finalize
    Finalize --> End
    Deleted -->|No| CheckSpec
    CheckSpec -->|Invalid| RecordEvent
    CheckSpec -->|Valid| DetermineMode
    
    DetermineMode -->|Serverless| ServerlessPath
    DetermineMode -->|RawDeployment| RawPath
    DetermineMode -->|ModelMesh| ModelMeshPath
    
    CreateKNService --> SetupRouting
    SetupRouting --> UpdateStatus
    
    CreateDeployment --> CreateService
    CreateService --> CreateIngress
    CreateIngress --> UpdateStatus
    
    RegisterModel --> ConfigureServing
    ConfigureServing --> UpdateStatus
    
    UpdateStatus --> SetConditions
    SetConditions --> RecordEvent
    RecordEvent --> End
    
    style ServerlessPath fill:#e1f5ff
    style RawPath fill:#fff4e1
    style ModelMeshPath fill:#f0e1ff
```

## InferenceService CRD Structure

```mermaid
flowchart TB
    subgraph ISVC["InferenceService CRD"]
        Meta[metadata]
        Spec[spec]
        Status[status]
    end
    
    subgraph SpecFields["Spec Fields"]
        Predictor[predictor]
        Transformer[transformer]
        Explainer[explainer]
        
        subgraph PredictorSpec["Predictor Spec"]
            Model[model]
            Runtime[runtime]
            Storage[storageUri]
            Resources[resources]
            Replicas[minReplicas/maxReplicas]
            Scaling[scaleTarget/scaleMetric]
        end
        
        subgraph ComponentOptions["Common Options"]
            ContainerSpec[containers]
            ImageSpec[image]
            EnvSpec[env]
            VolumesSpec[volumes]
        end
    end
    
    subgraph StatusFields["Status Fields"]
        Conditions[conditions]
        URL[url]
        Address[address]
        Components[components]
        
        subgraph ConditionTypes["Condition Types"]
            Ready[Ready]
            RoutesReady[RoutesReady]
            PredictorReady[PredictorReady]
            TransformerReady[TransformerReady]
        end
    end
    
    ISVC --> Meta
    ISVC --> Spec
    ISVC --> Status
    
    Spec --> SpecFields
    Predictor --> PredictorSpec
    Predictor --> ComponentOptions
    Transformer --> ComponentOptions
    Explainer --> ComponentOptions
    
    Status --> StatusFields
    Conditions --> ConditionTypes
    
    style ISVC fill:#e1f5ff
    style SpecFields fill:#fff4e1
    style StatusFields fill:#f0e1ff
```

## Controller State Machine

```mermaid
flowchart TB
    Init[Initial State]
    Creating[Creating Resources]
    Pending[Pending]
    Ready[Ready]
    Updating[Updating]
    Failed[Failed]
    Deleting[Deleting]
    Deleted[Deleted]
    
    Init -->|Create Event| Creating
    Creating -->|Resources Created| Pending
    Pending -->|All Ready| Ready
    Creating -->|Error| Failed
    
    Ready -->|Update Event| Updating
    Updating -->|Success| Ready
    Updating -->|Error| Failed
    
    Failed -->|Manual Fix| Creating
    Failed -->|Delete Event| Deleting
    
    Ready -->|Delete Event| Deleting
    Pending -->|Delete Event| Deleting
    Deleting -->|Finalizers Complete| Deleted
    
    style Init fill:#cccccc
    style Ready fill:#99ff99
    style Failed fill:#ff9999
    style Deleted fill:#cccccc
```

## Component Creation Logic

```mermaid
flowchart TB
    Start[Start Component Creation]
    CheckTransformer{Transformer<br/>Defined?}
    CheckExplainer{Explainer<br/>Defined?}
    
    subgraph ComponentCreation["Component Creation"]
        CreatePredictorDep[Create Predictor Deployment]
        CreateTransformerDep[Create Transformer Deployment]
        CreateExplainerDep[Create Explainer Deployment]
        
        CreatePredictorSvc[Create Predictor Service]
        CreateTransformerSvc[Create Transformer Service]
        CreateExplainerSvc[Create Explainer Service]
    end
    
    subgraph Routing["Routing Configuration"]
        CreateVirtualSvc[Create Virtual Service]
        ConfigureRoutes[Configure Routes]
        SetupTrafficSplit[Setup Traffic Splitting]
    end
    
    subgraph Chaining["Request Chaining"]
        ChainTransformer[Transformer → Predictor]
        ChainExplainer[Predictor → Explainer]
    end
    
    Complete[Component Creation Complete]
    
    Start --> CreatePredictorDep
    CreatePredictorDep --> CreatePredictorSvc
    CreatePredictorSvc --> CheckTransformer
    
    CheckTransformer -->|Yes| CreateTransformerDep
    CheckTransformer -->|No| CheckExplainer
    CreateTransformerDep --> CreateTransformerSvc
    CreateTransformerSvc --> CheckExplainer
    
    CheckExplainer -->|Yes| CreateExplainerDep
    CheckExplainer -->|No| CreateVirtualSvc
    CreateExplainerDep --> CreateExplainerSvc
    CreateExplainerSvc --> CreateVirtualSvc
    
    CreateVirtualSvc --> ConfigureRoutes
    ConfigureRoutes --> SetupTrafficSplit
    SetupTrafficSplit --> ChainTransformer
    ChainTransformer --> ChainExplainer
    ChainExplainer --> Complete
    
    style ComponentCreation fill:#e1f5ff
    style Routing fill:#fff4e1
    style Chaining fill:#f0e1ff
```

## Webhook Processing

### Validating Webhook Flow

```mermaid
flowchart TB
    Request[Admission Request]
    
    subgraph Validation["Validation Checks"]
        SchemaValidation[Schema Validation]
        RuntimeValidation[Runtime Validation]
        ResourceValidation[Resource Validation]
        StorageValidation[Storage URI Validation]
        ConflictCheck[Conflict Detection]
    end
    
    subgraph Decisions["Decision Logic"]
        AllValid{All Checks<br/>Passed?}
    end
    
    Allow[Allow Request]
    Deny[Deny Request with Message]
    
    Request --> SchemaValidation
    SchemaValidation --> RuntimeValidation
    RuntimeValidation --> ResourceValidation
    ResourceValidation --> StorageValidation
    StorageValidation --> ConflictCheck
    ConflictCheck --> AllValid
    
    AllValid -->|Yes| Allow
    AllValid -->|No| Deny
    
    style Validation fill:#e1f5ff
    style Allow fill:#99ff99
    style Deny fill:#ff9999
```

### Mutating Webhook Flow

```mermaid
flowchart TB
    Request[Admission Request]
    
    subgraph Mutation["Mutation Operations"]
        SetDefaults[Set Default Values]
        InjectAnnotations[Inject Annotations]
        AddLabels[Add Labels]
        ConfigureRuntime[Configure Runtime]
        SetResources[Set Resource Limits]
        InjectVolumes[Inject Storage Volumes]
    end
    
    subgraph RuntimeConfig["Runtime Configuration"]
        SelectRuntime[Select Serving Runtime]
        ConfigureContainer[Configure Container Spec]
        SetEnvVars[Set Environment Variables]
    end
    
    Patch[Generate JSON Patch]
    Response[Return Mutated Spec]
    
    Request --> SetDefaults
    SetDefaults --> InjectAnnotations
    InjectAnnotations --> AddLabels
    AddLabels --> ConfigureRuntime
    ConfigureRuntime --> SetResources
    SetResources --> InjectVolumes
    InjectVolumes --> SelectRuntime
    
    SelectRuntime --> ConfigureContainer
    ConfigureContainer --> SetEnvVars
    SetEnvVars --> Patch
    Patch --> Response
    
    style Mutation fill:#e1f5ff
    style RuntimeConfig fill:#fff4e1
```

## Status Management

```mermaid
flowchart TB
    subgraph StatusUpdate["Status Update Process"]
        GetCurrent[Get Current Status]
        CheckComponents[Check Component Status]
        
        subgraph ComponentStatus["Component Status"]
            CheckPredictor[Check Predictor Ready]
            CheckTransformer[Check Transformer Ready]
            CheckExplainer[Check Explainer Ready]
            CheckRoutes[Check Routes Ready]
        end
        
        AggregateStatus[Aggregate Status]
        CalculateConditions[Calculate Conditions]
        UpdateConditions[Update Conditions]
    end
    
    subgraph Conditions["Status Conditions"]
        ReadyCondition[Ready Condition]
        PredictorReadyCondition[PredictorReady]
        TransformerReadyCondition[TransformerReady]
        ExplainerReadyCondition[ExplainerReady]
        RoutesReadyCondition[RoutesReady]
    end
    
    PatchStatus[Patch Status to API]
    RecordMetrics[Record Metrics]
    
    GetCurrent --> CheckComponents
    CheckComponents --> CheckPredictor
    CheckComponents --> CheckTransformer
    CheckComponents --> CheckExplainer
    CheckComponents --> CheckRoutes
    
    CheckPredictor --> AggregateStatus
    CheckTransformer --> AggregateStatus
    CheckExplainer --> AggregateStatus
    CheckRoutes --> AggregateStatus
    
    AggregateStatus --> CalculateConditions
    CalculateConditions --> UpdateConditions
    
    UpdateConditions --> ReadyCondition
    UpdateConditions --> PredictorReadyCondition
    UpdateConditions --> TransformerReadyCondition
    UpdateConditions --> ExplainerReadyCondition
    UpdateConditions --> RoutesReadyCondition
    
    UpdateConditions --> PatchStatus
    PatchStatus --> RecordMetrics
    
    style StatusUpdate fill:#e1f5ff
    style ComponentStatus fill:#fff4e1
    style Conditions fill:#f0e1ff
```

## Traffic Management

```mermaid
flowchart TB
    ISVC[InferenceService]
    
    subgraph TrafficConfig["Traffic Configuration"]
        Default[Default Traffic 100%]
        Canary[Canary Deployment]
        Shadow[Shadow Traffic]
        ABTest[A/B Testing]
    end
    
    subgraph CanaryFlow["Canary Rollout"]
        OldRevision[Old Revision 90%]
        NewRevision[New Revision 10%]
        Monitor[Monitor Metrics]
        Decide{Success?}
        Promote[Promote to 100%]
        Rollback[Rollback]
    end
    
    subgraph Implementation["Implementation"]
        VirtualService[Istio VirtualService]
        DestinationRule[Destination Rule]
        Subsets[Traffic Subsets]
    end
    
    ISVC --> TrafficConfig
    TrafficConfig --> Canary
    
    Canary --> OldRevision
    Canary --> NewRevision
    OldRevision --> Monitor
    NewRevision --> Monitor
    Monitor --> Decide
    Decide -->|Yes| Promote
    Decide -->|No| Rollback
    
    Canary --> Implementation
    VirtualService --> DestinationRule
    DestinationRule --> Subsets
    
    style TrafficConfig fill:#e1f5ff
    style CanaryFlow fill:#fff4e1
    style Implementation fill:#f0e1ff
```

## Error Handling and Recovery

```mermaid
flowchart TB
    Error[Error Detected]
    
    subgraph ErrorTypes["Error Classification"]
        Transient[Transient Error]
        Permanent[Permanent Error]
        Resource[Resource Error]
        Config[Configuration Error]
    end
    
    subgraph Recovery["Recovery Strategy"]
        Retry[Retry with Backoff]
        FixConfig[Fix Configuration]
        ScaleResources[Scale Resources]
        Fail[Mark as Failed]
    end
    
    subgraph Backoff["Retry Backoff"]
        Immediate[Immediate: 0s]
        Short[Short: 5s]
        Medium[Medium: 30s]
        Long[Long: 5m]
        GiveUp[Give Up After 10 Attempts]
    end
    
    Error --> ErrorTypes
    
    Transient --> Retry
    Resource --> ScaleResources
    Config --> FixConfig
    Permanent --> Fail
    
    Retry --> Immediate
    Immediate --> Short
    Short --> Medium
    Medium --> Long
    Long --> GiveUp
    
    style ErrorTypes fill:#ff9999
    style Recovery fill:#ffcc99
    style Backoff fill:#fff4e1
```

## Controller Metrics

The InferenceService Controller exposes various metrics:

```mermaid
flowchart LR
    subgraph Metrics["Controller Metrics"]
        ReconcileCount[Reconciliation Count]
        ReconcileLatency[Reconciliation Latency]
        QueueDepth[Work Queue Depth]
        ErrorRate[Error Rate]
        
        ISVCCount[InferenceService Count]
        ISVCReady[Ready InferenceServices]
        ISVCFailed[Failed InferenceServices]
        
        ComponentCount[Component Count]
        ResourceUsage[Resource Usage]
    end
    
    subgraph Export["Export Targets"]
        Prometheus[Prometheus]
        Grafana[Grafana Dashboard]
        Alerts[Alert Manager]
    end
    
    Metrics --> Prometheus
    Prometheus --> Grafana
    Prometheus --> Alerts
    
    style Metrics fill:#e1f5ff
    style Export fill:#fff4e1
```

## Key Features

### 1. Multi-Mode Deployment Support

The controller supports three deployment modes:

- **Serverless (Knative)**: Scale-to-zero, autoscaling, traffic splitting
- **Raw Kubernetes**: Traditional deployments with HPA
- **ModelMesh**: High-density multi-model serving

### 2. Component Management

Manages three types of components:

- **Predictor**: Required - serves the model
- **Transformer**: Optional - pre/post-processing
- **Explainer**: Optional - model explanations

### 3. Advanced Traffic Control

- Canary deployments with percentage-based routing
- Shadow traffic for testing
- A/B testing support
- Blue-green deployments

### 4. Status Tracking

Comprehensive status tracking with:

- Ready conditions for each component
- URL and address information
- Error messages and reasons
- Last transition timestamps

### 5. Webhook Integration

- **Validating Webhook**: Ensures spec correctness
- **Mutating Webhook**: Sets defaults and injects configurations

## Configuration Options

### Controller Manager Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: inferenceservice-config
data:
  deploy:
    defaultDeploymentMode: "Serverless"
  ingress:
    ingressGateway: "knative-serving/knative-ingress-gateway"
    ingressService: "istio-ingressgateway.istio-system.svc.cluster.local"
  logger:
    logLevel: "info"
  metricsAggregator:
    enableMetricAggregation: "true"
```

### Leader Election

The controller uses leader election for high availability:

```yaml
leaderElection:
  enabled: true
  leaseDuration: 15s
  renewDeadline: 10s
  retryPeriod: 2s
```

## Performance Optimization

```mermaid
flowchart TB
    subgraph Optimization["Performance Optimizations"]
        Caching[Resource Caching]
        BatchProcessing[Batch Processing]
        ParallelReconcile[Parallel Reconciliation]
        RateLimiting[Rate Limiting]
    end
    
    subgraph CacheStrategy["Cache Strategy"]
        LocalCache[Local Cache]
        SharedCache[Shared Informer Cache]
        TTL[TTL-based Invalidation]
    end
    
    subgraph Tuning["Tuning Parameters"]
        Workers[Worker Threads]
        QueueSize[Queue Size]
        BackoffRate[Backoff Rate]
        SyncPeriod[Sync Period]
    end
    
    Optimization --> CacheStrategy
    Optimization --> Tuning
    
    Caching --> LocalCache
    Caching --> SharedCache
    Caching --> TTL
    
    style Optimization fill:#e1f5ff
    style CacheStrategy fill:#fff4e1
    style Tuning fill:#f0e1ff
```

## Best Practices

1. **Resource Limits**: Always specify resource requests and limits
2. **Health Checks**: Configure proper liveness and readiness probes
3. **Monitoring**: Enable metrics collection and alerting
4. **Logging**: Use structured logging with appropriate log levels
5. **Version Control**: Use revisions for rollback capability
6. **Testing**: Validate changes in staging before production

## Troubleshooting

Common issues and solutions:

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| InferenceService stuck in Creating | Resource constraints | Check node resources, adjust limits |
| Routes not ready | Istio misconfiguration | Verify VirtualService and Gateway |
| Predictor not ready | Image pull error | Check image name and registry access |
| Status not updating | Controller not running | Check controller pod logs |

## Related Components

- [Data Plane Components](./03-DATA-PLANE-COMPONENTS.md)
- [Knative Integration](./10-KNATIVE-INTEGRATION.md)
- [ModelMesh Integration](./09-MODELMESH-INTEGRATION.md)
- [Autoscaling Mechanisms](./11-AUTOSCALING-MECHANISMS.md)

