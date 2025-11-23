# KServe Learning Guide for New Developers

This guide provides a comprehensive walkthrough of KServe's architecture, focusing on the InferenceService Status Management feature as a deep-dive example.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Development Environment Setup](#2-development-environment-setup)
3. [Architecture Overview](#3-architecture-overview)
4. [Deep Dive: InferenceService Status Management](#4-deep-dive-inferenceservice-status-management)
5. [Controller Reconciliation Loop](#5-controller-reconciliation-loop)
6. [How to Add a New Status Field](#6-how-to-add-a-new-status-field)
7. [Testing Guide](#7-testing-guide)
8. [Common Development Tasks](#8-common-development-tasks)
9. [Troubleshooting](#9-troubleshooting)
10. [Additional Resources](#10-additional-resources)

---

## 1. Project Overview

### What is KServe?

KServe is a **Kubernetes-native platform for serving machine learning models**. It provides:

- **Standardized Inference Protocol**: Works across ML frameworks (TensorFlow, PyTorch, Scikit-learn, Hugging Face, etc.)
- **Serverless Model Serving**: Auto-scaling with scale-to-zero capability
- **Advanced Deployments**: Canary rollouts, A/B testing, multi-model serving
- **Production Features**: Monitoring, explainability, pre/post-processing

### Key Components

```
kserve/
├── pkg/                          # Core Go code
│   ├── apis/serving/v1beta1/    # API definitions (CRDs)
│   ├── controller/              # Kubernetes controllers
│   ├── agent/                   # Model download agent
│   └── constants/               # Project-wide constants
├── cmd/                         # Binary entry points
│   ├── manager/                 # Controller manager
│   ├── agent/                   # Agent binary
│   └── router/                  # Router binary
├── python/                      # Python model servers
│   ├── kserve/                  # Python SDK
│   ├── sklearnserver/          # Scikit-learn server
│   ├── huggingfaceserver/      # Hugging Face server
│   └── ...
├── config/                      # Kubernetes manifests
└── test/                        # Test files
```

### Technologies Used

- **Go 1.21+**: Primary implementation language
- **Kubernetes**: Deployment platform
- **Knative Serving**: Serverless capabilities (optional)
- **Python 3.11+**: Model servers
- **Docker/Podman**: Container builds

---

## 2. Development Environment Setup

### Prerequisites

1. **Go** (1.21 or higher)
   ```bash
   go version
   # Should output: go version go1.21.x or higher
   ```

2. **Docker or Podman**
   ```bash
   docker --version
   # OR
   podman --version
   ```

3. **Kubernetes cluster** (for testing)
   - **Local options**: kind, minikube, k3d
   - **Cloud options**: GKE, EKS, AKS

4. **kubectl**
   ```bash
   kubectl version --client
   ```

5. **Make**
   ```bash
   make --version
   ```

### Initial Setup

```bash
# 1. Navigate to the project
cd /home/mwaykole/project/downstream/kserve

# 2. Install Go dependencies
go mod download

# 3. Install development tools (linters, code generators, etc.)
make clean  # Clean any old binaries
# Tools will be auto-installed when you run make commands

# 4. Verify everything is working
make fmt      # Format code
make vet      # Run go vet
make test     # Run tests (this will take a few minutes)
```

### Setting Up a Local Kubernetes Cluster

**Option 1: Using kind (Recommended for development)**

```bash
# Install kind
go install sigs.k8s.io/kind@latest

# Create a cluster
kind create cluster --name kserve-dev

# Verify
kubectl cluster-info --context kind-kserve-dev
```

**Option 2: Using minikube**

```bash
# Install minikube
# See: https://minikube.sigs.k8s.io/docs/start/

# Start cluster
minikube start --cpus 4 --memory 8192

# Verify
kubectl get nodes
```

### Building and Deploying KServe Locally

```bash
# 1. Build the controller manager binary
make manager

# This creates: bin/manager

# 2. Build Docker images (optional, for full deployment)
export KO_DOCKER_REPO=docker.io/your-username  # Or your registry
make docker-build

# 3. Deploy to your cluster (development mode)
make deploy-dev

# This will:
# - Install CRDs (Custom Resource Definitions)
# - Deploy the KServe controller
# - Set up RBAC permissions
# - Install serving runtimes

# 4. Verify deployment
kubectl get pods -n kserve
# You should see kserve-controller-manager pod running

# 5. Check logs
kubectl logs -n kserve -l control-plane=kserve-controller-manager -f
```

### Development Workflow

```bash
# 1. Make code changes

# 2. Run pre-commit checks
make precommit
# This runs:
# - go fmt (formatting)
# - go vet (static analysis)
# - golangci-lint (linting)
# - python formatting/linting
# - code generation
# - manifest generation
# - poetry lock file updates

# 3. Run tests
make test

# 4. Build and test your changes
make manager
./bin/manager  # Test locally if possible

# 5. Build and push Docker image
make docker-build
make docker-push

# 6. Deploy to cluster
make deploy-dev
```

---

## 3. Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User                                 │
│                    (kubectl/API)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Kubernetes API Server                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              KServe Controller Manager                       │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ InferenceService│  │ ServingRuntime│  │ TrainedModel   │  │
│  │  Controller  │  │  Controller   │  │  Controller     │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           Kubernetes Resources Created                       │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Knative      │  │ Deployments  │  │ Services        │  │
│  │ Services     │  │ (Raw mode)   │  │                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Model Pods                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Init Container: Storage Initializer                 │    │
│  │ (Downloads model from S3/GCS/etc.)                  │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Main Container: Model Server                        │    │
│  │ (TensorFlow, PyTorch, Scikit-learn, etc.)          │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Key Concepts

#### 1. InferenceService (ISVC)
The main CRD that users create to deploy models.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: my-model
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: "gs://bucket/model"
```

#### 2. ServingRuntime
Defines how to run specific model types.

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: sklearn-runtime
spec:
  supportedModelFormats:
    - name: sklearn
      version: "1"
  containers:
    - name: kserve-container
      image: kserve/sklearnserver:latest
```

#### 3. Components
An InferenceService can have:
- **Predictor**: Main model (required)
- **Transformer**: Pre/post-processing (optional)
- **Explainer**: Model explanations (optional)

#### 4. Deployment Modes
- **Serverless**: Uses Knative (auto-scaling, scale-to-zero)
- **RawDeployment**: Uses standard K8s Deployments (simpler, no scale-to-zero)

---

## 4. Deep Dive: InferenceService Status Management

### Overview

Status management is how KServe tracks and reports the health of your ML model deployments.

**File**: `pkg/apis/serving/v1beta1/inference_service_status.go`

### Data Structure

```go
// InferenceServiceStatus defines the observed state of InferenceService
type InferenceServiceStatus struct {
    // Embedded Status with Conditions
    duckv1.Status `json:",inline"`

    // Addressable endpoint for the InferenceService
    Address *duckv1.Addressable `json:"address,omitempty"`

    // URL holds the url that will distribute traffic
    URL *apis.URL `json:"url,omitempty"`

    // Statuses for the components (predictor, transformer, explainer)
    Components map[ComponentType]ComponentStatusSpec `json:"components,omitempty"`

    // Model related statuses
    ModelStatus ModelStatus `json:"modelStatus,omitempty"`

    // InferenceService DeploymentMode
    DeploymentMode string `json:"deploymentMode,omitempty"`
}
```

### Component Status

```go
type ComponentStatusSpec struct {
    // Latest revision name that is in ready state
    LatestReadyRevision string `json:"latestReadyRevision,omitempty"`

    // Latest revision name that is created
    LatestCreatedRevision string `json:"latestCreatedRevision,omitempty"`

    // Previous revision name that is rolled out with 100 percent traffic
    PreviousRolledoutRevision string `json:"previousRolledoutRevision,omitempty"`

    // Latest revision name that is rolled out with 100 percent traffic
    LatestRolledoutRevision string `json:"latestRolledoutRevision,omitempty"`

    // Traffic distribution
    Traffic []knservingv1.TrafficTarget `json:"traffic,omitempty"`

    // URLs
    URL     *apis.URL `json:"url,omitempty"`
    RestURL *apis.URL `json:"restUrl,omitempty"`
    GrpcURL *apis.URL `json:"grpcUrl,omitempty"`

    // Addressable endpoint
    Address *duckv1.Addressable `json:"address,omitempty"`
}
```

### Model Status (The Cool Part!)

```go
type ModelStatus struct {
    // Whether the available predictor endpoints reflect the current Spec
    // Values: UpToDate, InProgress, BlockedByFailedLoad, InvalidSpec
    TransitionStatus TransitionStatus `json:"transitionStatus"`

    // State information of the predictor's model
    ModelRevisionStates *ModelRevisionStates `json:"states,omitempty"`

    // Details of last failure
    LastFailureInfo *FailureInfo `json:"lastFailureInfo,omitempty"`

    // Model copy information
    ModelCopies *ModelCopies `json:"copies,omitempty"`
}

type ModelRevisionStates struct {
    // High level state: Pending, Standby, Loading, Loaded, FailedToLoad
    ActiveModelState ModelState `json:"activeModelState"`
    TargetModelState ModelState `json:"targetModelState,omitempty"`
}

type FailureInfo struct {
    Location          string        `json:"location,omitempty"`
    Reason            FailureReason `json:"reason,omitempty"`
    Message           string        `json:"message,omitempty"`
    ModelRevisionName string        `json:"modelRevisionName,omitempty"`
    Time              *metav1.Time  `json:"time,omitempty"`
    ExitCode          int32         `json:"exitCode,omitempty"`
}
```

### Conditions (Kubernetes Pattern)

KServe uses Kubernetes Conditions to report status:

```go
const (
    // Component-level conditions
    PredictorReady              apis.ConditionType = "PredictorReady"
    TransformerReady            apis.ConditionType = "TransformerReady"
    ExplainerReady              apis.ConditionType = "ExplainerReady"

    // Route conditions
    PredictorRouteReady         apis.ConditionType = "PredictorRouteReady"
    TransformerRouteReady       apis.ConditionType = "TransformerRouteReady"
    ExplainerRoutesReady        apis.ConditionType = "ExplainerRoutesReady"

    // Configuration conditions
    PredictorConfigurationReady apis.ConditionType = "PredictorConfigurationReady"
    TransformerConfigurationReady apis.ConditionType = "TransformerConfigurationReady"
    ExplainerConfigurationReady apis.ConditionType = "ExplainerConfigurationReady"

    // Aggregate conditions
    IngressReady              apis.ConditionType = "IngressReady"
    RoutesReady               apis.ConditionType = "RoutesReady"
    LatestDeploymentReady     apis.ConditionType = "LatestDeploymentReady"

    // Special states
    Stopped                   apis.ConditionType = "Stopped"
)
```

Each condition has:
- **Type**: What we're checking (e.g., PredictorReady)
- **Status**: True, False, or Unknown
- **Reason**: Machine-readable reason (e.g., "MinimumReplicasAvailable")
- **Message**: Human-readable details (e.g., "Deployment has minimum availability")

### Status Propagation Flow

```
1. User creates InferenceService
        ↓
2. Controller creates Kubernetes resources (Service/Deployment)
        ↓
3. Kubernetes resources report their status
        ↓
4. Controller observes resource status
        ↓
5. Controller calls propagation methods:
   - PropagateStatus() for serverless
   - PropagateRawStatus() for raw deployments
   - PropagateModelStatus() for detailed model state
        ↓
6. Status aggregation:
   - PropagateCrossComponentStatus()
        ↓
7. Update InferenceService status in API server
        ↓
8. User sees status via kubectl/API
```

### Detailed Status Methods

#### PropagateStatus (Serverless Mode)

**File**: `pkg/apis/serving/v1beta1/inference_service_status.go:448-517`

```go
func (ss *InferenceServiceStatus) PropagateStatus(
    component ComponentType,
    serviceStatus *knservingv1.ServiceStatus,
) {
    // 1. Initialize components map if needed
    if len(ss.Components) == 0 {
        ss.Components = make(map[ComponentType]ComponentStatusSpec)
    }

    // 2. Get or create component status
    statusSpec, ok := ss.Components[component]
    if !ok {
        ss.Components[component] = ComponentStatusSpec{}
    }

    // 3. Update revision tracking
    statusSpec.LatestCreatedRevision = serviceStatus.LatestCreatedRevisionName

    // 4. Track traffic routing for canary deployments
    for _, traffic := range serviceStatus.Traffic {
        if traffic.RevisionName == serviceStatus.LatestReadyRevisionName &&
           traffic.LatestRevision != nil && *traffic.LatestRevision {
            if traffic.Percent != nil && *traffic.Percent == 100 {
                // Track full rollout
                statusSpec.PreviousRolledoutRevision = statusSpec.LatestRolledoutRevision
                statusSpec.LatestRolledoutRevision = serviceStatus.LatestReadyRevisionName
            }
        }
    }

    // 5. Update ready revision
    if serviceStatus.LatestReadyRevisionName != statusSpec.LatestReadyRevision {
        statusSpec.LatestReadyRevision = serviceStatus.LatestReadyRevisionName
    }

    // 6. Copy URL/Address when ready
    readyCondition := serviceStatus.GetCondition(knservingv1.ServiceConditionReady)
    if readyCondition != nil && readyCondition.Status == corev1.ConditionTrue {
        if serviceStatus.Address != nil {
            statusSpec.Address = serviceStatus.Address
        }
        if serviceStatus.URL != nil {
            statusSpec.URL = serviceStatus.URL
        }
    }

    // 7. Propagate component ready condition
    readyConditionType := readyConditionsMap[component]
    ss.SetCondition(readyConditionType, readyCondition)

    // 8. Propagate route condition
    routeCondition := serviceStatus.GetCondition("RoutesReady")
    routeConditionType := routeConditionsMap[component]
    ss.SetCondition(routeConditionType, routeCondition)

    // 9. Propagate configuration condition
    configurationCondition := serviceStatus.GetCondition("ConfigurationsReady")
    configurationConditionType := configurationConditionsMap[component]
    ss.SetCondition(configurationConditionType, configurationCondition)

    // 10. Copy traffic status
    statusSpec.Traffic = serviceStatus.Traffic

    // 11. Save component status
    ss.Components[component] = statusSpec
    ss.ObservedGeneration = serviceStatus.ObservedGeneration
}
```

#### PropagateRawStatus (Raw Deployment Mode)

**File**: `pkg/apis/serving/v1beta1/inference_service_status.go:337-361`

```go
func (ss *InferenceServiceStatus) PropagateRawStatus(
    component ComponentType,
    deploymentList []*appsv1.Deployment,
    url *apis.URL,
) {
    // 1. Initialize components
    if len(ss.Components) == 0 {
        ss.Components = make(map[ComponentType]ComponentStatusSpec)
    }

    // 2. Get component status
    statusSpec, ok := ss.Components[component]
    if !ok {
        ss.Components[component] = ComponentStatusSpec{}
    }

    // 3. Extract deployment condition
    condition := getDeploymentCondition(deploymentList, appsv1.DeploymentAvailable)

    // 4. Set component ready based on deployment availability
    readyCondition := readyConditionsMap[component]
    ss.SetCondition(readyCondition, condition)

    // 5. Save status
    ss.Components[component] = statusSpec
    ss.ObservedGeneration = deploymentList[0].Status.ObservedGeneration
}
```

#### PropagateModelStatus (Model Loading Details)

**File**: `pkg/apis/serving/v1beta1/inference_service_status.go:590-682`

This is the most complex method - it inspects pod status to determine model loading state.

```go
func (ss *InferenceServiceStatus) PropagateModelStatus(
    statusSpec ComponentStatusSpec,
    podList *corev1.PodList,
    rawDeployment bool,
    serviceStatus *knservingv1.ServiceStatus,
) bool {
    totalCopies := len(podList.Items)

    // Case 1: No pods
    if totalCopies == 0 {
        if !rawDeployment {
            // Check if scaled to 0 due to error
            for _, knativeCond := range serviceStatus.Conditions {
                if knativeCond.Status == "False" {
                    ss.UpdateModelRevisionStates(FailedToLoad, totalCopies, nil)
                    return true
                }
            }
        }
        // Otherwise, just pending
        ss.UpdateModelRevisionStates(Pending, totalCopies, nil)
        return true
    }

    // Case 2: Check storage initializer (init container)
    for _, cs := range podList.Items[0].Status.InitContainerStatuses {
        if cs.Name == constants.StorageInitializerContainerName {
            switch {
            case cs.State.Running != nil:
                // Model is downloading
                if cs.LastTerminationState.Terminated != nil {
                    // Was previously terminated - requeue to check again
                    return false
                }
                ss.UpdateModelRevisionStates(Loading, totalCopies, nil)
                return true

            case cs.State.Terminated != nil &&
                 cs.State.Terminated.Reason == constants.StateReasonError:
                // Download failed
                ss.UpdateModelRevisionStates(FailedToLoad, totalCopies, &FailureInfo{
                    Reason:   ModelLoadFailed,
                    Message:  cs.State.Terminated.Message,
                    ExitCode: cs.State.Terminated.ExitCode,
                })
                return true

            case cs.State.Waiting != nil &&
                 cs.State.Waiting.Reason == constants.StateReasonCrashLoopBackOff:
                // Init container keeps crashing
                ss.UpdateModelRevisionStates(FailedToLoad, totalCopies, &FailureInfo{
                    Reason:   ModelLoadFailed,
                    Message:  cs.LastTerminationState.Terminated.Message,
                    ExitCode: cs.LastTerminationState.Terminated.ExitCode,
                })
                return true
            }
        }
    }

    // Case 3: Service is ready
    if ss.IsReady() {
        if rawDeployment {
            ss.UpdateModelRevisionStates(Loaded, totalCopies, nil)
            return true
        } else if statusSpec.LatestCreatedRevision == statusSpec.LatestReadyRevision {
            // For serverless, ensure revisions match
            ss.UpdateModelRevisionStates(Loaded, totalCopies, nil)
            return true
        }
    }

    // Case 4: Check kserve container status
    for _, cs := range podList.Items[0].Status.ContainerStatuses {
        if cs.Name == constants.InferenceServiceContainerName {
            switch {
            case cs.State.Terminated != nil &&
                 cs.State.Terminated.Reason == constants.StateReasonError:
                // Container failed
                ss.UpdateModelRevisionStates(FailedToLoad, totalCopies, &FailureInfo{
                    Reason:   ModelLoadFailed,
                    Message:  cs.State.Terminated.Message,
                    ExitCode: cs.State.Terminated.ExitCode,
                })

            case cs.State.Waiting != nil &&
                 cs.State.Waiting.Reason == constants.StateReasonCrashLoopBackOff:
                // Container keeps crashing
                ss.UpdateModelRevisionStates(FailedToLoad, totalCopies, &FailureInfo{
                    Reason:   ModelLoadFailed,
                    Message:  cs.LastTerminationState.Terminated.Message,
                    ExitCode: cs.LastTerminationState.Terminated.ExitCode,
                })

            default:
                // Still pending
                ss.UpdateModelRevisionStates(Pending, totalCopies, nil)
            }
        }
    }

    return true
}
```

### Real-World Example: Model Deployment Lifecycle

Let's trace what happens when you deploy a model:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sklearn-iris
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: "gs://kfserving-examples/models/sklearn/iris"
```

**Timeline:**

```
T=0s: User applies YAML
├─ InferenceService created
├─ Status initialized
│  ├─ Conditions: Ready=Unknown, PredictorReady=Unknown
│  └─ ModelStatus: TransitionStatus=InProgress, ActiveModelState=Pending

T=2s: Controller reconciles
├─ Finds matching ServingRuntime (sklearn)
├─ Creates Knative Service (or Deployment)
├─ Status: PredictorConfigurationReady=Unknown

T=5s: Pod created
├─ Storage initializer starts downloading model
├─ PropagateModelStatus() called
│  └─ Sees init container running
├─ Status Update:
│  ├─ ModelState: Loading
│  └─ TransitionStatus: InProgress

T=10s: Model downloaded successfully
├─ Storage init container completes
├─ Kserve container starts
├─ PropagateModelStatus() called
│  └─ Sees main container starting
├─ Status: ModelState still Loading

T=15s: Container ready!
├─ Health checks pass
├─ PropagateStatus() called
│  └─ Sees Service Ready=True
├─ PropagateModelStatus() called
│  └─ Sees IsReady()=true
├─ Status Update:
│  ├─ PredictorReady: True
│  ├─ PredictorRouteReady: True
│  ├─ PredictorConfigurationReady: True
│  ├─ RoutesReady: True (aggregated)
│  ├─ LatestDeploymentReady: True (aggregated)
│  ├─ Ready: True (overall)
│  ├─ ModelState: Loaded
│  ├─ TransitionStatus: UpToDate
│  ├─ URL: http://sklearn-iris.default.example.com
│  └─ ModelCopies: TotalCopies=1

✅ READY TO SERVE PREDICTIONS!
```

**What the user sees:**

```bash
$ kubectl get isvc sklearn-iris
NAME           URL                                      READY   PREV   LATEST   AGE
sklearn-iris   http://sklearn-iris.default.example.com  True    100           30s

$ kubectl get isvc sklearn-iris -o yaml
status:
  conditions:
  - type: Ready
    status: "True"
  - type: PredictorReady
    status: "True"
  url: http://sklearn-iris.default.example.com
  modelStatus:
    transitionStatus: UpToDate
    states:
      activeModelState: Loaded
      targetModelState: Loaded
    copies:
      totalCopies: 1
```

**If model download fails:**

```
T=5s: Storage initializer starts
T=8s: Download fails (404 Not Found)
├─ Init container terminates with error
├─ PropagateModelStatus() called
│  └─ Detects: cs.State.Terminated.Reason == "Error"
├─ Status Update:
│  ├─ ModelState: FailedToLoad
│  ├─ TransitionStatus: BlockedByFailedLoad
│  └─ LastFailureInfo:
│     ├─ Reason: ModelLoadFailed
│     ├─ Message: "Failed to download model: 404 Not Found"
│     ├─ ExitCode: 1
│     └─ Time: 2024-01-15T08:23:45Z
```

```bash
$ kubectl get isvc sklearn-iris
NAME           URL   READY   PREV   LATEST   AGE
sklearn-iris         False                   15s

$ kubectl get isvc sklearn-iris -o yaml
status:
  conditions:
  - type: Ready
    status: "False"
    reason: ModelLoadFailed
    message: "Failed to download model: 404 Not Found"
  modelStatus:
    transitionStatus: BlockedByFailedLoad
    states:
      activeModelState: FailedToLoad
      targetModelState: FailedToLoad
    lastFailureInfo:
      reason: ModelLoadFailed
      message: "Failed to download model: 404 Not Found"
      exitCode: 1
      time: "2024-01-15T08:23:45Z"
```

---

## 5. Controller Reconciliation Loop

Controllers are the heart of Kubernetes operators. They watch resources and drive the system towards desired state.

**File**: `pkg/controller/v1beta1/inferenceservice/controller.go`

### The Reconciliation Pattern

```go
// Reconcile is the main loop
func (r *InferenceServiceReconciler) Reconcile(
    ctx context.Context,
    req ctrl.Request,
) (ctrl.Result, error) {
    // 1. Fetch the InferenceService
    isvc := &v1beta1.InferenceService{}
    if err := r.Get(ctx, req.NamespacedName, isvc); err != nil {
        if errors.IsNotFound(err) {
            // Resource deleted, nothing to do
            return ctrl.Result{}, nil
        }
        return ctrl.Result{}, err
    }

    // 2. Handle deletion (check for finalizers)
    if !isvc.ObjectMeta.DeletionTimestamp.IsZero() {
        return r.reconcileDelete(ctx, isvc)
    }

    // 3. Initialize status if needed
    if len(isvc.Status.Conditions) == 0 {
        isvc.Status.InitializeConditions()
        if err := r.Status().Update(ctx, isvc); err != nil {
            return ctrl.Result{}, err
        }
    }

    // 4. Reconcile each component
    // Predictor (required)
    if result, err := r.reconcilePredictor(ctx, isvc); err != nil {
        return result, err
    }

    // Transformer (optional)
    if isvc.Spec.Transformer != nil {
        if result, err := r.reconcileTransformer(ctx, isvc); err != nil {
            return result, err
        }
    }

    // Explainer (optional)
    if isvc.Spec.Explainer != nil {
        if result, err := r.reconcileExplainer(ctx, isvc); err != nil {
            return result, err
        }
    }

    // 5. Reconcile ingress/routing
    if result, err := r.reconcileIngress(ctx, isvc); err != nil {
        return result, err
    }

    // 6. Update status
    if err := r.Status().Update(ctx, isvc); err != nil {
        return ctrl.Result{}, err
    }

    // 7. Return result
    // Requeue if needed, or done
    return ctrl.Result{}, nil
}
```

### Predictor Reconciliation

**File**: `pkg/controller/v1beta1/inferenceservice/components/predictor.go:85`

```go
func (p *Predictor) Reconcile(
    ctx context.Context,
    isvc *v1beta1.InferenceService,
) (ctrl.Result, error) {
    // 1. Find matching ServingRuntime
    runtime, err := p.reconcileModel(ctx, isvc, multiNodeEnabled)
    if err != nil {
        // Update status with error
        isvc.Status.UpdateModelTransitionStatus(v1beta1.InvalidSpec, &v1beta1.FailureInfo{
            Reason: v1beta1.NoSupportingRuntime,
            Message: err.Error(),
        })
        return ctrl.Result{}, err
    }

    // 2. Build PodSpec from runtime
    podSpec, err := p.buildPodSpec(isvc, runtime)
    if err != nil {
        return ctrl.Result{}, err
    }

    // 3. Choose deployment mode (Serverless or Raw)
    if p.deploymentMode == constants.Serverless {
        // Create/Update Knative Service
        result, err := p.reconcileKnativeService(ctx, isvc, podSpec)
        if err != nil {
            return result, err
        }
    } else {
        // Create/Update Deployment + Service
        result, err := p.reconcileRawDeployment(ctx, isvc, podSpec)
        if err != nil {
            return result, err
        }
    }

    // 4. Get pods for status
    podList, err := p.getPods(ctx, isvc)
    if err != nil {
        return ctrl.Result{}, err
    }

    // 5. Update status
    if p.deploymentMode == constants.Serverless {
        // Get Knative Service status
        ksvc := &knservingv1.Service{}
        err := p.client.Get(ctx, types.NamespacedName{
            Name: predictorName,
            Namespace: isvc.Namespace,
        }, ksvc)

        // Propagate Knative status
        isvc.Status.PropagateStatus(v1beta1.PredictorComponent, &ksvc.Status)

        // Propagate model status
        statusSpec := isvc.Status.Components[v1beta1.PredictorComponent]
        isvc.Status.PropagateModelStatus(statusSpec, podList, false, &ksvc.Status)
    } else {
        // Get Deployment status
        deployments, err := p.getDeployments(ctx, isvc)

        // Propagate raw deployment status
        isvc.Status.PropagateRawStatus(v1beta1.PredictorComponent, deployments, url)

        // Propagate model status
        statusSpec := isvc.Status.Components[v1beta1.PredictorComponent]
        isvc.Status.PropagateModelStatus(statusSpec, podList, true, nil)
    }

    return ctrl.Result{}, nil
}
```

### Watch and Event Handling

Controllers use "watches" to be notified of changes:

```go
func (r *InferenceServiceReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        // Watch InferenceService changes
        For(&v1beta1.InferenceService{}).
        // Watch owned Knative Services
        Owns(&knservingv1.Service{}).
        // Watch owned Deployments
        Owns(&appsv1.Deployment{}).
        // Watch owned Services
        Owns(&corev1.Service{}).
        Complete(r)
}
```

**How it works:**

```
User creates/updates InferenceService
        ↓
Kubernetes API Server notifies controller
        ↓
Controller adds request to work queue
        ↓
Worker goroutine picks up request
        ↓
Reconcile() function called
        ↓
Creates/updates child resources
        ↓
Kubernetes creates actual pods/services
        ↓
Child resources change (pods become ready)
        ↓
Controller notified via "Owns" watches
        ↓
Reconcile() called again
        ↓
Updates InferenceService status
        ↓
Process repeats until desired state = actual state
```

### Key Controller Patterns

1. **Idempotency**: Reconcile can be called multiple times with same input - must produce same result
2. **Status vs Spec**:
   - Spec = what user wants (desired state)
   - Status = what exists (actual state)
   - Controller drives actual → desired
3. **Requeue**: Return `ctrl.Result{Requeue: true}` or `ctrl.Result{RequeueAfter: 30*time.Second}` to reconcile again
4. **Ownership**: Use `controllerutil.SetControllerReference()` so child resources are deleted with parent
5. **Finalizers**: Clean up external resources before deletion

---

## 6. How to Add a New Status Field

Let's add a practical example: tracking the **last time the model was updated**.

### Step 1: Add Field to Status Struct

**File**: `pkg/apis/serving/v1beta1/inference_service_status.go`

```go
type ModelStatus struct {
    TransitionStatus    TransitionStatus     `json:"transitionStatus"`
    ModelRevisionStates *ModelRevisionStates `json:"states,omitempty"`
    LastFailureInfo     *FailureInfo         `json:"lastFailureInfo,omitempty"`
    ModelCopies         *ModelCopies         `json:"copies,omitempty"`

    // NEW FIELD: Track when model was last successfully loaded
    LastLoadedTime      *metav1.Time         `json:"lastLoadedTime,omitempty"`
}
```

### Step 2: Update the Propagation Logic

```go
func (ss *InferenceServiceStatus) UpdateModelRevisionStates(
    modelState ModelState,
    totalCopies int,
    info *FailureInfo,
) {
    if ss.ModelStatus.ModelRevisionStates == nil {
        ss.ModelStatus.ModelRevisionStates = &ModelRevisionStates{
            ActiveModelState: modelState,
            TargetModelState: modelState,
        }
    } else {
        ss.ModelStatus.ModelRevisionStates.TargetModelState = modelState
    }

    switch modelState {
    case Pending, Loading:
        ss.ModelStatus.TransitionStatus = InProgress

    case Loaded:
        ss.ModelStatus.TransitionStatus = UpToDate
        ss.ModelStatus.ModelCopies = &ModelCopies{TotalCopies: totalCopies}
        ss.ModelStatus.ModelRevisionStates.ActiveModelState = Loaded

        // NEW: Set last loaded time
        now := metav1.Now()
        ss.ModelStatus.LastLoadedTime = &now

    case FailedToLoad:
        ss.ModelStatus.TransitionStatus = BlockedByFailedLoad
    }

    if info != nil {
        ss.SetModelFailureInfo(info)
    }
}
```

### Step 3: Add Tests

**File**: `pkg/apis/serving/v1beta1/inference_service_status_test.go`

```go
func TestModelStatus_LastLoadedTime(t *testing.T) {
    g := gomega.NewGomegaWithT(t)

    isvcStatus := &InferenceServiceStatus{
        Status: duckv1.Status{
            Conditions: duckv1.Conditions{
                {Type: "Ready", Status: corev1.ConditionTrue},
            },
        },
        ModelStatus: ModelStatus{},
    }

    // Initially, LastLoadedTime should be nil
    g.Expect(isvcStatus.ModelStatus.LastLoadedTime).To(gomega.BeNil())

    // Update to Loaded state
    isvcStatus.UpdateModelRevisionStates(Loaded, 1, nil)

    // LastLoadedTime should now be set
    g.Expect(isvcStatus.ModelStatus.LastLoadedTime).NotTo(gomega.BeNil())

    // Should be recent (within last 5 seconds)
    now := metav1.Now()
    timeDiff := now.Time.Sub(isvcStatus.ModelStatus.LastLoadedTime.Time)
    g.Expect(timeDiff.Seconds()).To(gomega.BeNumerically("<", 5))
}
```

### Step 4: Generate CRD Manifests

```bash
# This regenerates the CRD YAML from Go structs
make manifests

# This updates:
# - config/crd/full/serving.kserve.io_inferenceservices.yaml
# - OpenAPI schemas
# - Generated code
```

### Step 5: Run Tests

```bash
# Run all tests
make test

# Run specific test
go test -v ./pkg/apis/serving/v1beta1 -run TestModelStatus_LastLoadedTime
```

### Step 6: Verify the Change

```bash
# Apply the new CRD
kubectl apply -f config/crd/full/serving.kserve.io_inferenceservices.yaml

# Create a test InferenceService
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: test-model
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: "gs://kfserving-examples/models/sklearn/iris"
EOF

# Wait for it to be ready
kubectl wait --for=condition=Ready isvc/test-model --timeout=300s

# Check the new field
kubectl get isvc test-model -o jsonpath='{.status.modelStatus.lastLoadedTime}'
# Should output something like: 2024-01-15T10:23:45Z
```

### Complete Example: Adding Model Size Tracking

Let's add another useful field - tracking the model size:

```go
// 1. Add to ModelStatus struct
type ModelStatus struct {
    // ... existing fields ...

    // Size of the model in bytes (from storage initializer)
    ModelSizeBytes *int64 `json:"modelSizeBytes,omitempty"`
}

// 2. Update storage initializer to report size
// File: python/kserve/kserve/storage/storage.py
def download_model(storage_uri: str) -> int:
    """Download model and return size in bytes"""
    size = 0
    # ... download logic ...
    return size

// 3. Pass size through annotation
annotations[constants.ModelSizeBytesAnnotation] = str(model_size)

// 4. Read in controller
// File: pkg/controller/v1beta1/inferenceservice/components/predictor.go
if sizeStr, ok := pod.Annotations[constants.ModelSizeBytesAnnotation]; ok {
    if size, err := strconv.ParseInt(sizeStr, 10, 64); err == nil {
        isvc.Status.ModelStatus.ModelSizeBytes = &size
    }
}

// 5. Add test
func TestModelStatus_ModelSize(t *testing.T) {
    // ... test that model size is correctly propagated ...
}

// 6. Generate and test
make manifests
make test
```

---

## 7. Testing Guide

### Running Tests

```bash
# Run all tests
make test

# Run tests for specific package
go test ./pkg/apis/serving/v1beta1/...

# Run with verbose output
go test -v ./pkg/apis/serving/v1beta1/...

# Run specific test
go test -v ./pkg/apis/serving/v1beta1 -run TestPropagateModelStatus

# Run with coverage
go test -cover ./pkg/apis/serving/v1beta1/...

# Generate coverage report
go test -coverprofile=coverage.out ./pkg/...
go tool cover -html=coverage.out
```

### Writing Tests

KServe uses:
- **Standard Go testing**: `testing` package
- **Gomega**: Assertion library (more readable than standard assertions)
- **Table-driven tests**: Common pattern for testing multiple scenarios

**Example test structure:**

```go
func TestInferenceServiceStatus_PropagateModelStatus(t *testing.T) {
    g := gomega.NewGomegaWithT(t)

    scenarios := map[string]struct {
        // Input
        isvcStatus    *InferenceServiceStatus
        statusSpec    ComponentStatusSpec
        podList       *corev1.PodList
        rawDeployment bool
        serviceStatus *knservingv1.ServiceStatus

        // Expected output
        expectedRevisionStates   *ModelRevisionStates
        expectedTransitionStatus TransitionStatus
        expectedFailureInfo      *FailureInfo
        expectedReturnValue      bool
    }{
        "pod list is empty": {
            isvcStatus: &InferenceServiceStatus{ /* ... */ },
            podList: &corev1.PodList{Items: []corev1.Pod{}},
            expectedRevisionStates: &ModelRevisionStates{
                ActiveModelState: Pending,
                TargetModelState: Pending,
            },
            expectedTransitionStatus: InProgress,
            expectedReturnValue: true,
        },
        "storage initializer in running state": {
            // ... test setup ...
        },
        // ... more scenarios ...
    }

    for name, scenario := range scenarios {
        t.Run(name, func(t *testing.T) {
            // Execute
            result := scenario.isvcStatus.PropagateModelStatus(
                scenario.statusSpec,
                scenario.podList,
                scenario.rawDeployment,
                scenario.serviceStatus,
            )

            // Assert
            g.Expect(result).To(gomega.Equal(scenario.expectedReturnValue))
            g.Expect(scenario.isvcStatus.ModelStatus.ModelRevisionStates).
                To(gomega.Equal(scenario.expectedRevisionStates))
            g.Expect(scenario.isvcStatus.ModelStatus.TransitionStatus).
                To(gomega.Equal(scenario.expectedTransitionStatus))
            g.Expect(scenario.isvcStatus.ModelStatus.LastFailureInfo).
                To(gomega.Equal(scenario.expectedFailureInfo))
        })
    }
}
```

### Integration Tests

Integration tests run against a real (or fake) Kubernetes cluster:

```bash
# These are in test/e2e/
make test-e2e
```

### Unit Test Best Practices

1. **Test each state transition**
   - Pending → Loading → Loaded
   - Pending → FailedToLoad
   - Loading → FailedToLoad

2. **Test edge cases**
   - Empty pod list
   - Missing containers
   - Nil values

3. **Test error conditions**
   - CrashLoopBackOff
   - ImagePullBackOff
   - Storage errors

4. **Use meaningful test names**
   ```go
   "storage initializer failed due to crash loopBackOff"  // Good
   "test1"  // Bad
   ```

5. **Keep tests independent**
   - Don't rely on test execution order
   - Reset state between tests

---

## 8. Common Development Tasks

### Task 1: Adding a New Condition Type

```go
// 1. Define the condition
const (
    ModelCacheReady apis.ConditionType = "ModelCacheReady"
)

// 2. Add to condition set (if it's a top-level condition)
var conditionSet = apis.NewLivingConditionSet(
    PredictorReady,
    IngressReady,
    ModelCacheReady,  // NEW
)

// 3. Set the condition in controller
isvc.Status.SetCondition(ModelCacheReady, &apis.Condition{
    Type:   ModelCacheReady,
    Status: corev1.ConditionTrue,
    Reason: "CachePopulated",
    Message: "Model cache has been populated successfully",
})

// 4. Add test
func TestModelCacheReady(t *testing.T) {
    status := &InferenceServiceStatus{}
    status.InitializeConditions()

    status.SetCondition(ModelCacheReady, &apis.Condition{
        Status: corev1.ConditionTrue,
    })

    g.Expect(status.IsConditionReady(ModelCacheReady)).To(gomega.BeTrue())
}
```

### Task 2: Debugging Controller Issues

```bash
# 1. Check controller logs
kubectl logs -n kserve -l control-plane=kserve-controller-manager -f

# 2. Increase log verbosity
# Edit deployment and add: --zap-log-level=debug

# 3. Check InferenceService status
kubectl get isvc -A
kubectl describe isvc <name>

# 4. Check underlying resources
kubectl get ksvc -A  # Knative services
kubectl get deployment -A
kubectl get pods -A

# 5. Check events
kubectl get events --sort-by='.lastTimestamp'
```

### Task 3: Local Controller Development

```bash
# 1. Build the controller
make manager

# 2. Set up environment variables
export KUBECONFIG=~/.kube/config

# 3. Run locally (instead of in cluster)
./bin/manager \
  --metrics-bind-address=:8080 \
  --health-probe-bind-address=:8081

# Now the controller runs locally but manages cluster resources
# Great for debugging with breakpoints!
```

### Task 4: Adding Python Model Server Support

```go
// 1. Create serving runtime
// config/runtimes/kserve-myserver.yaml
apiVersion: serving.kserve.io/v1alpha1
kind: ClusterServingRuntime
metadata:
  name: myserver
spec:
  supportedModelFormats:
    - name: myformat
      version: "1"
      autoSelect: true
  containers:
    - name: kserve-container
      image: myorg/myserver:latest
      args:
        - --model_name={{.Name}}
        - --model_dir=/mnt/models
```

```python
# 2. Create Python server
# python/myserver/model.py
from kserve import Model, ModelServer

class MyModel(Model):
    def __init__(self, name: str):
        super().__init__(name)
        self.model = None

    def load(self):
        # Load your model
        self.model = load_my_model()

    def predict(self, request):
        # Make predictions
        return self.model.predict(request)

if __name__ == "__main__":
    model = MyModel("mymodel")
    ModelServer().start([model])
```

```dockerfile
# 3. Create Dockerfile
# python/myserver.Dockerfile
FROM python:3.11-slim
COPY myserver /app/myserver
RUN pip install kserve
ENTRYPOINT ["python", "-m", "myserver.model"]
```

```bash
# 4. Build and test
cd python
docker build -t myorg/myserver:latest -f myserver.Dockerfile .
docker push myorg/myserver:latest

# 5. Deploy serving runtime
kubectl apply -f config/runtimes/kserve-myserver.yaml

# 6. Test with InferenceService
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: test-my-model
spec:
  predictor:
    model:
      modelFormat:
        name: myformat
      storageUri: "s3://bucket/mymodel"
EOF
```

---

## 9. Troubleshooting

### Common Issues and Solutions

#### Issue 1: Tests Failing

```bash
# Error: undefined: apis.ConditionType
# Solution: Missing import
import (
    "knative.dev/pkg/apis"
)

# Error: cannot use X (type Y) as type Z
# Solution: Check struct definitions, ensure fields match

# Error: timeout waiting for condition
# Solution: Check if test setup creates required resources
```

#### Issue 2: CRD Not Updating

```bash
# Problem: Made changes to Go structs but CRD YAML not updated
# Solution:
make manifests  # Regenerates CRDs from Go code
kubectl apply -f config/crd/full/serving.kserve.io_inferenceservices.yaml

# Problem: CRD too large (>1MB)
# Solution: KServe uses minimal CRDs in production
# See: hack/minimal-crdgen.sh
```

#### Issue 3: Controller Not Reconciling

```bash
# Check controller is running
kubectl get pods -n kserve

# Check RBAC permissions
kubectl auth can-i list inferenceservices --as=system:serviceaccount:kserve:kserve-controller-manager

# Check controller logs for errors
kubectl logs -n kserve -l control-plane=kserve-controller-manager --tail=100

# Enable debug logging
kubectl set env deployment/kserve-controller-manager -n kserve LOG_LEVEL=debug
```

#### Issue 4: Model Not Loading

```bash
# 1. Check InferenceService status
kubectl get isvc mymodel -o yaml

# 2. Check pods
kubectl get pods -l serving.kserve.io/inferenceservice=mymodel

# 3. Check storage initializer logs
kubectl logs <pod-name> -c storage-initializer

# 4. Check kserve container logs
kubectl logs <pod-name> -c kserve-container

# 5. Common causes:
# - Wrong storageUri
# - Missing credentials (S3/GCS secrets)
# - Model format mismatch
# - Insufficient resources (CPU/memory/GPU)
```

---

## 10. Additional Resources

### Documentation

- **KServe Website**: https://kserve.github.io/website/
- **API Reference**: https://kserve.github.io/website/reference/api/
- **Developer Guide**: https://kserve.github.io/website/developer/developer/

### Code References

**Key Files:**
- Status definitions: `pkg/apis/serving/v1beta1/inference_service_status.go`
- Controller: `pkg/controller/v1beta1/inferenceservice/controller.go`
- Components: `pkg/controller/v1beta1/inferenceservice/components/`
- Constants: `pkg/constants/constants.go`

**Important Packages:**
- `k8s.io/apimachinery/pkg/apis/meta/v1`: Kubernetes types
- `knative.dev/pkg/apis`: Condition management
- `sigs.k8s.io/controller-runtime`: Controller framework

### Community

- **Slack**: https://github.com/kserve/community#slack
- **GitHub Issues**: https://github.com/kserve/kserve/issues
- **Community Meetings**: https://github.com/kserve/community#community-meetings

### Learning Path

**Beginner:**
1. Understand Kubernetes basics (Pods, Deployments, Services)
2. Learn about CRDs and controllers
3. Read KServe documentation
4. Run examples from `docs/samples/`
5. Read status management code (this guide)

**Intermediate:**
1. Understand Knative Serving basics
2. Study controller reconciliation loop
3. Add a simple status field (follow section 6)
4. Write tests for your changes
5. Review PRs on GitHub

**Advanced:**
1. Implement a new component type
2. Add support for a new model format
3. Optimize controller performance
4. Contribute to upstream KServe

### Quick Reference Commands

```bash
# Development
make fmt           # Format code
make vet          # Run go vet
make test         # Run tests
make precommit    # Run all pre-commit checks
make manager      # Build controller binary

# Building
make docker-build                    # Build controller image
make docker-build-sklearn           # Build sklearn server
make docker-build-huggingface       # Build HF server

# Deployment
make deploy                # Deploy to cluster (production mode)
make deploy-dev           # Deploy in development mode
make undeploy             # Remove from cluster

# Code Generation
make manifests            # Generate CRDs
make generate            # Generate deepcopy, clients, etc.

# Debugging
kubectl get isvc -A                           # List InferenceServices
kubectl describe isvc <name>                   # Detailed status
kubectl logs -n kserve -l control-plane=kserve-controller-manager -f
```

---

## Appendix: Status Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Creates InferenceService                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              InferenceService Controller Triggered               │
│                   (Reconcile loop starts)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Initialize Status Conditions                    │
│              isvc.Status.InitializeConditions()                  │
│  Conditions: Ready=Unknown, PredictorReady=Unknown               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Find/Create Serving Runtime                         │
│          (sklearn, pytorch, tensorflow, etc.)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           Create Kubernetes Resources                            │
│     ┌──────────────────┬──────────────────┐                    │
│     │  Serverless Mode │  Raw Mode        │                    │
│     │  (Knative)       │  (K8s Deployment)│                    │
│     │                  │                  │                    │
│     │  - Service       │  - Deployment    │                    │
│     │  - Route         │  - Service       │                    │
│     │  - Configuration │  - Ingress       │                    │
│     └──────────────────┴──────────────────┘                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Pod Created                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Init Container: storage-initializer              │          │
│  │ Status: Running                                  │          │
│  │ Action: Downloading model from storageUri        │          │
│  └──────────────────────────────────────────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            Controller Observes Pod Status                        │
│              PropagateModelStatus() called                       │
│                                                                  │
│  Check: cs.State.Running != nil                                 │
│  Result: ModelState = Loading                                   │
│          TransitionStatus = InProgress                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                     ┌───────┴────────┐
                     │                │
                     ▼                ▼
         ┌──────────────────┐  ┌──────────────────┐
         │  SUCCESS PATH    │  │   FAILURE PATH   │
         └──────────────────┘  └──────────────────┘
                     │                │
                     ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Model Downloaded Successfully   │   Model Download Failed      │
│  Init container exits 0          │   Init container exits 1     │
└────────────────┬─────────────────┴──────────────┬───────────────┘
                 │                                │
                 ▼                                ▼
┌─────────────────────────────────┐  ┌───────────────────────────┐
│  Main Container Starts          │  │  Status Updated           │
│  kserve-container               │  │  ModelState = FailedToLoad│
│  Loading model into memory      │  │  TransitionStatus =       │
│  Health checks starting         │  │    BlockedByFailedLoad    │
└────────────────┬────────────────┘  │  FailureInfo populated    │
                 │                    └───────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Container Ready                                     │
│  Health checks passing                                           │
│  PropagateStatus() called                                        │
│  PropagateModelStatus() called                                   │
│                                                                  │
│  Check: IsReady() == true                                       │
│  Result: ModelState = Loaded                                    │
│          TransitionStatus = UpToDate                             │
│          PredictorReady = True                                   │
│          URL = http://model.namespace.svc.cluster.local          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          Aggregate Cross-Component Status                        │
│        PropagateCrossComponentStatus() called                    │
│                                                                  │
│  For each component (predictor, transformer, explainer):        │
│    - Check RouteReady conditions                                │
│    - Check ConfigurationReady conditions                         │
│                                                                  │
│  Set aggregate conditions:                                       │
│    - RoutesReady = True (if all component routes ready)         │
│    - LatestDeploymentReady = True (if all configs ready)        │
│    - Ready = True (if predictor ready && ingress ready)         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           Update InferenceService Status in API                  │
│              r.Status().Update(ctx, isvc)                        │
│                                                                  │
│  Final Status:                                                   │
│    Ready: True                                                   │
│    URL: http://model.namespace.example.com                       │
│    ModelStatus:                                                  │
│      TransitionStatus: UpToDate                                  │
│      States:                                                     │
│        ActiveModelState: Loaded                                  │
│        TargetModelState: Loaded                                  │
│      ModelCopies:                                                │
│        TotalCopies: 1                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ✅ READY TO SERVE!                            │
│                                                                  │
│  Users can now send prediction requests:                        │
│  curl http://model.namespace.example.com/v1/models/model:predict│
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

This guide covered:

1. **Project Overview**: Understanding KServe's purpose and structure
2. **Development Setup**: Getting your environment ready
3. **Architecture**: How components fit together
4. **Status Management**: Deep dive into status tracking (the feature walkthrough)
5. **Controller Loop**: How reconciliation works
6. **Adding Features**: Step-by-step guide to adding status fields
7. **Testing**: How to write and run tests
8. **Common Tasks**: Practical development workflows
9. **Troubleshooting**: Solutions to common issues
10. **Resources**: Where to learn more

**Key Takeaways:**

- KServe uses Kubernetes controllers to manage ML model deployments
- Status is the "source of truth" for what's actually happening
- Conditions follow Kubernetes patterns for consistent status reporting
- Model status goes beyond just "ready/not ready" to show loading progress
- Tests are crucial - they document expected behavior
- The reconciliation loop continuously drives actual state → desired state

**Next Steps:**

1. Set up your development environment
2. Run the tests to see them pass
3. Try adding a simple status field (follow section 6)
4. Deploy an InferenceService and watch the status changes
5. Join the community Slack and say hi!

Good luck with your KServe development journey! 🚀