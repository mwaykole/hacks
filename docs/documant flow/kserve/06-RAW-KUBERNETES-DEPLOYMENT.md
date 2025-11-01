# KServe Raw Kubernetes Deployment Mode

## Overview

Raw Kubernetes deployment mode is KServe's **lightweight** deployment option that uses standard Kubernetes resources (Deployment + Service) instead of Knative Serving. This mode is simpler, more predictable, but lacks some serverless features like scale-to-zero.

## Raw Deployment vs Serverless

```mermaid
flowchart TB
    subgraph Serverless["Serverless Mode (Knative)"]
        direction TB
        KN[Knative Serving]
        KNFeatures[✓ Scale-to-zero<br/>✓ Request-based autoscaling<br/>✓ Canary rollouts<br/>✓ Revision management<br/>✗ More complexity<br/>✗ Additional dependencies]
    end
    
    subgraph Raw["Raw Kubernetes Mode"]
        direction TB
        K8s[K8s Deployment + Service]
        RawFeatures[✓ Simple & lightweight<br/>✓ Standard K8s resources<br/>✓ Predictable behavior<br/>✓ HPA autoscaling<br/>✗ No scale-to-zero<br/>✗ Basic traffic splitting]
    end
    
    User[User Creates InferenceService]
    
    User -->|deploymentMode: Serverless| Serverless
    User -->|deploymentMode: RawDeployment| Raw
    
    style Serverless fill:#e1f5ff
    style Raw fill:#fff4e1
    style User fill:#f0e1ff
```

**Simple Explanation:**
Think of it like choosing between:
- **Serverless Mode**: Like AWS Lambda - complex but auto-scales, even to zero
- **Raw Mode**: Like a regular container - simple, always running, uses standard Kubernetes

## Raw Deployment Architecture

```mermaid
flowchart TB
    subgraph User["User Layer"]
        Client[Client Request]
    end
    
    subgraph Ingress["Ingress Layer"]
        IstioGateway[Istio Gateway]
        VirtualService[Virtual Service]
    end
    
    subgraph K8sResources["Kubernetes Resources Created"]
        Deployment[Deployment<br/>Standard K8s Deployment]
        Service[Service<br/>ClusterIP Service]
        HPA[HPA<br/>Horizontal Pod Autoscaler]
        
        subgraph Pods["Pods"]
            Pod1[Pod 1<br/>Storage Init + Predictor + Agent]
            Pod2[Pod 2<br/>Storage Init + Predictor + Agent]
            Pod3[Pod N<br/>Storage Init + Predictor + Agent]
        end
    end
    
    subgraph Monitoring["Monitoring"]
        Metrics[Metrics Server]
        Prometheus[Prometheus]
    end
    
    Client --> IstioGateway
    IstioGateway --> VirtualService
    VirtualService --> Service
    Service --> Pods
    
    HPA -.->|Watches CPU/Memory| Pods
    HPA -.->|Scales| Deployment
    
    Pods -.->|Metrics| Metrics
    Pods -.->|Custom Metrics| Prometheus
    Prometheus -.->|Feeds| HPA
    
    style User fill:#e1f5ff
    style Ingress fill:#fff4e1
    style K8sResources fill:#f0e1ff
    style Monitoring fill:#e1ffe1
```

**Simple Explanation:**
In Raw mode, KServe creates regular Kubernetes resources you already know:
- **Deployment**: Manages your inference pods (just like any app)
- **Service**: Provides a stable endpoint to reach pods
- **HPA**: Scales pods based on CPU/memory (standard Kubernetes autoscaling)
- No special Knative magic - just plain Kubernetes!

## Configuration Flow

