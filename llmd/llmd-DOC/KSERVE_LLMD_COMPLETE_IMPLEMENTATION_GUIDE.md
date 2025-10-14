# KServe LLMD Complete Implementation Guide

**Document Version:** 2.0  
**Date:** October 13, 2025  
**Purpose:** Complete guide to KServe LLMInferenceService implementation with llm-d architecture

---

## 📖 Table of Contents

1. [Overview: llm-d Architecture in KServe](#overview-llm-d-architecture-in-kserve)
2. [KServe LLMD Architecture](#kserve-llmd-architecture)
3. [How KServe Controller Implements llm-d Concepts](#how-kserve-controller-implements-llm-d-concepts)
4. [Complete Feature Implementation Guide](#complete-feature-implementation-guide)
5. [Resource Creation Flow](#resource-creation-flow)
6. [Request Flow Architecture](#request-flow-architecture)
7. [Integration Points](#integration-points)
8. [Production Considerations](#production-considerations)

---

## Overview: llm-d Architecture in KServe

### The Relationship

```
┌────────────────────────────────────────────────────────────────┐
│ llm-d Project (Kubernetes-Native Stack)                                   │
├────────────────────────────────────────────────────────────────┤
│ Components:                                                               │
│ • Inference Gateway (IGW) - Request scheduling & routing                  │
│ • vLLM Model Server - Inference engine                                    │
│ • Endpoint Picker (EPP) - Intelligent pod selection                       │
│ • InferencePool - Service discovery                                       │
│ • HTTPRoute - Gateway API routing                                         │
│                                                                           │
│ Architecture Patterns:                                                    │
│ • Disaggregated Prefill/Decode                                            │
│ • KV-cache-aware routing                                                  │
│ • RDMA/NIXL for KV transfer                                               │
│ • Helm-based deployment                                                   │
└────────────────────────────────────────────────────────────────┘
                            │
                            │ Inspired ↓
                            │
┌───────────────────────────────────────────────────────────────────┐
│ KServe LLMInferenceService (CRD Implementation)                   │
├───────────────────────────────────────────────────────────────────┤
│ Implementation:                                                   │
│ • Kubernetes CRD (serving.kserve.io/v1alpha1)                     │
│ • Controller-based reconciliation                                 │
│ • Automatic resource creation                                     │
│ • Declarative configuration                                       │
│                                                                   │
│ Adopts llm-d Patterns:                                            │
│ • Prefill/Decode split via controller                             │
│ • Gateway API integration                                         │
│ • InferencePool creation                                          │
│ • Template-based configuration                                    │
└───────────────────────────────────────────────────────────────────┘
```

### Key Differences in Implementation

| Aspect | llm-d Project | KServe LLMD CRD |
|--------|---------------|-----------------|
| **Deployment** | Helm charts (manual) | CRD (controller-automated) |
| **Scheduler** | Deployed separately (EPP) | Created by controller (optional) |
| **Configuration** | Values files | YAML spec |
| **Lifecycle** | User-managed | Controller-managed |
| **Flexibility** | High (customize anything) | Medium (within CRD schema) |
| **Resources Created** | User defines in Helm | Controller auto-creates |

---

## KServe LLMD Architecture

### Component Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        KServe Control Plane                          │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  LLMISVCReconciler Controller                              │    │
│  │  (pkg/controller/v1alpha1/llmisvc/)                        │    │
│  │                                                            │    │
│  │  Watches:                                                  │    │
│  │  • LLMInferenceService CRD                                 │    │
│  │  • LLMInferenceServiceConfig CRD                           │    │
│  │                                                            │    │
│  │  Reconciles:                                               │    │
│  │  1. Merges baseRefs configs                                │    │
│  │  2. Replaces template variables                            │    │
│  │  3. Creates Kubernetes resources                           │    │
│  │     ├─ Deployments (decode, prefill, workers)             │    │
│  │     ├─ Services (ClusterIP, Headless)                     │    │
│  │     ├─ HTTPRoute (Gateway API)                            │    │
│  │     ├─ InferencePool (service discovery)                  │    │
│  │     └─ InferenceModel (metadata)                          │    │
│  │  4. Updates status                                         │    │
│  └────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            │ Creates ↓
                            │
┌──────────────────────────────────────────────────────────────────────┐
│                        Data Plane Resources                          │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Prefill Deployment (if spec.prefill exists)                │   │
│  │  ├─ Replicas: spec.prefill.replicas                         │   │
│  │  ├─ Labels: llm-d.ai/role=prefill                           │   │
│  │  └─ Containers:                                             │   │
│  │     └─ storage-initializer (init) + main (vLLM)            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Decode Deployment                                           │   │
│  │  ├─ Replicas: spec.replicas                                 │   │
│  │  ├─ Labels: llm-d.ai/role=decode                            │   │
│  │  └─ Containers:                                             │   │
│  │     ├─ storage-initializer (init)                           │   │
│  │     ├─ llm-d-routing-sidecar (init, restartPolicy=Always)  │   │
│  │     └─ main (vLLM)                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Scheduler Deployment (if spec.router.scheduler exists)     │   │
│  │  └─ llm-d-inference-scheduler (Endpoint Picker - EPP)       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Gateway API Resources                                       │   │
│  │  ├─ HTTPRoute (routing rules)                               │   │
│  │  ├─ InferencePool (pod discovery + health)                  │   │
│  │  └─ InferenceModel (model metadata)                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### Controller Reconciliation Flow

```go
// Simplified from pkg/controller/v1alpha1/llmisvc/reconciler.go

func (r *LLMISVCReconciler) Reconcile(ctx context.Context, req ctrl.Request) {
    // 1. Fetch LLMInferenceService
    llmisvc := &v1alpha1.LLMInferenceService{}
    r.Get(ctx, req.NamespacedName, llmisvc)
    
    // 2. Merge baseRefs configurations
    mergedSpec := r.MergeBaseRefs(llmisvc)
    
    // 3. Replace template variables ({{ .Name }}, {{ .Namespace }}, etc.)
    finalSpec := r.ReplaceVariables(mergedSpec, llmisvc)
    
    // 4. Create/Update Decode Deployment
    decodeDeployment := r.CreateDecodeDeployment(finalSpec)
    r.CreateOrUpdate(ctx, decodeDeployment)
    
    // 5. Create/Update Prefill Deployment (if spec.prefill exists)
    if finalSpec.Prefill != nil {
        prefillDeployment := r.CreatePrefillDeployment(finalSpec)
        r.CreateOrUpdate(ctx, prefillDeployment)
    }
    
    // 6. Create/Update Scheduler (if spec.router.scheduler exists)
    if finalSpec.Router != nil && finalSpec.Router.Scheduler != nil {
        schedulerDeployment := r.CreateSchedulerDeployment(finalSpec)
        r.CreateOrUpdate(ctx, schedulerDeployment)
    }
    
    // 7. Create InferencePool (for service discovery)
    inferencePool := r.CreateInferencePool(finalSpec)
    r.CreateOrUpdate(ctx, inferencePool)
    
    // 8. Create HTTPRoute (for Gateway API routing)
    httpRoute := r.CreateHTTPRoute(finalSpec)
    r.CreateOrUpdate(ctx, httpRoute)
    
    // 9. Update status with URL and conditions
    r.UpdateStatus(ctx, llmisvc)
}
```

---

## How KServe Controller Implements llm-d Concepts

### 1. Disaggregated Prefill/Decode

**llm-d Implementation:**
```yaml
# llm-d uses Helm values
prefill:
  replicas: 2
  parallelism:
    tensor: 8

decode:
  replicas: 8
  parallelism:
    tensor: 2
```

**KServe LLMD Implementation:**
```yaml
# KServe uses CRD spec
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-70b
spec:
  # Decode configuration (top-level)
  replicas: 8
  parallelism:
    tensor: 2
  
  # Prefill configuration (nested)
  prefill:
    replicas: 2
    parallelism:
      tensor: 8
```

**What the Controller Does:**

```go
// pkg/controller/v1alpha1/llmisvc/deployment.go

func (r *LLMISVCReconciler) CreatePrefillDeployment(spec v1alpha1.LLMInferenceServiceSpec) *appsv1.Deployment {
    deployment := &appsv1.Deployment{
        ObjectMeta: metav1.ObjectMeta{
            Name: fmt.Sprintf("%s-kserve-prefill", llmisvc.Name),
            Labels: map[string]string{
                "llm-d.ai/role": "prefill",  // llm-d label for identification
                "app.kubernetes.io/component": "prefill",
            },
        },
        Spec: appsv1.DeploymentSpec{
            Replicas: spec.Prefill.Replicas,
            Template: corev1.PodTemplateSpec{
                Spec: corev1.PodSpec{
                    InitContainers: []corev1.Container{
                        {
                            Name: "storage-initializer",
                            // Downloads model from URI
                        },
                    },
                    Containers: []corev1.Container{
                        {
                            Name: "main",
                            Args: []string{
                                "--port=8000",
                                fmt.Sprintf("--tensor-parallel-size=%d", spec.Prefill.Parallelism.Tensor),
                                // Prefill-specific args
                            },
                        },
                    },
                },
            },
        },
    }
    return deployment
}

func (r *LLMISVCReconciler) CreateDecodeDeployment(spec v1alpha1.LLMInferenceServiceSpec) *appsv1.Deployment {
    deployment := &appsv1.Deployment{
        ObjectMeta: metav1.ObjectMeta{
            Name: fmt.Sprintf("%s-kserve", llmisvc.Name),
            Labels: map[string]string{
                "llm-d.ai/role": "decode",  // llm-d label
                "app.kubernetes.io/component": "decode",
            },
        },
        Spec: appsv1.DeploymentSpec{
            Replicas: spec.Replicas,
            Template: corev1.PodTemplateSpec{
                Spec: corev1.PodSpec{
                    InitContainers: []corev1.Container{
                        {
                            Name: "storage-initializer",
                        },
                        {
                            Name: "llm-d-routing-sidecar",  // llm-d routing component
                            RestartPolicy: "Always",  // Runs as sidecar
                            // Routes requests to prefill or local vLLM
                        },
                    },
                    Containers: []corev1.Container{
                        {
                            Name: "main",
                            Args: []string{
                                "--port=8001",  // Internal port (sidecar uses 8000)
                                fmt.Sprintf("--tensor-parallel-size=%d", spec.Parallelism.Tensor),
                            },
                        },
                    },
                },
            },
        },
    }
    return deployment
}
```

### 2. Intelligent Scheduling (Endpoint Picker)

**llm-d Implementation:**
```bash
# Deployed via Helm
helm install epp \
  oci://registry/inferencepool \
  --set scheduler.enabled=true
```

**KServe LLMD Implementation:**
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-70b
spec:
  router:
    scheduler: {}  # Controller creates scheduler deployment
```

**What the Controller Does:**

```go
func (r *LLMISVCReconciler) CreateSchedulerDeployment(spec v1alpha1.LLMInferenceServiceSpec) *appsv1.Deployment {
    return &appsv1.Deployment{
        ObjectMeta: metav1.ObjectMeta{
            Name: fmt.Sprintf("%s-kserve-router-scheduler", llmisvc.Name),
        },
        Spec: appsv1.DeploymentSpec{
            Replicas: ptr.To(int32(1)),
            Template: corev1.PodTemplateSpec{
                Spec: corev1.PodSpec{
                    Containers: []corev1.Container{
                        {
                            Name: "main",
                            Image: "ghcr.io/llm-d/llm-d-inference-scheduler:latest",
                            Ports: []corev1.ContainerPort{
                                {Name: "grpc", ContainerPort: 9002},
                                {Name: "health", ContainerPort: 9003},
                                {Name: "metrics", ContainerPort: 9090},
                            },
                            Env: []corev1.EnvVar{
                                {
                                    Name: "INFERENCE_POOL_NAME",
                                    Value: fmt.Sprintf("%s-inference-pool", llmisvc.Name),
                                },
                            },
                        },
                    },
                },
            },
        },
    }
}
```

### 3. InferencePool (Service Discovery)

**llm-d Concept:**
- Tracks all vLLM pods (prefill + decode)
- Provides health status
- Used by EPP for pod selection

**KServe LLMD Implementation:**

```go
func (r *LLMISVCReconciler) CreateInferencePool(spec v1alpha1.LLMInferenceServiceSpec) *igwapi.InferencePool {
    pool := &igwapi.InferencePool{
        ObjectMeta: metav1.ObjectMeta{
            Name: fmt.Sprintf("%s-inference-pool", llmisvc.Name),
        },
        Spec: igwapi.InferencePoolSpec{
            Selector: &metav1.LabelSelector{
                MatchLabels: map[string]string{
                    "app.kubernetes.io/name": llmisvc.Name,
                },
            },
            TargetRef: igwapi.InferenceTarget{
                Kind: "Service",
                Name: fmt.Sprintf("%s-kserve-workload-svc", llmisvc.Name),
            },
        },
    }
    return pool
}
```

**Generated InferencePool:**
```yaml
apiVersion: inference.networking.k8s.io/v1alpha1
kind: InferencePool
metadata:
  name: llama-70b-inference-pool
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: llama-70b
  targetRef:
    kind: Service
    name: llama-70b-kserve-workload-svc
```

### 4. HTTPRoute (Gateway API Routing)

**llm-d Implementation:**
```yaml
# User creates HTTPRoute manually
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: llm-route
spec:
  parentRefs:
  - name: my-gateway
  rules:
  - backendRefs:
    - group: inference.networking.k8s.io
      kind: InferencePool
      name: llama-70b-inference-pool
```

**KServe LLMD Implementation:**
```yaml
# Controller auto-creates
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
spec:
  router:
    gateway: {}  # Use default gateway
    route:
      http:
        rules:
        - matches:
          - path:
              type: PathPrefix
              value: /
```

**What the Controller Creates:**

```go
func (r *LLMISVCReconciler) CreateHTTPRoute(spec v1alpha1.LLMInferenceServiceSpec) *gwapiv1.HTTPRoute {
    return &gwapiv1.HTTPRoute{
        ObjectMeta: metav1.ObjectMeta{
            Name: fmt.Sprintf("%s-kserve-route", llmisvc.Name),
        },
        Spec: gwapiv1.HTTPRouteSpec{
            ParentRefs: []gwapiv1.ParentReference{
                {
                    Name: "default-gateway",  // From spec.router.gateway
                },
            },
            Rules: []gwapiv1.HTTPRouteRule{
                {
                    Matches: []gwapiv1.HTTPRouteMatch{
                        {
                            Path: &gwapiv1.HTTPPathMatch{
                                Type:  ptr.To(gwapiv1.PathMatchPathPrefix),
                                Value: ptr.To(fmt.Sprintf("/%s/%s", llmisvc.Namespace, llmisvc.Name)),
                            },
                        },
                    },
                    BackendRefs: []gwapiv1.HTTPBackendRef{
                        {
                            BackendRef: gwapiv1.BackendRef{
                                BackendObjectReference: gwapiv1.BackendObjectReference{
                                    Group: ptr.To(gwapiv1.Group("inference.networking.k8s.io")),
                                    Kind:  ptr.To(gwapiv1.Kind("InferencePool")),
                                    Name:  gwapiv1.ObjectName(fmt.Sprintf("%s-inference-pool", llmisvc.Name)),
                                    Port:  ptr.To(gwapiv1.PortNumber(8000)),
                                },
                            },
                        },
                    },
                    Filters: []gwapiv1.HTTPRouteFilter{
                        {
                            Type: gwapiv1.HTTPRouteFilterURLRewrite,
                            URLRewrite: &gwapiv1.HTTPURLRewriteFilter{
                                Path: &gwapiv1.HTTPPathModifier{
                                    Type:               gwapiv1.PrefixMatchHTTPPathModifier,
                                    ReplacePrefixMatch: ptr.To("/"),
                                },
                            },
                        },
                    },
                },
            },
        },
    }
}
```

---

## Complete Feature Implementation Guide

### Feature 1: Basic Model Deployment

**User YAML:**
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: basic-llm
  namespace: default
spec:
  model:
    uri: hf://meta-llama/Llama-3-8B
  replicas: 2
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:latest
      resources:
        requests:
          nvidia.com/gpu: "1"
  router:
    gateway: {}
    route: {}
```

**What the Controller Creates:**

1. **Deployment:** `basic-llm-kserve`
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: basic-llm-kserve
     labels:
       app.kubernetes.io/name: basic-llm
       app.kubernetes.io/component: decode
   spec:
     replicas: 2
     template:
       spec:
         initContainers:
         - name: storage-initializer
           image: kserve/storage-initializer:latest
           args:
           - hf://meta-llama/Llama-3-8B
           - /mnt/models
         containers:
         - name: main
           image: vllm/vllm-openai:latest
           args:
           - --port=8000
           - --model=/mnt/models
           - --served-model-name=basic-llm
   ```

2. **Service:** `basic-llm-kserve-workload-svc`
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: basic-llm-kserve-workload-svc
   spec:
     selector:
       app.kubernetes.io/name: basic-llm
     ports:
     - port: 8000
       targetPort: 8000
   ```

3. **InferencePool:** `basic-llm-inference-pool`
4. **HTTPRoute:** `basic-llm-kserve-route`
5. **InferenceModel:** `basic-llm-model`

**Total Resources Created:** 5

---

### Feature 2: Configuration Inheritance (BaseRefs)

**llm-d Pattern:**
- Helm values inheritance
- Override patterns

**KServe LLMD Implementation:**

```yaml
# Base configuration
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: standard-config
spec:
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      resources:
        requests:
          cpu: "4"
          memory: "16Gi"
  router:
    gateway: {}

---
# Service using base
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: my-llm
spec:
  baseRefs:
  - name: standard-config
  model:
    uri: hf://meta-llama/Llama-3-8B
  replicas: 3
```

**Controller Logic:**

```go
// pkg/controller/v1alpha1/llmisvc/config_merge.go

func (r *LLMISVCReconciler) MergeBaseRefs(llmisvc *v1alpha1.LLMInferenceService) v1alpha1.LLMInferenceServiceSpec {
    mergedSpec := v1alpha1.LLMInferenceServiceSpec{}
    
    // 1. Start with empty spec
    
    // 2. Apply each baseRef in order (last wins on conflicts)
    for _, baseRef := range llmisvc.Spec.BaseRefs {
        config := &v1alpha1.LLMInferenceServiceConfig{}
        r.Get(ctx, types.NamespacedName{
            Name:      baseRef.Name,
            Namespace: llmisvc.Namespace,
        }, config)
        
        // Strategic merge
        mergedSpec = StrategicMerge(mergedSpec, config.Spec)
    }
    
    // 3. Apply LLMInferenceService spec (highest priority)
    mergedSpec = StrategicMerge(mergedSpec, llmisvc.Spec)
    
    return mergedSpec
}

func StrategicMerge(base, override v1alpha1.LLMInferenceServiceSpec) v1alpha1.LLMInferenceServiceSpec {
    // Merge rules:
    // - Scalars: override wins
    // - Lists: append
    // - Maps: deep merge
    
    result := base.DeepCopy()
    
    if override.Model.URI != "" {
        result.Model = override.Model
    }
    
    if override.Replicas != nil {
        result.Replicas = override.Replicas
    }
    
    if override.Template.Containers != nil {
        result.Template.Containers = override.Template.Containers
    }
    
    return *result
}
```

---

### Feature 3: Template Variables

**llm-d Pattern:**
- Helm templating
- Dynamic value substitution

**KServe LLMD Implementation:**

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: template-config
spec:
  model:
    name: "{{.Name}}-model"
  template:
    containers:
    - name: main
      env:
      - name: MODEL_NAME
        value: "{{.Name}}"
      - name: NAMESPACE
        value: "{{.Namespace}}"
      args:
      - --served-model-name={{.Name}}
      - --tensor-parallel-size={{.Parallelism.Tensor}}
```

**Controller Logic:**

```go
// pkg/controller/v1alpha1/llmisvc/template.go

func (r *LLMISVCReconciler) ReplaceVariables(spec v1alpha1.LLMInferenceServiceSpec, llmisvc *v1alpha1.LLMInferenceService) v1alpha1.LLMInferenceServiceSpec {
    data := map[string]interface{}{
        "Name":      llmisvc.Name,
        "Namespace": llmisvc.Namespace,
        "Spec":      llmisvc.Spec,
        "Parallelism": map[string]int{
            "Tensor":   spec.Parallelism.Tensor,
            "Pipeline": spec.Parallelism.Pipeline,
            "Data":     spec.Parallelism.Data,
            "Expert":   spec.Parallelism.Expert,
        },
    }
    
    // Use text/template to replace variables
    tmpl := template.New("spec")
    specJSON, _ := json.Marshal(spec)
    specStr := string(specJSON)
    
    result, err := tmpl.Parse(specStr)
    if err != nil {
        return spec
    }
    
    var buf bytes.Buffer
    result.Execute(&buf, data)
    
    var finalSpec v1alpha1.LLMInferenceServiceSpec
    json.Unmarshal(buf.Bytes(), &finalSpec)
    
    return finalSpec
}
```

**⚠️ Known Issue:**
This feature is currently buggy in v1alpha1. Template variables are often not substituted correctly.

---

### Feature 4: Prefill/Decode Disaggregation

**Complete Implementation:**

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-70b
spec:
  model:
    uri: hf://meta-llama/Llama-3-70B
  
  # Prefill configuration
  prefill:
    replicas: 2
    parallelism:
      tensor: 8
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        resources:
          requests:
            nvidia.com/gpu: "8"
            cpu: "32"
            memory: "256Gi"
  
  # Decode configuration (top-level)
  replicas: 8
  parallelism:
    tensor: 2
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          nvidia.com/gpu: "2"
          cpu: "16"
          memory: "64Gi"
  
  # Enable scheduler for intelligent routing
  router:
    gateway: {}
    route: {}
    scheduler: {}
```

**Resources Created:**

```
Prefill Deployment (2 pods):
└─ llama-70b-kserve-prefill
   ├─ Pod: llama-70b-kserve-prefill-xxxxx-aaaaa
   │  ├─ Init: storage-initializer (downloads model)
   │  └─ Container: main (vLLM prefill mode)
   │     └─ 8 GPUs, port 8000
   └─ Pod: llama-70b-kserve-prefill-xxxxx-bbbbb
      └─ Same as above

Decode Deployment (8 pods):
└─ llama-70b-kserve
   ├─ Pod: llama-70b-kserve-yyyyy-ccccc
   │  ├─ Init: storage-initializer
   │  ├─ Init: llm-d-routing-sidecar (restartPolicy: Always)
   │  │  └─ Port 8000 (external), routes to prefill or local decode
   │  └─ Container: main (vLLM decode mode)
   │     └─ 2 GPUs, port 8001 (internal)
   ├─ ... (7 more pods)

Scheduler Deployment (1 pod):
└─ llama-70b-kserve-router-scheduler
   └─ Pod: llama-70b-kserve-router-scheduler-zzzzz
      └─ Container: main (llm-d-inference-scheduler / EPP)
         └─ Ports: 9002 (gRPC), 9003 (health), 9090 (metrics)

Gateway API Resources:
├─ InferencePool: llama-70b-inference-pool
├─ HTTPRoute: llama-70b-kserve-route
└─ InferenceModel: llama-70b-model

Total: 11 pods + 3 Gateway API resources
GPUs: 16 (prefill) + 16 (decode) = 32 GPUs
```

---

### Feature 5: Multi-GPU Parallelism

**Types Supported:**

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
spec:
  parallelism:
    tensor: 8      # Model sharding across GPUs
    pipeline: 2    # Model stages across GPUs
    data: 4        # Batch parallelism
    expert: 16     # MoE expert parallelism
```

**Controller Translation to vLLM Args:**

```go
func (r *LLMISVCReconciler) BuildVLLMArgs(spec v1alpha1.LLMInferenceServiceSpec) []string {
    args := []string{
        "--port=8000",
        "--model=/mnt/models",
    }
    
    if spec.Parallelism.Tensor > 0 {
        args = append(args, fmt.Sprintf("--tensor-parallel-size=%d", spec.Parallelism.Tensor))
    }
    
    if spec.Parallelism.Pipeline > 0 {
        args = append(args, fmt.Sprintf("--pipeline-parallel-size=%d", spec.Parallelism.Pipeline))
    }
    
    if spec.Parallelism.Data > 0 {
        args = append(args, fmt.Sprintf("--distributed-executor-backend=ray"))
        // Ray will handle data parallelism
    }
    
    if spec.Parallelism.Expert > 0 {
        args = append(args, fmt.Sprintf("--tensor-parallel-size=%d", spec.Parallelism.Expert))
        args = append(args, "--enable-expert-parallel")
    }
    
    return args
}
```

**GPU Resource Allocation:**

```go
func (r *LLMISVCReconciler) SetGPUResources(container *corev1.Container, parallelism ParallelismSpec) {
    gpuCount := parallelism.Tensor
    if gpuCount == 0 {
        gpuCount = 1
    }
    
    container.Resources.Requests = corev1.ResourceList{
        corev1.ResourceName("nvidia.com/gpu"): resource.MustParse(fmt.Sprintf("%d", gpuCount)),
    }
    container.Resources.Limits = container.Resources.Requests
}
```

**Critical Rule:**
```
parallelism.tensor value MUST match resources.requests.gpu value
```

---

### Feature 6: Multi-Node Deployment

**User YAML:**
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-405b
spec:
  model:
    uri: hf://meta-llama/Llama-3-405B
  
  replicas: 2  # 2 leader-worker groups
  parallelism:
    pipeline: 4  # 4-stage pipeline
  
  # Leader pod
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "8"
  
  # Worker pods
  worker:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "8"
```

**Controller Uses LeaderWorkerSet:**

```go
func (r *LLMISVCReconciler) CreateLeaderWorkerSet(spec v1alpha1.LLMInferenceServiceSpec) *lwsv1.LeaderWorkerSet {
    return &lwsv1.LeaderWorkerSet{
        ObjectMeta: metav1.ObjectMeta{
            Name: fmt.Sprintf("%s-lws", llmisvc.Name),
        },
        Spec: lwsv1.LeaderWorkerSetSpec{
            Replicas: spec.Replicas,  // Number of groups
            LeaderWorkerTemplate: lwsv1.LeaderWorkerTemplate{
                Size: ptr.To(int32(spec.Parallelism.Pipeline)),  // Workers per leader
                LeaderTemplate: &corev1.PodTemplateSpec{
                    Spec: spec.Template.Spec,
                },
                WorkerTemplate: corev1.PodTemplateSpec{
                    Spec: spec.Worker.Spec,
                },
            },
        },
    }
}
```

**Resources Created:**
```
Group 1:
├─ Leader: llama-405b-lws-0 (8 GPUs)
└─ Workers:
   ├─ llama-405b-lws-0-worker-1 (8 GPUs)
   ├─ llama-405b-lws-0-worker-2 (8 GPUs)
   └─ llama-405b-lws-0-worker-3 (8 GPUs)

Group 2:
├─ Leader: llama-405b-lws-1 (8 GPUs)
└─ Workers:
   ├─ llama-405b-lws-1-worker-1 (8 GPUs)
   ├─ llama-405b-lws-1-worker-2 (8 GPUs)
   └─ llama-405b-lws-1-worker-3 (8 GPUs)

Total: 8 pods, 64 GPUs
```

---

## Resource Creation Flow

### Complete Reconciliation Sequence

```
1. User applies LLMInferenceService YAML
   ↓
2. KServe API Server validates CRD
   ↓
3. LLMISVCReconciler receives watch event
   ↓
4. Reconcile() function starts
   ↓
5. Fetch LLMInferenceService from API server
   ↓
6. Merge baseRefs (if any)
   ├─ Fetch each LLMInferenceServiceConfig
   ├─ Apply strategic merge (last wins)
   └─ Result: Merged spec
   ↓
7. Replace template variables
   ├─ Build template data (Name, Namespace, Spec)
   ├─ Parse spec as template
   ├─ Execute template substitution
   └─ Result: Final spec with values
   ↓
8. Create/Update Decode Deployment
   ├─ Build PodSpec with init containers
   ├─ Add routing sidecar (if disaggregated)
   ├─ Generate vLLM args from spec
   ├─ Set labels (llm-d.ai/role=decode)
   └─ CreateOrUpdate() via client
   ↓
9. Create/Update Prefill Deployment (if spec.prefill exists)
   ├─ Build separate PodSpec
   ├─ No routing sidecar
   ├─ Set labels (llm-d.ai/role=prefill)
   └─ CreateOrUpdate()
   ↓
10. Create/Update Scheduler Deployment (if spec.router.scheduler)
    ├─ Use llm-d-inference-scheduler image
    ├─ Configure InferencePool name
    └─ CreateOrUpdate()
    ↓
11. Create/Update Services
    ├─ Workload Service (ClusterIP)
    ├─ Prefill Service (if applicable)
    └─ Headless Service (for InferencePool)
    ↓
12. Create/Update InferencePool
    ├─ Set selector for pod discovery
    ├─ Configure targetRef to Service
    └─ CreateOrUpdate()
    ↓
13. Create/Update HTTPRoute
    ├─ Set parentRefs to Gateway
    ├─ Configure path: /<namespace>/<name>
    ├─ Set backendRef to InferencePool
    ├─ Add URLRewrite filter
    └─ CreateOrUpdate()
    ↓
14. Create/Update InferenceModel
    ├─ Store model metadata
    └─ CreateOrUpdate()
    ↓
15. Update LLMInferenceService Status
    ├─ Set URL from HTTPRoute
    ├─ Set Ready condition
    ├─ Add pod counts
    └─ UpdateStatus()
    ↓
16. Reconciliation complete
    ↓
17. Watch for changes and re-reconcile
```

---

## Request Flow Architecture

### Without Scheduler (Basic)

```
User Request
    ↓
Gateway (Envoy/Istio/etc)
    ↓
HTTPRoute (path: /<namespace>/<llm-name>)
    ↓
InferencePool (round-robin to pods)
    ↓
vLLM Pod (decode-only, single deployment)
    ↓
Response
```

### With Scheduler (No Disaggregation)

```
User Request
    ↓
Gateway
    ↓
HTTPRoute
    ↓
Scheduler (EPP - gRPC endpoint picker)
    ├─ Analyzes request
    ├─ Checks pod health (via InferencePool)
    ├─ Checks pod load
    └─ Selects best pod
    ↓
Selected vLLM Pod
    ↓
Response
```

### With Scheduler + Disaggregation (Full llm-d Architecture)

```
User Request: "Explain quantum computing in detail"
    ↓
Gateway (Envoy)
    ↓
HTTPRoute (routes to InferencePool)
    ↓
Scheduler (EPP)
    ├─ Request Analysis:
    │  ├─ Prompt tokens: 8 (short prompt)
    │  ├─ Expected output: ~200 tokens
    │  └─ Conversation ID: new (no KV cache)
    │
    ├─ Pod Selection Logic:
    │  ├─ Check InferencePool for available pods
    │  ├─ Prefill pods: 2 available
    │  ├─ Decode pods: 8 available
    │  ├─ No existing KV cache for this conversation
    │  └─ Decision: Route to Decode Pod 3 (lowest load)
    │
    └─ Routing Decision: → Decode Pod 3
    ↓
Decode Pod 3
    ↓
Routing Sidecar (llm-d-routing-sidecar)
    ├─ Receives request on port 8000
    ├─ Checks: Does this conversation have KV cache locally?
    ├─ Answer: No (new conversation)
    ├─ Decision: Need prefill → Forward to Prefill Pod
    └─ Selects: Prefill Pod 1 (load-balanced)
    ↓
Prefill Pod 1 (vLLM prefill mode)
    ├─ Processes prompt in parallel across 8 GPUs
    ├─ Generates KV cache
    ├─ Generates first token
    └─ Returns: First token + KV cache (via RDMA/NIXL)
    ↓
Routing Sidecar (receives KV cache)
    ├─ Stores KV cache locally
    ├─ Forwards first token + KV cache to local vLLM
    └─ Marks conversation for cache affinity
    ↓
vLLM Decode (port 8001, local)
    ├─ Receives first token + KV cache
    ├─ Generates remaining tokens sequentially
    └─ Streams tokens back
    ↓
Routing Sidecar → Gateway → User
    ↓
Stream: "Quantum computing is a revolutionary..."

─────────────────────────────────────────────

Follow-up Request: "Can you give an example?"
    ↓
Gateway → HTTPRoute → Scheduler (EPP)
    ├─ Request Analysis:
    │  ├─ Conversation ID: same as before
    │  └─ Scheduler checks: Which pod has KV cache?
    │
    ├─ KV Cache Lookup (via InferencePool metadata):
    │  └─ Decode Pod 3 has cache for this conversation
    │
    └─ Decision: Route to Decode Pod 3 (cache affinity!)
    ↓
Decode Pod 3 → Routing Sidecar
    ├─ Receives request
    ├─ Checks: KV cache exists locally? YES!
    ├─ Decision: Skip prefill, go directly to decode
    └─ Forwards to local vLLM (port 8001)
    ↓
vLLM Decode
    ├─ Reuses existing KV cache (no prefill needed!)
    ├─ Appends new prompt
    ├─ Generates new tokens
    └─ Much faster! (no prefill overhead)
    ↓
Routing Sidecar → Gateway → User
    ↓
Stream: "Sure! For example, Shor's algorithm..."
```

**Key Optimizations:**
1. **First request:** Prefill → Decode (full pipeline)
2. **Follow-up requests:** Direct to Decode (cache hit)
3. **Scheduler intelligence:** Routes to pod with cache
4. **RDMA/NIXL:** Fast KV transfer between prefill → decode

---

## Integration Points

### 1. Gateway API Integration

**KServe LLMD integrates with:**
```
Gateway API v1 (gateway.networking.k8s.io)
└─ HTTPRoute
   └─ BackendRefs to InferencePool

Inference Extension v1alpha2 (inference.networking.k8s.io)
└─ InferencePool (pod discovery + health)
└─ InferenceModel (model metadata)
```

**Supported Gateway Implementations:**
- Istio
- Kubernetes Gateway API (kgateway)
- GKE Gateway
- OpenShift Gateway

### 2. vLLM Integration

**Controller generates vLLM-compatible arguments:**
```go
args := []string{
    "--port=8000",
    "--model=/mnt/models",
    "--served-model-name=" + llmisvc.Name,
    "--tensor-parallel-size=" + fmt.Sprint(parallelism.Tensor),
    "--pipeline-parallel-size=" + fmt.Sprint(parallelism.Pipeline),
    "--dtype=float16",
    "--max-model-len=4096",
    "--enable-prefix-caching",
}

// For disaggregated mode
if isDecodeMode {
    args = append(args, "--port=8001")  // Internal port
    // Sidecar handles external port 8000
}
```

### 3. llm-d Components Integration

**KServe LLMD uses these llm-d components:**

| Component | Version | Purpose | How Used |
|-----------|---------|---------|----------|
| llm-d-inference-scheduler | v0.3.0 | EPP (Endpoint Picker) | Deployed when `spec.router.scheduler` exists |
| llm-d-routing-sidecar | v0.3.0 | Request routing in decode pods | Injected as init container (restartPolicy: Always) |
| llm-d base image | v0.2.0 | vLLM with NIXL support | Used for prefill/decode when disaggregated |

**Container Images:**
```yaml
# Scheduler
image: ghcr.io/llm-d/llm-d-inference-scheduler:v0.3.0

# Routing Sidecar
image: ghcr.io/llm-d/llm-d-routing-sidecar:v0.3.0

# vLLM with NIXL
image: ghcr.io/llm-d/llm-d:v0.2.0
```

### 4. NIXL Integration (for KV Transfer)

**When disaggregation is enabled:**
```go
// Controller adds NIXL environment variables
env := []corev1.EnvVar{
    {
        Name:  "NIXL_BACKEND",
        Value: "rdma",  // or "tcp"
    },
    {
        Name:  "NIXL_ENABLE_KV_TRANSFER",
        Value: "true",
    },
}
```

---

## Production Considerations

### Current Status (v1alpha1)

**✅ What Works:**
- Basic single-deployment LLM serving
- Configuration inheritance (baseRefs)
- Multi-GPU parallelism
- Gateway API integration
- InferencePool creation

**⚠️ Known Issues:**
- Template variables not substituting correctly
- Prefill/decode disaggregation needs testing
- Scheduler integration is experimental
- Limited production validation

**❌ Not Recommended For:**
- Production deployments (alpha status)
- Critical workloads
- Large-scale deployments

### When to Use KServe LLMD

**Good For:**
- Learning Kubernetes CRD patterns
- Experimenting with disaggregated serving
- Testing llm-d concepts in KServe
- Development environments

**Not Good For:**
- Production (use llm-d project or ServingRuntime)
- Mission-critical services
- When you need commercial support

### Migration Path

**From KServe LLMD to llm-d Project:**

1. **Export your configuration:**
   ```bash
   kubectl get llmisvc my-llm -o yaml > my-llm-kserve.yaml
   ```

2. **Convert to llm-d Helm values:**
   ```yaml
   # From KServe LLMD spec
   spec:
     replicas: 8
     prefill:
       replicas: 2
     parallelism:
       tensor: 4
   
   # To llm-d Helm values
   modelserver:
     decode:
       replicas: 8
       parallelism:
         tensor: 4
     prefill:
       replicas: 2
       parallelism:
         tensor: 4
   ```

3. **Deploy with Helm:**
   ```bash
   cd llm-d-repo/guides/pd-disaggregation
   helmfile apply -n my-namespace
   ```

### Alternative: Use ServingRuntime (RHOAI)

**For RHOAI users:**
```yaml
# More stable, GA approach
apiVersion: serving.kserve.io/v1beta1
kind: ServingRuntime
# ... (see LLMD_VS_SERVINGRUNTIME_COMPARISON_REPORT.md)
```

---

## Summary

### Key Takeaways

1. **KServe LLMD adopts llm-d architecture**
   - Uses llm-d components (scheduler, sidecar, NIXL)
   - Implements same patterns (P/D disaggregation)
   - But via Kubernetes CRD + controller automation

2. **Controller is the brain**
   - Merges baseRefs
   - Replaces variables
   - Creates all resources automatically
   - Manages full lifecycle

3. **Resources created automatically**
   - Deployments (prefill, decode, scheduler)
   - Services
   - InferencePool
   - HTTPRoute
   - InferenceModel

4. **Integration with llm-d ecosystem**
   - Uses llm-d container images
   - Adopts llm-d labels (`llm-d.ai/role`)
   - Integrates with Gateway API Inference Extension

5. **Production status: Not ready**
   - Alpha (v1alpha1)
   - Known bugs (template variables)
   - Use llm-d project or ServingRuntime for production

---

## References

**KServe Code:**
- Controller: `pkg/controller/v1alpha1/llmisvc/`
- API Types: `pkg/apis/serving/v1alpha1/llm_inference_service_types.go`
- Config Merge: `pkg/controller/v1alpha1/llmisvc/config_merge.go`

**llm-d Project:**
- Website: https://www.llm-d.ai
- GitHub: https://github.com/llm-d/llm-d
- Inference Scheduler: https://github.com/llm-d/llm-d-inference-scheduler

**Gateway API:**
- Inference Extension: https://github.com/kubernetes-sigs/gateway-api-inference-extension
- Gateway API: https://gateway-api.sigs.k8s.io/

**Related Docs:**
- [00_IMPORTANT_CLARIFICATION.md](./00_IMPORTANT_CLARIFICATION.md) - Systems comparison
- [QUICK_DECISION_GUIDE.md](./QUICK_DECISION_GUIDE.md) - Which to use
- [LLMD_USER_GUIDE_ALL_FEATURES.md](./LLMD_USER_GUIDE_ALL_FEATURES.md) - User perspective
- [LLMD_COMPLETE_ARCHITECTURE_AND_FEATURES.md](./LLMD_COMPLETE_ARCHITECTURE_AND_FEATURES.md) - Technical details

---

**Document End** - For questions, see clarification docs or llm-d community resources.