```mermaid
flowchart TB
    Start[User Creates InferenceService]
    
    subgraph Config["Configuration"]
        SetMode[Set deploymentMode:<br/>RawDeployment]
        SetReplicas[Set minReplicas/maxReplicas]
        SetResources[Set CPU/Memory Requests]
        SetScaling[Optional: Configure HPA]
    end
    
    subgraph Controller["Controller Processing"]
        DetectMode{Deployment<br/>Mode?}
        CreateDeployment[Create K8s Deployment]
        CreateService[Create K8s Service]
        CreateHPA[Create HPA]
        CreateVS[Create VirtualService]
    end
    
    subgraph Resources["Created Resources"]
        DeploymentObj[Deployment Object]
        ServiceObj[Service Object]
        HPAObj[HPA Object]
        VSObj[VirtualService Object]
    end
    
    Start --> Config
    SetMode --> DetectMode
    SetReplicas --> DetectMode
    SetResources --> DetectMode
    SetScaling --> DetectMode
    
    DetectMode -->|RawDeployment| CreateDeployment
    CreateDeployment --> CreateService
    CreateService --> CreateHPA
    CreateHPA --> CreateVS
    
    CreateDeployment --> DeploymentObj
    CreateService --> ServiceObj
    CreateHPA --> HPAObj
    CreateVS --> VSObj
    
    style Config fill:#e1f5ff
    style Controller fill:#fff4e1
    style Resources fill:#f0e1ff
```

**Simple Explanation:**
When you set `deploymentMode: RawDeployment`:
1. Controller sees: "Ah, user wants simple Kubernetes mode"
2. Creates: Regular Deployment (not Knative Service)
3. Creates: Regular Service (ClusterIP type)
4. Creates: HPA if you want autoscaling
5. Creates: VirtualService for Istio routing (if using Istio)

That's it! No Knative, no serverless complexity.

## InferenceService YAML Example

### Basic Raw Deployment

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: pytorch-raw
  namespace: models
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
spec:
  predictor:
    model:
      modelFormat:
        name: pytorch
      storageUri: s3://my-bucket/pytorch-model
      resources:
        requests:
          cpu: 2
          memory: 4Gi
        limits:
          cpu: 4
          memory: 8Gi
          nvidia.com/gpu: 1
    minReplicas: 2
    maxReplicas: 5
```

**Simple Explanation:**
```
This says: "Create a regular Kubernetes deployment with:
- Always keep 2 pods running (no scale-to-zero!)
- Can scale up to 5 pods max
- Each pod gets 2 CPUs and 4GB RAM
- PyTorch model from S3
- Simple and straightforward!"
```

### With HPA Configuration

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: pytorch-hpa
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
spec:
  predictor:
    model:
      modelFormat:
        name: pytorch
      storageUri: s3://my-bucket/model
      resources:
        requests:
          cpu: 2
          memory: 4Gi
    minReplicas: 2
    maxReplicas: 10
    scaleTarget: 80  # Target CPU utilization percentage
    scaleMetric: cpu  # Scale based on CPU
```

**Simple Explanation:**
```
This adds autoscaling:
- Start with 2 pods
- Scale up to 10 pods if needed
- When average CPU across pods > 80%, add more pods
- When CPU drops, remove pods (but keep minimum 2)
- Standard Kubernetes HPA behavior
```

## What Gets Created

```mermaid
flowchart TB
    ISVC[InferenceService: pytorch-raw]
    
    subgraph Created["Resources Created by Controller"]
        Dep[Deployment:<br/>pytorch-raw-predictor-default]
        
        subgraph DepSpec["Deployment Spec"]
            Replicas[replicas: 2]
            Template[Pod Template]
            Strategy[Rolling Update Strategy]
        end
        
        Svc[Service:<br/>pytorch-raw-predictor-default]
        
        subgraph SvcSpec["Service Spec"]
            Type[type: ClusterIP]
            Port[port: 80 → 8080]
            Selector[selector: matches deployment]
        end
        
        HPA[HPA:<br/>pytorch-raw-predictor-default]
        
        subgraph HPASpec["HPA Spec"]
            MinMax[min: 2, max: 5]
            Target[targetCPU: 80%]
            Behavior[scaleDown: stabilization]
        end
        
        VS[VirtualService:<br/>pytorch-raw]
        
        subgraph VSSpec["VirtualService Spec"]
            Host[host: pytorch-raw.models.svc]
            Route[route to Service]
        end
    end
    
    ISVC --> Created
    Dep --> DepSpec
    Svc --> SvcSpec
    HPA --> HPASpec
    VS --> VSSpec
    
    style ISVC fill:#e1f5ff
    style Created fill:#fff4e1
    style DepSpec fill:#f0e1ff
    style SvcSpec fill:#e1ffe1
    style HPASpec fill:#ffe1f5
    style VSSpec fill:#f5e1ff
```

**Simple Explanation:**
For one InferenceService, you get four standard Kubernetes objects:
1. **Deployment**: Manages your inference pods (like nginx, redis, any app)
2. **Service**: Gives pods a stable DNS name 
3. **HPA**: Automatically adds/removes pods based on load
4. **VirtualService**: Routes external traffic to the Service (Istio only)

You can see all of these with regular `kubectl get` commands!

## Request Flow

```mermaid
flowchart LR
    Client[Client]
    
    subgraph Ingress["Ingress"]
        Gateway[Istio Gateway<br/>External Entry]
        VS[VirtualService<br/>Routing Rules]
    end
    
    subgraph K8s["Kubernetes"]
        Service[Service<br/>Load Balancer]
        
        subgraph Pods["Pods"]
            Pod1[Pod 1<br/>Predictor]
            Pod2[Pod 2<br/>Predictor]
        end
    end
    
    Response[Response]
    
    Client -->|1. HTTP Request| Gateway
    Gateway -->|2. Match route| VS
    VS -->|3. Forward to| Service
    Service -->|4. Load balance| Pod1
    Service -->|4. Load balance| Pod2
    Pod1 -->|5. Inference| Service
    Pod2 -->|5. Inference| Service
    Service -->|6. Return| VS
    VS -->|7. Return| Gateway
    Gateway -->|8. Response| Response
    
    style Ingress fill:#e1f5ff
    style K8s fill:#fff4e1
    style Pods fill:#f0e1ff
```

**Simple Explanation:**
Request flow is straightforward (no Knative in the middle!):
1. Client sends request to Istio Gateway
2. VirtualService routes to your Service
3. Service load-balances to one of your pods
4. Pod does inference and returns result
5. Response goes back through same path

It's just like accessing any Kubernetes service - simple!

## Scaling Behavior

```mermaid
flowchart TB
    subgraph Initial["Initial State"]
        Start[InferenceService Created<br/>minReplicas: 2]
        Deploy2[2 Pods Running<br/>Always]
    end
    
    subgraph LoadIncrease["Load Increases"]
        Traffic[More Requests Come]
        CPUHigh[CPU Usage > 80%]
        HPADetect[HPA Detects High Load]
        ScaleUp[HPA Increases Replicas]
        NewPods[New Pods Start]
    end
    
    subgraph LoadDecrease["Load Decreases"]
        LessTraffic[Fewer Requests]
        CPULow[CPU Usage < 40%]
        HPADetect2[HPA Detects Low Load]
        Wait[Wait Stabilization Period<br/>5 minutes default]
        ScaleDown[HPA Decreases Replicas]
        RemovePods[Pods Terminate]
        KeepMin[But Keep minReplicas: 2]
    end
    
    Start --> Deploy2
    Deploy2 --> Traffic
    Traffic --> CPUHigh
    CPUHigh --> HPADetect
    HPADetect --> ScaleUp
    ScaleUp --> NewPods
    
    NewPods --> LessTraffic
    LessTraffic --> CPULow
    CPULow --> HPADetect2
    HPADetect2 --> Wait
    Wait --> ScaleDown
    ScaleDown --> RemovePods
    RemovePods --> KeepMin
    
    style Initial fill:#e1f5ff
    style LoadIncrease fill:#99ff99
    style LoadDecrease fill:#ffcc99
```

**Simple Explanation:**
Raw mode scaling is predictable:
- **Always running**: Minimum 2 pods (no scale-to-zero!)
- **Scale up**: When CPU > 80%, HPA adds pods (happens in seconds)
- **Scale down**: When CPU < 40%, HPA waits 5 minutes then removes pods
- **Cost**: You pay for minimum pods even with zero traffic
- **Benefit**: No cold start! Requests always answered immediately

## Comparison with Serverless

```mermaid
flowchart TB
    subgraph RawMode["Raw Deployment Mode"]
        RawStart[Always Running<br/>2+ pods minimum]
        RawScale[HPA Scales<br/>Based on CPU/Memory]
        RawCost[Higher Cost<br/>Pods always running]
        RawLatency[No Cold Start<br/>Immediate response]
        RawSimple[Simple Setup<br/>Standard K8s]
    end
    
    subgraph ServerlessMode["Serverless Mode"]
        KNStart[Can Scale to Zero<br/>0 pods when idle]
        KNScale[KPA/HPA Scales<br/>Request-based + CPU]
        KNCost[Lower Cost<br/>Zero cost when idle]
        KNLatency[Cold Start<br/>5-30s first request]
        KNComplex[Complex Setup<br/>Needs Knative]
    end
    
    UseCase{Your Use Case?}
    
    UseCase -->|24/7 traffic<br/>Low latency critical| RawMode
    UseCase -->|Sporadic traffic<br/>Cost optimization| ServerlessMode
    
    style RawMode fill:#fff4e1
    style ServerlessMode fill:#e1f5ff
    style UseCase fill:#f0e1ff
```

**Simple Explanation:**

**Choose Raw Deployment when:**
- You have steady, 24/7 traffic
- You can't tolerate cold starts
- You want simple, predictable behavior
- You're familiar with standard Kubernetes
- Cost of running minimum pods is acceptable

**Choose Serverless when:**
- Traffic is sporadic or unpredictable
- Cost optimization is critical
- You can tolerate 5-30 second cold starts
- You want advanced features (canary, revisions)
- You don't mind managing Knative

## Pod Structure

```mermaid
flowchart TB
    subgraph Pod["Inference Pod"]
        subgraph Init["Init Container"]
            StorageInit[storage-initializer<br/>Downloads model from S3]
        end
        
        subgraph Main["Main Containers"]
            Predictor[kserve-container<br/>Predictor - Serves model]
            
            Agent[agent<br/>Optional - Monitoring]
        end
        
        subgraph Volumes["Volumes"]
            ModelVol[model-dir<br/>emptyDir: 10Gi]
            ShmVol[shm<br/>emptyDir: 2Gi]
        end
    end
    
    Init -->|Downloads to| ModelVol
    Predictor -->|Reads from| ModelVol
    Predictor -->|Uses| ShmVol
    
    style Init fill:#e1f5ff
    style Main fill:#fff4e1
    style Volumes fill:#f0e1ff
```

**Simple Explanation:**
Each pod in Raw mode has the same structure as Serverless:
1. **Init container** downloads your model once
2. **Predictor container** loads model and serves requests
3. **Agent container** (optional) monitors and logs
4. **Volumes** store the model and provide shared memory

Nothing special - just standard Kubernetes pod structure!

## Monitoring & Operations

```mermaid
flowchart TB
    subgraph Operations["Standard K8s Operations"]
        Kubectl[kubectl commands work!]
        
        subgraph Commands["Common Commands"]
            GetPods[kubectl get pods<br/>See all inference pods]
            Logs[kubectl logs<br/>Check container logs]
            Describe[kubectl describe deployment<br/>See deployment status]
            Scale[kubectl scale deployment<br/>Manual scaling]
            Restart[kubectl rollout restart<br/>Restart pods]
        end
        
        subgraph Monitoring["Monitoring"]
            Metrics[kubectl top pods<br/>CPU/Memory usage]
            Events[kubectl get events<br/>See pod events]
            HPAStatus[kubectl get hpa<br/>See autoscaler status]
        end
    end
    
    subgraph Tools["Standard Tools Work"]
        Prometheus[Prometheus<br/>Scrapes pod metrics]
        Grafana[Grafana<br/>Visualize metrics]
        Logs2[Logging<br/>Standard log collectors]
    end
    
    Operations --> Tools
    
    style Operations fill:#e1f5ff
    style Commands fill:#fff4e1
    style Monitoring fill:#f0e1ff
    style Tools fill:#e1ffe1
```

**Simple Explanation:**
Everything you know about Kubernetes works:
- `kubectl get/describe/logs` - all work normally
- Standard monitoring tools - Prometheus, Grafana work out of the box
- No special commands needed - it's just a Kubernetes deployment!
- Debug just like any other app in Kubernetes

## Updating Models

```mermaid
flowchart TB
    Update[Update InferenceService]
    
    subgraph UpdateProcess["Update Process"]
        ChangeSpec[Change storageUri or<br/>other spec fields]
        ControllerDetect[Controller Detects Change]
        UpdateDeployment[Update Deployment Spec]
        RollingUpdate[K8s Rolling Update]
        
        subgraph Rolling["Rolling Update Process"]
            NewPod1[Create new pod]
            Wait1[Wait until ready]
            OldPod1[Terminate old pod]
            NewPod2[Create next new pod]
            Continue[Continue...]
        end
    end
    
    Complete[Update Complete<br/>Zero Downtime]
    
    Update --> ChangeSpec
    ChangeSpec --> ControllerDetect
    ControllerDetect --> UpdateDeployment
    UpdateDeployment --> RollingUpdate
    RollingUpdate --> Rolling
    Rolling --> Complete
    
    style UpdateProcess fill:#e1f5ff
    style Rolling fill:#fff4e1
    style Complete fill:#99ff99
```

**Simple Explanation:**
Updating is safe and predictable:
1. Update your InferenceService YAML (new model, new image, etc.)
2. Controller updates the Deployment
3. Kubernetes does standard rolling update:
   - Starts new pod with new model
   - Waits until new pod is ready
   - Terminates old pod
   - Repeats for all pods
4. Zero downtime! Traffic always goes to ready pods

## Networking Configuration

```mermaid
flowchart TB
    subgraph Network["Networking Options"]
        subgraph WithIstio["With Istio"]
            Gateway[Istio Gateway<br/>External access]
            VS[VirtualService<br/>Routing rules]
            Service[Service<br/>ClusterIP]
            Pods1[Pods]
            
            Gateway --> VS
            VS --> Service
            Service --> Pods1
        end
        
        subgraph WithoutIstio["Without Istio"]
            Ingress[K8s Ingress<br/>External access]
            Service2[Service<br/>ClusterIP]
            Pods2[Pods]
            
            Ingress --> Service2
            Service2 --> Pods2
        end
        
        subgraph Internal["Internal Only"]
            Service3[Service<br/>ClusterIP only]
            Pods3[Pods]
            InternalClient[Other pods in cluster]
            
            InternalClient --> Service3
            Service3 --> Pods3
        end
    end
    
    style WithIstio fill:#e1f5ff
    style WithoutIstio fill:#fff4e1
    style Internal fill:#f0e1ff
```

**Simple Explanation:**
You have options for how clients reach your model:
- **With Istio**: Use Gateway + VirtualService (most common)
- **Without Istio**: Use standard Kubernetes Ingress
- **Internal only**: Just use the Service (cluster-internal access)

All standard Kubernetes networking - nothing special!

## Best Practices

### 1. Resource Configuration

```yaml
# Good: Set proper resource limits
resources:
  requests:
    cpu: 2
    memory: 4Gi
  limits:
    cpu: 4
    memory: 8Gi
    nvidia.com/gpu: 1
```

**Why**: HPA needs requests to calculate scaling. Limits prevent pods from consuming all node resources.

### 2. Replica Configuration

```yaml
# Good: Set reasonable min/max
minReplicas: 2  # Always have 2 for HA
maxReplicas: 10  # Cap at 10 to control costs
```

**Why**: Min ensures availability, max prevents runaway scaling costs.

### 3. HPA Configuration

```yaml
# Good: Configure HPA properly
scaleTarget: 70  # Not too aggressive
scaleMetric: cpu  # Use CPU for predictable scaling
```

**Why**: 70% gives room for traffic spikes. CPU is reliable metric for inference workloads.

### 4. Health Probes

```yaml
# Ensure probes are configured
readinessProbe:
  httpGet:
    path: /v1/models/my-model
    port: 8080
  initialDelaySeconds: 30
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 10
```

**Why**: Prevents traffic to unhealthy pods, restarts hung containers.

## Troubleshooting

### Problem: Pods Not Scaling

```mermaid
flowchart TB
    Problem[Pods Stuck at minReplicas]
    
    subgraph Checks["Check These"]
        C1[HPA created?<br/>kubectl get hpa]
        C2[Metrics available?<br/>kubectl top pods]
        C3[Resource requests set?<br/>Check pod spec]
        C4[Target reasonable?<br/>Not too high]
    end
    
    subgraph Solutions["Solutions"]
        S1[Ensure metrics-server installed]
        S2[Set proper resource requests]
        S3[Lower scaleTarget value]
        S4[Check HPA status for errors]
    end
    
    Problem --> Checks
    Checks --> Solutions
    
    style Problem fill:#ff9999
    style Checks fill:#fff4e1
    style Solutions fill:#99ff99
```

### Problem: High Latency

```mermaid
flowchart TB
    Problem[Response Times Too High]
    
    subgraph Checks["Investigate"]
        C1[Pods at max capacity?<br/>Check CPU/Memory]
        C2[Too few replicas?<br/>Increase minReplicas]
        C3[Model loading slow?<br/>Check init container]
        C4[Network issues?<br/>Check service mesh]
    end
    
    subgraph Solutions["Fix It"]
        S1[Increase maxReplicas]
        S2[Lower scaleTarget]
        S3[Add more resources per pod]
        S4[Optimize model loading]
    end
    
    Problem --> Checks
    Checks --> Solutions
    
    style Problem fill:#ff9999
    style Checks fill:#fff4e1
    style Solutions fill:#99ff99
```

## When to Use Raw Deployment

```mermaid
flowchart TB
    Decision{Choose Deployment Mode}
    
    subgraph UseRaw["Use Raw Deployment"]
        R1[Steady 24/7 traffic]
        R2[Low latency critical]
        R3[Simple infrastructure preferred]
        R4[Team knows standard K8s]
        R5[No cold start tolerance]
    end
    
    subgraph UseServerless["Use Serverless"]
        S1[Sporadic or unpredictable traffic]
        S2[Cost optimization critical]
        S3[Can tolerate cold starts]
        S4[Need advanced features]
        S5[Have Knative expertise]
    end
    
    Decision -->|Your needs match| UseRaw
    Decision -->|Your needs match| UseServerless
    
    style UseRaw fill:#99ff99
    style UseServerless fill:#99ccff
```

**Simple Explanation:**
Pick Raw Deployment if you need:
- ✅ Simple and predictable
- ✅ Always ready (no cold start)
- ✅ Standard Kubernetes (no Knative)
- ✅ Easy to understand and debug
- ❌ Accept: Always running (costs more)
- ❌ Accept: Basic scaling (no request-based autoscaling)

## Summary

**Raw Kubernetes Deployment Mode = Simple & Predictable**

```mermaid
flowchart LR
    Raw[Raw Deployment] --> Simple[Standard K8s<br/>No Knative]
    Simple --> Always[Always Running<br/>No cold start]
    Always --> HPA[HPA Scaling<br/>CPU/Memory based]
    HPA --> Easy[Easy to Debug<br/>Standard tools work]
    
    style Raw fill:#e1f5ff
    style Simple fill:#fff4e1
    style Always fill:#f0e1ff
    style HPA fill:#e1ffe1
    style Easy fill:#99ff99
```

**Key Takeaway**: If you know Kubernetes, you know Raw Deployment mode. It's just a regular Deployment with an InferenceService wrapper - simple, reliable, and predictable!

## Related Components

- [Overall Architecture](./01-KSERVE-OVERALL-ARCHITECTURE.md) - Deployment modes comparison
- [InferenceService Controller](./02-INFERENCESERVICE-CONTROLLER.md) - How controller creates resources
- [Knative Integration](./10-KNATIVE-INTEGRATION.md) - Serverless alternative (coming soon)
- [Autoscaling Mechanisms](./11-AUTOSCALING-MECHANISMS.md) - HPA deep dive (coming soon)

