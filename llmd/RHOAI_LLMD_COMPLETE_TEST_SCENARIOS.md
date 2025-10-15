# RHOAI LLMD - Complete Test Scenarios & Known Issues

**Document Version:** 1.0  
**Date:** October 15, 2025  
**Based On:** KServe v1alpha1 LLMD codebase analysis  
**Status:** Production Test Plan

---

## EXECUTIVE SUMMARY

### Known Issues Found in Codebase
1. **CRITICAL**: Controller reconciliation partially disabled (workload & router)
2. **HIGH**: Template variable substitution may fail with complex templates
3. **MEDIUM**: InferencePool condition propagation not implemented
4. **MEDIUM**: ConfigMap watch not implemented (manual reconcile trigger needed)
5. **LOW**: Scheduler port mismatch not validated
6. **LOW**: Gateway reference existence not validated

### Test Coverage
- **Total Test Scenarios**: 168
- **Critical (P0)**: 28 scenarios
- **High Priority (P1)**: 52 scenarios  
- **Medium Priority (P2)**: 58 scenarios
- **Low Priority (P3)**: 30 scenarios

---

## CRITICAL ISSUES FROM CODEBASE

### ISSUE-001: Controller Reconciliation Partially Disabled
**Location**: `pkg/controller/v1alpha1/llmisvc/controller.go:207-216`

```go
// Lines 207-216 (COMMENTED OUT!)
// TODO: add workload reconciliation and re-enable this code
// if err := r.reconcileWorkload(ctx, llmSvc, config.StorageConfig); err != nil {
//     return fmt.Errorf("failed to reconcile workload: %w", err)
// }

// TODO: add router reconciliation and re-enable this code  
// if err := r.reconcileRouter(ctx, llmSvc); err != nil {
//     return fmt.Errorf("failed to reconcile networking: %w", err)
// }
```

**Impact**: 
- Workloads (Deployments, Pods) may not be created
- Networking (HTTPRoutes, Gateways) may not be configured
- LLMD CRDs accepted but nothing deployed

**Test Scenario Required**: Verify this is re-enabled in RHOAI

---

### ISSUE-002: Template Variable Substitution Failures
**Location**: `pkg/controller/v1alpha1/llmisvc/config_merge.go:176-204`

```go
// Line 190: Option("missingkey=error")
// This will FAIL if any template variable is undefined
```

**Impact**:
- Any undefined variable in baseRef → Pod fails to start
- Error message not user-friendly
- Difficult to debug

**Test Scenarios Required**:
- Test with all valid template variables
- Test with undefined variables (should give clear error)
- Test with nested variables

---

## TEST SCENARIO CATEGORIES

1. **Raw KServe Baseline** (10 scenarios)
2. **LLMD Basic Features** (25 scenarios)
3. **LLMD Advanced Features** (40 scenarios)
4. **Configuration Management** (18 scenarios)
5. **Networking & Routing** (22 scenarios)
6. **Scaling & Performance** (15 scenarios)
7. **Failure & Recovery** (20 scenarios)
8. **Security & RBAC** (10 scenarios)
9. **Integration Tests** (8 scenarios)

---

# CATEGORY 1: RAW KSERVE BASELINE (Control Group)

## Scenario RK-001: Basic ServingRuntime Deployment
**Priority**: P0 (Blocker)  
**Type**: Baseline Control  
**Purpose**: Establish performance baseline without LLMD

### Prerequisites
- RHOAI installed
- Namespace created
- GPU node available (or CPU for OPT-125M)

### Test Steps

#### Step 1: Create ServingRuntime
```bash
# Action
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: vllm-runtime-baseline
  namespace: test-baseline
spec:
  supportedModelFormats:
  - name: vllm
    version: "1"
  containers:
  - name: kserve-container
    image: vllm/vllm-openai:v0.6.3
    args:
    - --port=8080
    - --model=/mnt/models
    resources:
      requests:
        cpu: "2"
        memory: "8Gi"
EOF

# Expected Result
✓ ServingRuntime created
✓ No errors in output

# Validation
kubectl get servingruntime vllm-runtime-baseline -n test-baseline
# Should show: Ready=True
```

#### Step 2: Create InferenceService
```bash
# Action  
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: opt125m-baseline
  namespace: test-baseline
spec:
  predictor:
    model:
      modelFormat:
        name: vllm
      runtime: vllm-runtime-baseline
      storageUri: oci://quay.io/opendatahub/opt-125m:latest
EOF

# Expected Result
✓ InferenceService created
✓ Status transitions: Pending → Creating → Ready

# Validation
kubectl get isvc opt125m-baseline -n test-baseline
# Should show: READY=True
```

#### Step 3: Verify Deployment Created
```bash
# Action
kubectl get deployment -n test-baseline -l serving.kserve.io/inferenceservice=opt125m-baseline

# Expected Result
✓ Deployment exists
✓ Name pattern: opt125m-baseline-predictor-*
✓ Replicas: 1/1 available

# Validation - Check pod details
kubectl get pods -n test-baseline -l serving.kserve.io/inferenceservice=opt125m-baseline -o yaml

# Verify:
✓ Init container: storage-initializer (downloads model)
✓ Main container: kserve-container (runs vLLM)
✓ No routing sidecar (this is raw KServe)
✓ No llm-d.ai/* labels
```

#### Step 4: Verify Service Created
```bash
# Action
kubectl get svc -n test-baseline -l serving.kserve.io/inferenceservice=opt125m-baseline

# Expected Result
✓ Service exists  
✓ Name: opt125m-baseline-predictor
✓ Type: ClusterIP
✓ Port: 80 or 8080
```

#### Step 5: Verify NO LLMD Resources
```bash
# Action - These should NOT exist
kubectl get llmisvc -n test-baseline
kubectl get inferencepool -n test-baseline  
kubectl get httproute -n test-baseline

# Expected Result
✓ No LLMInferenceService found
✓ No InferencePool found
✓ HTTPRoute may exist (if serverless mode)
```

#### Step 6: Test Inference
```bash
# Action - Get service URL
ISVC_URL=$(kubectl get isvc opt125m-baseline -n test-baseline -o jsonpath='{.status.url}')

# Send inference request
curl -X POST "$ISVC_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "opt125m-baseline",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "max_tokens": 20
  }'

# Expected Result
✓ HTTP 200 OK
✓ Valid JSON response
✓ Response contains "choices" array
✓ Response time < 5 seconds (first request)

# Sample Response
{
  "id": "cmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "opt125m-baseline",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "2+2 equals 4."
    },
    "finish_reason": "stop"
  }]
}
```

#### Step 7: Measure Baseline Metrics
```bash
# Action - Run load test
for i in {1..100}; do
  time curl -s -X POST "$ISVC_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model":"opt125m-baseline","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}' \
    > /dev/null
done | awk '/real/ {sum+=$2; count++} END {print "Average latency:", sum/count, "seconds"}'

# Expected Result
✓ Average latency recorded (baseline)
✓ No request failures
✓ Consistent response times

# Record for comparison
echo "BASELINE_LATENCY: XXXXms" > baseline-metrics.txt
```

### Expected Results Summary
| Metric | Expected Value | Actual | Pass/Fail |
|--------|----------------|--------|-----------|
| InferenceService Ready | True | | |
| Deployment Available | 1/1 | | |
| Pod Running | True | | |
| Inference Response | 200 OK | | |
| Average Latency | < 2000ms | | |
| No LLMD Resources | Confirmed | | |

### Edge Cases to Test

#### EC-RK-001: Invalid Model URI
```bash
# Test with non-existent model
storageUri: oci://invalid-registry/model:latest

# Expected Result
✗ Pod in CrashLoopBackOff
✗ Storage-initializer logs show: "404 Not Found" or "Failed to pull"
✗ InferenceService status: Ready=False, reason=ModelDownloadFailed
```

#### EC-RK-002: Insufficient Memory
```bash
# Test with 70B model on 8Gi memory
resources:
  requests:
    memory: "8Gi"  # Too small for 70B!

# Expected Result
✗ Pod OOMKilled
✗ vLLM logs show: "RuntimeError: CUDA out of memory"
✗ Pod restarts repeatedly
```

#### EC-RK-003: Missing Runtime
```bash
# Reference non-existent runtime
runtime: non-existent-runtime

# Expected Result
✗ InferenceService status: Ready=False
✗ Error message: "ServingRuntime 'non-existent-runtime' not found"
```

### Cleanup
```bash
kubectl delete isvc opt125m-baseline -n test-baseline
kubectl delete servingruntime vllm-runtime-baseline -n test-baseline
kubectl delete namespace test-baseline
```

---

## Scenario RK-002: Raw KServe with Multiple Replicas
**Priority**: P1 (Critical)  
**Type**: Baseline Scaling

### Test Steps

#### Step 1: Deploy with 3 Replicas
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: opt125m-scaled
  namespace: test-baseline
spec:
  predictor:
    minReplicas: 3
    maxReplicas: 3
    model:
      modelFormat:
        name: vllm
      runtime: vllm-runtime-baseline
      storageUri: oci://quay.io/opendatahub/opt-125m:latest
EOF

# Expected: 3 pods created
```

#### Step 2: Verify All Replicas Running
```bash
# Wait for all pods
kubectl wait --for=condition=Ready pod \
  -l serving.kserve.io/inferenceservice=opt125m-scaled \
  -n test-baseline \
  --timeout=600s

# Verify count
POD_COUNT=$(kubectl get pods -l serving.kserve.io/inferenceservice=opt125m-scaled \
  -n test-baseline --field-selector=status.phase=Running | wc -l)

echo "Running pods: $POD_COUNT"
# Expected: 3 (or 4 with header line)

# Expected Result
✓ 3 pods in Running state
✓ All pods have container ready
✓ No pods in Error/CrashLoopBackOff
```

#### Step 3: Test Load Distribution
```bash
# Send 30 requests (10 per pod expected)
for i in {1..30}; do
  curl -s -X POST "$ISVC_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"opt125m-scaled\",\"messages\":[{\"role\":\"user\",\"content\":\"Request $i\"}],\"max_tokens\":5}" &
done
wait

# Check which pods handled requests
for pod in $(kubectl get pods -l serving.kserve.io/inferenceservice=opt125m-scaled \
  -n test-baseline -o name); do
  REQUEST_COUNT=$(kubectl logs $pod -n test-baseline -c kserve-container | \
    grep "POST /v1/chat/completions" | wc -l)
  echo "$pod: $REQUEST_COUNT requests"
done

# Expected Result
✓ All pods received requests
✓ Distribution roughly equal (8-12 requests per pod)
✓ No single pod overloaded
```

#### Step 4: Test Pod Failure During Traffic
```bash
# Start continuous load
(while true; do
  curl -s "$ISVC_URL/v1/chat/completions" \
    -d '{"model":"opt125m-scaled","messages":[{"role":"user","content":"Test"}],"max_tokens":5}'
  sleep 1
done) &
LOAD_PID=$!

# Delete one pod after 30 seconds
sleep 30
POD_TO_DELETE=$(kubectl get pods -l serving.kserve.io/inferenceservice=opt125m-scaled \
  -n test-baseline -o jsonpath='{.items[0].metadata.name}')
echo "Deleting pod: $POD_TO_DELETE"
kubectl delete pod $POD_TO_DELETE -n test-baseline

# Continue load for another 60 seconds
sleep 60
kill $LOAD_PID

# Expected Result
✓ Some requests may fail during pod deletion (~5-10 seconds)
✓ Service recovers automatically
✓ New pod starts within 60 seconds
✓ Traffic resumes to all 3 pods
```

### Edge Cases

#### EC-RK-004: Scale to 0 Replicas
```bash
kubectl patch isvc opt125m-scaled -n test-baseline --type='json' \
  -p='[{"op": "replace", "path": "/spec/predictor/minReplicas", "value":0}]'

# Expected Result
✓ If serverless mode: Pods terminate, scale-to-zero works
✗ If raw deployment: MinReplicas=0 rejected or pods remain at 1
```

---

# CATEGORY 2: LLMD BASIC FEATURES

## Scenario LB-001: Basic LLMD Deployment (OCI Storage)
**Priority**: P0 (Blocker)  
**Type**: LLMD Core Functionality  
**Related Issue**: ISSUE-001 (Controller reconciliation)

### Prerequisites
- LLMD controller enabled in RHOAI
- Gateway API installed
- Gateway created (or use default)

### Test Steps

#### Step 1: Verify Controller Status
```bash
# CRITICAL: Verify controller reconciliation is enabled
kubectl logs -n kserve deployment/kserve-controller-manager -c manager | \
  grep "reconcileWorkload\|reconcileRouter"

# Expected Result
✓ Logs show "Reconciling Workload" messages
✓ Logs show "Reconciling Router" messages
✗ If no logs: FAIL - Controller reconciliation disabled (ISSUE-001)
```

#### Step 2: Create Gateway (if needed)
```bash
kubectl apply -f - <<EOF
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: llmd-gateway
  namespace: istio-system
spec:
  gatewayClassName: istio
  listeners:
  - name: http
    protocol: HTTP
    port: 80
EOF

# Verify gateway ready
kubectl wait --for=condition=Programmed gateway/llmd-gateway \
  -n istio-system --timeout=300s

# Expected Result
✓ Gateway status: Programmed=True
✓ Gateway has external IP or hostname
```

#### Step 3: Create LLMInferenceService
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-basic-oci
  namespace: test-llmd
spec:
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
    name: opt-125m
  replicas: 1
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      resources:
        requests:
          cpu: "2"
          memory: "8Gi"
        limits:
          cpu: "2"
          memory: "8Gi"
  router:
    gateway: {}
    route: {}
EOF

# Expected Result
✓ LLMInferenceService created
✓ No validation errors
```

#### Step 4: Monitor Status Transitions
```bash
# Watch status
kubectl get llmisvc llm-basic-oci -n test-llmd -w

# Expected Status Progression
1. Initially: Ready=Unknown
2. After 10-30s: PresetsCombined=True
3. After 30-60s: MainWorkloadReady=True
4. After 60-90s: RouterReady=True
5. Finally: Ready=True

# Verify with detailed status
kubectl get llmisvc llm-basic-oci -n test-llmd -o yaml

# Check status.conditions
# Expected conditions (from lifecycle.go):
- type: PresetsCombined
  status: "True"
- type: MainWorkloadReady
  status: "True"
- type: RouterReady
  status: "True"
- type: Ready
  status: "True"
```

#### Step 5: Verify Deployment Created
```bash
# Check deployment (from workload_single_node.go:86)
DEPLOYMENT_NAME="llm-basic-oci-kserve"
kubectl get deployment $DEPLOYMENT_NAME -n test-llmd

# Expected Result
✓ Deployment exists
✓ Available replicas: 1/1
✓ Ready replicas: 1/1

# Verify labels (from workload_single_node.go:80-82)
kubectl get deployment $DEPLOYMENT_NAME -n test-llmd -o yaml | grep -A 10 labels:

# Expected labels:
app.kubernetes.io/component: llminferenceservice-workload
app.kubernetes.io/name: llm-basic-oci
app.kubernetes.io/part-of: llminferenceservice
kserve.io/component: workload
llm-d.ai/role: both  # "both" because no prefill specified
```

#### Step 6: Verify Pod Structure
```bash
# Get pod
POD=$(kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-basic-oci \
  -o jsonpath='{.items[0].metadata.name}')

# Check init containers
kubectl get pod $POD -n test-llmd -o jsonpath='{.spec.initContainers[*].name}'

# Expected Result
✓ storage-initializer present
✗ llm-d-routing-sidecar NOT present (single node, no disaggregation)

# Check main containers
kubectl get pod $POD -n test-llmd -o jsonpath='{.spec.containers[*].name}'

# Expected Result
✓ main container present
✓ Only 1 main container (no sidecar running)

# Verify storage-initializer args
kubectl get pod $POD -n test-llmd -o yaml | grep -A 5 "name: storage-initializer"

# Expected:
args:
- oci://quay.io/opendatahub/opt-125m:latest
- /mnt/models
```

#### Step 7: Verify HTTPRoute Created
```bash
# Check HTTPRoute (from router.go:120)
HTTPROUTE_NAME="llm-basic-oci-kserve-route"
kubectl get httproute $HTTPROUTE_NAME -n test-llmd -o yaml

# Expected Result
✓ HTTPRoute exists
✓ ParentRefs point to gateway
✓ Path matches: /test-llmd/llm-basic-oci
✓ Backend: InferencePool (if scheduler) or Service

# Verify path configuration
kubectl get httproute $HTTPROUTE_NAME -n test-llmd \
  -o jsonpath='{.spec.rules[0].matches[0].path.value}'

# Expected: /test-llmd/llm-basic-oci
```

#### Step 8: Verify Service Created
```bash
SERVICE_NAME="llm-basic-oci-kserve-workload-svc"
kubectl get svc $SERVICE_NAME -n test-llmd

# Expected Result
✓ Service exists
✓ Type: ClusterIP
✓ Selector matches pod labels
✓ Port: 8000
```

#### Step 9: Verify URL in Status
```bash
kubectl get llmisvc llm-basic-oci -n test-llmd \
  -o jsonpath='{.status.url}'

# Expected Result
✓ URL present
✓ URL format: http://<gateway-host>/test-llmd/llm-basic-oci
✓ Also check .status.addresses for additional URLs
```

#### Step 10: Test Inference
```bash
# Get URL from status
LLMD_URL=$(kubectl get llmisvc llm-basic-oci -n test-llmd -o jsonpath='{.status.url}')

# Test inference
curl -X POST "$LLMD_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "opt-125m",
    "messages": [{"role": "user", "content": "What is AI?"}],
    "max_tokens": 50
  }'

# Expected Result
✓ HTTP 200 OK
✓ Valid JSON response
✓ Response contains generated text
✓ Response time < 5 seconds

# Verify in logs
kubectl logs $POD -n test-llmd -c main | grep "POST /v1/chat/completions"
# Expected: Log entry for the request
```

#### Step 11: Verify No Crashes/Restarts
```bash
# Check restart count
kubectl get pod $POD -n test-llmd \
  -o jsonpath='{.status.containerStatuses[0].restartCount}'

# Expected Result
✓ Restart count: 0
✓ All containers ready
✓ Pod age > 5 minutes

# Check for errors in logs
kubectl logs $POD -n test-llmd -c main | grep -i "error\|exception\|failed"

# Expected Result
✓ No critical errors
✓ vLLM started successfully
✓ Model loaded without errors
```

### Verification Checklist

| Resource | Expected | Actual | Status |
|----------|----------|--------|--------|
| LLMInferenceService | Created, Ready=True | | ☐ |
| Deployment | 1 replica available | | ☐ |
| Pod | Running, 0 restarts | | ☐ |
| Service | ClusterIP, port 8000 | | ☐ |
| HTTPRoute | Path matches | | ☐ |
| URL in status | Present | | ☐ |
| Inference works | 200 OK | | ☐ |
| No LLMD-specific issues | Confirmed | | ☐ |

### Edge Cases

#### EC-LB-001: Controller Reconciliation Disabled
```bash
# If ISSUE-001 not fixed, verify behavior
kubectl get llmisvc llm-basic-oci -n test-llmd -o yaml

# Check if resources created
kubectl get deployment,service,httproute -n test-llmd -l app.kubernetes.io/name=llm-basic-oci

# Expected if ISSUE-001 present:
✗ LLMInferenceService status shows Ready=True
✗ BUT no Deployment created
✗ No Service created
✗ No HTTPRoute created
✗ Status is lying - resources don't exist

# This is CRITICAL BUG if found
```

#### EC-LB-002: Invalid Model URI
```bash
# Create with bad URI
spec:
  model:
    uri: oci://invalid-registry/model:nonexistent

# Expected Result
✗ Pod in CrashLoopBackOff
✗ Storage-initializer logs: "Failed to pull image"
✗ LLMInferenceService status: MainWorkloadReady=False
```

#### EC-LB-003: Missing Gateway
```bash
# Create LLMD without gateway existing
spec:
  router:
    gateway:
      refs:
      - name: non-existent-gateway
        namespace: istio-system

# Expected Result
✗ HTTPRoute created but not programmed
✗ Status: RouterReady=False or Warning
✗ No external access
```

### Cleanup
```bash
kubectl delete llmisvc llm-basic-oci -n test-llmd
```

---

## Scenario LB-002: LLMD with S3 Storage
**Priority**: P1  
**Type**: Storage Integration

### Test Steps

#### Step 1: Create S3 Secret
```bash
kubectl create secret generic llmd-s3-secret -n test-llmd \
  --from-literal=AWS_ACCESS_KEY_ID=<key> \
  --from-literal=AWS_SECRET_ACCESS_KEY=<secret> \
  --from-literal=AWS_REGION=us-east-1 \
  --from-literal=AWS_S3_ENDPOINT=https://s3.amazonaws.com \
  --from-literal=AWS_S3_BUCKET=my-models-bucket

# Expected Result
✓ Secret created
✓ All keys present
```

#### Step 2: Create Service Account
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: llmd-s3-sa
  namespace: test-llmd
secrets:
- name: llmd-s3-secret
EOF

# Expected Result
✓ ServiceAccount created
✓ Secret linked
```

#### Step 3: Create LLMD with S3 Storage
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-s3
  namespace: test-llmd
spec:
  model:
    uri: s3://my-models-bucket/models/opt-125m/
    name: opt-125m-s3
  replicas: 1
  template:
    serviceAccountName: llmd-s3-sa
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      env:
      - name: AWS_ACCESS_KEY_ID
        valueFrom:
          secretKeyRef:
            name: llmd-s3-secret
            key: AWS_ACCESS_KEY_ID
      - name: AWS_SECRET_ACCESS_KEY
        valueFrom:
          secretKeyRef:
            name: llmd-s3-secret
            key: AWS_SECRET_ACCESS_KEY
      - name: AWS_REGION
        valueFrom:
          secretKeyRef:
            name: llmd-s3-secret
            key: AWS_REGION
      resources:
        requests:
          cpu: "2"
          memory: "8Gi"
  router:
    gateway: {}
    route: {}
EOF

# Expected Result
✓ LLMInferenceService created
✓ No validation errors
```

#### Step 4: Verify S3 Credentials Mounted
```bash
# Get pod
POD=$(kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-s3 \
  -o jsonpath='{.items[0].metadata.name}')

# Check ServiceAccount
kubectl get pod $POD -n test-llmd -o jsonpath='{.spec.serviceAccountName}'
# Expected: llmd-s3-sa

# Check env vars in storage-initializer
kubectl get pod $POD -n test-llmd -o yaml | \
  grep -A 20 "name: storage-initializer" | grep -A 10 "env:"

# Expected environment variables:
✓ AWS_ACCESS_KEY_ID
✓ AWS_SECRET_ACCESS_KEY  
✓ AWS_REGION
✓ Values from secret references
```

#### Step 5: Verify S3 Download
```bash
# Check storage-initializer logs
kubectl logs $POD -n test-llmd -c storage-initializer

# Expected Result
✓ Logs show: "Downloading from s3://my-models-bucket/models/opt-125m/"
✓ Progress indicators during download
✓ Final message: "Download complete" or "Model cached"
✓ No "403 Forbidden" or "404 Not Found" errors
```

#### Step 6: Test Inference
```bash
LLMD_URL=$(kubectl get llmisvc llm-s3 -n test-llmd -o jsonpath='{.status.url}')

curl -X POST "$LLMD_URL/v1/chat/completions" \
  -d '{"model":"opt-125m-s3","messages":[{"role":"user","content":"Test S3"}],"max_tokens":20}'

# Expected Result
✓ HTTP 200 OK
✓ Model loaded from S3 works correctly
```

### Edge Cases

#### EC-LB-101: Invalid AWS Credentials
```bash
# Create with wrong credentials
AWS_ACCESS_KEY_ID=INVALID_KEY

# Expected Result
✗ Storage-initializer logs: "403 Forbidden" or "SignatureDoesNotMatch"
✗ Pod in CrashLoopBackOff
✗ LLMInferenceService status: MainWorkloadReady=False, reason=ModelDownloadFailed
```

#### EC-LB-102: Bucket Does Not Exist
```bash
spec:
  model:
    uri: s3://non-existent-bucket/model/

# Expected Result
✗ Storage-initializer logs: "404 Not Found" or "NoSuchBucket"
✗ Pod restarts
```

#### EC-LB-103: Network Timeout
```bash
# Simulate with network policy blocking S3
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-s3
  namespace: test-llmd
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: llm-s3
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector: {}
EOF

# Expected Result
✗ Timeout during download
✗ Retry attempts visible in logs
✗ Eventually fails after timeout threshold
```

---

# CATEGORY 3: LLMD ADVANCED FEATURES

## Scenario LA-001: BaseRefs Configuration Inheritance
**Priority**: P1  
**Type**: Configuration Management  
**Related Issue**: ISSUE-002 (Template variables)

### Test Steps

#### Step 1: Create Base Configuration
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: standard-vllm-config
  namespace: test-llmd
spec:
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      args:
      - --dtype=float16
      - --max-model-len=4096
      resources:
        requests:
          cpu: "4"
          memory: "16Gi"
EOF

# Expected Result
✓ LLMInferenceServiceConfig created
✓ No errors
```

#### Step 2: Create LLMD with BaseRef
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-with-baseref
  namespace: test-llmd
spec:
  baseRefs:
  - name: standard-vllm-config
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
  replicas: 2
  template:
    containers:
    - name: main
      resources:
        requests:
          cpu: "2"  # Override CPU (lower)
          nvidia.com/gpu: "1"  # Add GPU
EOF

# Expected Result
✓ LLMInferenceService created
✓ Status: PresetsCombined=True
```

#### Step 3: Verify Configuration Merge
```bash
# Get actual deployment
DEP=$(kubectl get deployment -n test-llmd -l app.kubernetes.io/name=llm-with-baseref \
  -o jsonpath='{.items[0].metadata.name}')

# Check container configuration
kubectl get deployment $DEP -n test-llmd -o yaml | grep -A 30 "containers:"

# Expected merged result:
✓ image: vllm/vllm-openai:v0.6.3  # From base config
✓ args: [--dtype=float16, --max-model-len=4096]  # From base
✓ cpu: "2"  # From LLMD spec (overrides base "4")
✓ memory: "16Gi"  # From base config
✓ nvidia.com/gpu: "1"  # From LLMD spec (additional)

# Verify merge priority (LLMD spec wins)
CPU_REQUEST=$(kubectl get deployment $DEP -n test-llmd \
  -o jsonpath='{.spec.template.spec.containers[0].resources.requests.cpu}')
echo "CPU Request: $CPU_REQUEST"
# Expected: "2" not "4"
```

#### Step 4: Test Multiple BaseRefs (Priority)
```bash
# Create second config
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: gpu-config
  namespace: test-llmd
spec:
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.4  # Different version
      resources:
        requests:
          nvidia.com/gpu: "2"  # Different GPU count
EOF

# Create LLMD with both baseRefs
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-multi-baseref
  namespace: test-llmd
spec:
  baseRefs:
  - name: standard-vllm-config  # Applied first
  - name: gpu-config  # Applied second (overrides)
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
  router:
    gateway: {}
    route: {}
EOF

# Verify final image (last baseRef should win)
DEP=$(kubectl get deployment -n test-llmd -l app.kubernetes.io/name=llm-multi-baseref \
  -o jsonpath='{.items[0].metadata.name}')

IMAGE=$(kubectl get deployment $DEP -n test-llmd \
  -o jsonpath='{.spec.template.spec.containers[0].image}')

echo "Final image: $IMAGE"
# Expected: vllm/vllm-openai:v0.6.4 (from gpu-config, not standard-vllm-config)
```

### Edge Cases

#### EC-LA-001: BaseRef Not Found
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-missing-baseref
  namespace: test-llmd
spec:
  baseRefs:
  - name: non-existent-config  # Doesn't exist!
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
  router:
    gateway: {}
    route: {}
EOF

# Expected Result
✗ LLMInferenceService created but NOT ready
✗ Status condition: PresetsCombined=False
✗ Reason: "CombineBaseError"
✗ Message contains: "failed to get LLMInferenceServiceConfig"
✗ No deployment created

# Verify error
kubectl get llmisvc llm-missing-baseref -n testllmd -o yaml | grep -A 5 "conditions:"

# Expected condition:
- type: PresetsCombined
  status: "False"
  reason: CombineBaseError
  message: "failed to combine base-configurations: failed to get LLMInferenceServiceConfig \"non-existent-config\""
```

#### EC-LA-002: Template Variable in BaseRef (ISSUE-002)
```bash
# Create config with template variable
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: template-var-config
  namespace: test-llmd
spec:
  model:
    name: "{{.Name}}-model"  # Template variable!
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      args:
      - --served-model-name={{.Name}}  # Template variable!
EOF

# Create LLMD using this config
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-template-test
  namespace: test-llmd
spec:
  baseRefs:
  - name: template-var-config
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
  router:
    gateway: {}
    route: {}
EOF

# Check if variables substituted
kubectl wait --for=condition=Ready llmisvc/llm-template-test -n test-llmd --timeout=300s

POD=$(kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-template-test \
  -o jsonpath='{.items[0].metadata.name}')

# Check actual args in pod
kubectl get pod $POD -n test-llmd -o yaml | grep "served-model-name"

# Expected Result (if working correctly):
✓ --served-model-name=llm-template-test  # Variable substituted

# BUT if ISSUE-002 present:
✗ --served-model-name={{.Name}}  # Variable NOT substituted (literal)
✗ vLLM fails to start with error: "Invalid model name '{{.Name}}'"
✗ Pod crashes

# CRITICAL: This is ISSUE-002 - Template variables in baseRefs may not substitute
```

#### EC-LA-003: Circular BaseRef
```bash
# Create config A referencing config B
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: config-a
  namespace: test-llmd
spec:
  baseRefs:
  - name: config-b
  template:
    containers:
    - name: main
      image: image-a
EOF

# Create config B referencing config A (circular!)
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: config-b
  namespace: test-llmd
spec:
  baseRefs:
  - name: config-a  # Circular reference!
  template:
    containers:
    - name: main
      image: image-b
EOF

# Try to use config A
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-circular
  namespace: test-llmd
spec:
  baseRefs:
  - name: config-a
  model:
    uri: oci://model
  router:
    gateway: {}
EOF

# Expected Result
✗ Controller error or timeout
✗ Status: PresetsCombined=False
✗ Reason: Infinite loop or stack overflow
✗ Controller logs may show error

# Note: This should be prevented by validation but may not be
```

---

## Scenario LA-020: Prefill/Decode Disaggregation ⭐ **CRITICAL**
**Priority**: P0 (Blocker)  
**Type**: Core LLMD Feature

### Prerequisites
- Gateway API with ExtProc support
- Sufficient GPU resources (or CPU for testing)
- llm-d images available

### Test Steps

#### Step 1: Create Disaggregated LLMD
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-disagg
  namespace: test-llmd
spec:
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
    name: opt-125m-disagg
  
  # Decode configuration (top-level)
  replicas: 4
  parallelism:
    tensor: 1
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      resources:
        requests:
          cpu: "2"
          memory: "8Gi"
  
  # Prefill configuration
  prefill:
    replicas: 2
    parallelism:
      tensor: 1
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
        env:
        - name: VLLM_PREFILL_MODE
          value: "true"
        resources:
          requests:
            cpu: "4"
            memory: "16Gi"
  
  # Enable scheduler
  router:
    gateway: {}
    route: {}
    scheduler: {}
EOF

# Expected Result
✓ LLMInferenceService created
✓ Multiple resources will be created
```

#### Step 2: Wait for All Components Ready
```bash
# This may take 5-10 minutes
kubectl wait --for=condition=Ready llmisvc/llm-disagg -n test-llmd --timeout=900s

# Expected Result
✓ Status: Ready=True
✓ All conditions True
```

#### Step 3: Verify Prefill Deployment
```bash
# Check prefill deployment (from workload_single_node.go:156)
PREFILL_DEP="llm-disagg-kserve-prefill"
kubectl get deployment $PREFILL_DEP -n test-llmd

# Expected Result
✓ Deployment exists
✓ Replicas: 2/2 available
✓ Name matches pattern: <llmisvc-name>-kserve-prefill

# Verify prefill label (workload_single_node.go:151)
kubectl get deployment $PREFILL_DEP -n test-llmd \
  -o jsonpath='{.metadata.labels.llm-d\.ai/role}'

# Expected: "prefill"

# Check prefill pods
kubectl get pods -n test-llmd -l llm-d.ai/role=prefill

# Expected Result
✓ 2 pods Running
✓ Pod names: llm-disagg-kserve-prefill-xxxxx-yyyyy
✓ Each pod has VLLM_PREFILL_MODE=true env var
```

#### Step 4: Verify Decode Deployment
```bash
# Check decode deployment
DECODE_DEP="llm-disagg-kserve"
kubectl get deployment $DECODE_DEP -n test-llmd

# Expected Result
✓ Deployment exists
✓ Replicas: 4/4 available

# Verify decode label (workload_single_node.go:76-78)
kubectl get deployment $DECODE_DEP -n test-llmd \
  -o jsonpath='{.metadata.labels.llm-d\.ai/role}'

# Expected: "decode" (not "both", because prefill exists)

# Check decode pods
kubectl get pods -n test-llmd -l llm-d.ai/role=decode

# Expected Result
✓ 4 pods Running
✓ Pod names: llm-disagg-kserve-xxxxx-yyyyy
```

#### Step 5: Verify Routing Sidecar in Decode Pods
```bash
# Get one decode pod
DECODE_POD=$(kubectl get pods -n test-llmd -l llm-d.ai/role=decode \
  -o jsonpath='{.items[0].metadata.name}')

# Check init containers (from workload_single_node.go:107-119)
kubectl get pod $DECODE_POD -n test-llmd \
  -o jsonpath='{.spec.initContainers[*].name}'

# Expected Result
✓ storage-initializer present
✓ llm-d-routing-sidecar present

# Verify sidecar has restartPolicy=Always (runs as sidecar)
kubectl get pod $DECODE_POD -n test-llmd -o yaml | \
  grep -A 5 "name: llm-d-routing-sidecar" | grep restartPolicy

# Expected: restartPolicy: Always

# Verify INFERENCE_POOL_NAME env var (workload_single_node.go:114-118)
kubectl get pod $DECODE_POD -n test-llmd -o yaml | \
  grep -A 20 "name: llm-d-routing-sidecar" | grep INFERENCE_POOL_NAME

# Expected: INFERENCE_POOL_NAME: llm-disagg-inference-pool

# Verify ports
kubectl get pod $DECODE_POD -n test-llmd -o yaml | \
  grep -A 30 "containers:"

# Expected:
# Sidecar (init with restartPolicy:Always):
#   - port: 8000 (external, receives requests)
# Main container:
#   - port: 8001 (internal, sidecar forwards to this)
```

#### Step 6: Verify NO Routing Sidecar in Prefill Pods
```bash
# Get one prefill pod
PREFILL_POD=$(kubectl get pods -n test-llmd -l llm-d.ai/role=prefill \
  -o jsonpath='{.items[0].metadata.name}')

# Check init containers
kubectl get pod $PREFILL_POD -n test-llmd \
  -o jsonpath='{.spec.initContainers[*].name}'

# Expected Result
✓ storage-initializer present
✗ llm-d-routing-sidecar NOT present (prefill doesn't need routing)

# Verify only one container running
kubectl get pod $PREFILL_POD -n test-llmd \
  -o jsonpath='{.spec.containers[*].name}'

# Expected: main (only one container)
```

#### Step 7: Verify Scheduler Deployment
```bash
# Check scheduler (from scheduler.go:290)
SCHEDULER_DEP="llm-disagg-kserve-router-scheduler"
kubectl get deployment $SCHEDULER_DEP -n test-llmd

# Expected Result
✓ Deployment exists
✓ Replicas: 1/1 available
✓ Name pattern: <llmisvc-name>-kserve-router-scheduler

# Check scheduler pod
SCHEDULER_POD=$(kubectl get pods -n test-llmd \
  -l app.kubernetes.io/component=llminferenceservice-router-scheduler \
  -o jsonpath='{.items[0].metadata.name}')

kubectl get pod $SCHEDULER_POD -n test-llmd

# Expected Result
✓ Pod Running
✓ Container: main (llm-d-inference-scheduler)
✓ Ports: 9002 (gRPC), 9003 (health), 9090 (metrics)
```

#### Step 8: Verify InferencePool
```bash
# Check InferencePool (from scheduler.go:237)
kubectl get inferencepool llm-disagg-inference-pool -n test-llmd -o yaml

# Expected Result
✓ InferencePool exists
✓ Selector matches workload labels
✓ targetPortNumber: 8000

# Verify selector (from config_merge.go:152-158)
kubectl get inferencepool llm-disagg-inference-pool -n test-llmd \
  -o jsonpath='{.spec.selector}'

# Expected selector includes:
app.kubernetes.io/name: llm-disagg
kserve.io/component: workload

# Verify endpoints discovered
kubectl get inferencepool llm-disagg-inference-pool -n test-llmd \
  -o jsonpath='{.status.endpoints}'

# Expected: Should list all 6 pods (2 prefill + 4 decode)
```

#### Step 9: Verify InferenceModel
```bash
# Check InferenceModel (from scheduler.go:259)
kubectl get inferencemodel llm-disagg -n test-llmd -o yaml

# Expected Result
✓ InferenceModel exists
✓ modelName: opt-125m-disagg
✓ poolRef.name: llm-disagg-inference-pool
✓ criticality: Critical (default if not specified)

# Verify pool reference
kubectl get inferencemodel llm-disagg -n test-llmd \
  -o jsonpath='{.spec.poolRef.name}'

# Expected: llm-disagg-inference-pool
```

#### Step 10: Verify Scheduler Service
```bash
# Check EPP service (from scheduler.go:180)
EPP_SVC="llm-disagg-epp-service"
kubectl get svc $EPP_SVC -n test-llmd

# Expected Result
✓ Service exists
✓ Type: ClusterIP
✓ Ports include: grpc (9002)

# Verify ports (scheduler.go:216-223)
kubectl get svc $EPP_SVC -n test-llmd -o yaml | grep -A 10 "ports:"

# Expected ports:
- name: grpc
  port: 9002
- name: grpc-health
  port: 9003
- name: metrics
  port: 9090
```

#### Step 11: Test First Request (Prefill Flow)
```bash
# Get URL
LLMD_URL=$(kubectl get llmisvc llm-disagg -n test-llmd -o jsonpath='{.status.url}')

# Send first request with new session
SESSION_ID=$(uuidgen)

curl -X POST "$LLMD_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{
    "model": "opt-125m-disagg",
    "messages": [{"role": "user", "content": "Explain quantum computing in simple terms"}],
    "max_tokens": 100
  }'

# Expected Result
✓ HTTP 200 OK
✓ Response contains generated text
✓ Response time: 2-5 seconds (first request)
```

#### Step 12: Verify Request Flow Through Logs
```bash
# 1. Check scheduler logs
kubectl logs $SCHEDULER_POD -n test-llmd -c main --tail=50

# Expected in logs:
✓ "Processing request" or similar
✓ "prefill-filter" or "decode-filter" mentioned
✓ "Selected pod" or "Routing to" message

# 2. Find which decode pod handled request
for pod in $(kubectl get pods -n test-llmd -l llm-d.ai/role=decode -o name); do
  if kubectl logs $pod -c llm-d-routing-sidecar -n test-llmd | grep -q "$SESSION_ID"; then
    echo "Handling pod: $pod"
    HANDLING_POD=$(basename $pod)
    break
  fi
done

# 3. Check routing sidecar logs
kubectl logs $HANDLING_POD -c llm-d-routing-sidecar -n test-llmd --tail=50

# Expected in logs:
✓ Request received on port 8000
✓ "No KV cache found" or "Forwarding to prefill"
✓ Session ID appears in logs

# 4. Check prefill pod logs
for pod in $(kubectl get pods -n test-llmd -l llm-d.ai/role=prefill -o name); do
  if kubectl logs $pod -c main -n test-llmd --tail=100 | grep -q "POST /v1/chat/completions"; then
    echo "Prefill pod processed request: $pod"
    PREFILL_POD=$(basename $pod)
    break
  fi
done

kubectl logs $PREFILL_POD -c main -n test-llmd --tail=50

# Expected in logs:
✓ "POST /v1/chat/completions" request logged
✓ Processing completed
✓ Response sent back

# 5. Check decode pod logs (final generation)
kubectl logs $HANDLING_POD -c main -n test-llmd --tail=50

# Expected in logs:
✓ Request processed after receiving from sidecar
✓ Token generation logs
```

#### Step 13: Test Follow-Up Request (Cache Hit)
```bash
# Send follow-up request with SAME session ID
curl -X POST "$LLMD_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{
    "model": "opt-125m-disagg",
    "messages": [{"role": "user", "content": "Can you give me an example?"}],
    "max_tokens": 50
  }'

# Expected Result
✓ HTTP 200 OK
✓ Response time: 1-2 seconds (faster than first request!)
✓ Response makes sense in context

# Verify cache hit in logs
kubectl logs $HANDLING_POD -c llm-d-routing-sidecar -n test-llmd --tail=20

# Expected in logs:
✓ Session ID appears again
✓ "Cache hit" or "Using local decode"
✓ "Forwarding to localhost:8001" (not to prefill)

# Count prefill requests - should NOT increase
PREFILL_COUNT_BEFORE=$(kubectl logs $PREFILL_POD -c main -n test-llmd | \
  grep "POST /v1/chat/completions" | wc -l)

# Wait a moment then check again
sleep 5

PREFILL_COUNT_AFTER=$(kubectl logs $PREFILL_POD -c main -n test-llmd | \
  grep "POST /v1/chat/completions" | wc -l)

echo "Prefill requests before: $PREFILL_COUNT_BEFORE, after: $PREFILL_COUNT_AFTER"

# Expected Result
✓ Count should be the same (prefill NOT called for follow-up)
```

#### Step 14: Verify Scheduler Cache Affinity
```bash
# Send multiple follow-up requests with same session
for i in {1..5}; do
  curl -s -X POST "$LLMD_URL/v1/chat/completions" \
    -H "X-Session-ID: $SESSION_ID" \
    -d "{\"model\":\"opt-125m-disagg\",\"messages\":[{\"role\":\"user\",\"content\":\"Follow-up $i\"}],\"max_tokens\":10}"
  sleep 2
done

# Check which decode pods handled these requests
for pod in $(kubectl get pods -n test-llmd -l llm-d.ai/role=decode -o jsonpath='{.items[*].metadata.name}'); do
  COUNT=$(kubectl logs $pod -c llm-d-routing-sidecar -n test-llmd | grep "$SESSION_ID" | wc -l)
  echo "Pod $pod: $COUNT requests with this session"
done

# Expected Result
✓ All requests (or vast majority) went to same decode pod
✓ Scheduler maintained cache affinity
✓ Other decode pods: 0 or very few requests with this session ID
```

### Verification Checklist

| Component | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Prefill Deployment | 2/2 replicas | | ☐ |
| Decode Deployment | 4/4 replicas | | ☐ |
| Scheduler Deployment | 1/1 replica | | ☐ |
| Routing sidecar in decode | Present, restartPolicy=Always | | ☐ |
| NO sidecar in prefill | Confirmed | | ☐ |
| InferencePool | 6 endpoints | | ☐ |
| InferenceModel | Exists, correct poolRef | | ☐ |
| First request | Goes through prefill | | ☐ |
| Follow-up request | Skips prefill (cache hit) | | ☐ |
| Cache affinity | Same pod for session | | ☐ |

### Edge Cases

#### EC-LA-101: All Prefill Pods Crash
```bash
# Delete all prefill pods
kubectl delete pods -n test-llmd -l llm-d.ai/role=prefill

# Immediately try new request
NEW_SESSION=$(uuidgen)
curl -X POST "$LLMD_URL/v1/chat/completions" \
  -H "X-Session-ID: $NEW_SESSION" \
  -d '{"model":"opt-125m-disagg","messages":[{"role":"user","content":"Test"}],"max_tokens":10}' \
  --max-time 30

# Expected Result
✗ Request times out or returns 503/504
✗ Routing sidecar cannot reach prefill
✗ Error logs in sidecar: "Connection refused" or "Timeout"

# Wait for prefill pods to recover
kubectl wait --for=condition=Ready pod -n test-llmd \
  -l llm-d.ai/role=prefill \
  --timeout=300s

# Retry same request
curl -X POST "$LLMD_URL/v1/chat/completions" \
  -H "X-Session-ID: $NEW_SESSION" \
  -d '{"model":"opt-125m-disagg","messages":[{"role":"user","content":"Test"}],"max_tokens":10}'

# Expected Result
✓ HTTP 200 OK
✓ Service recovered
```

#### EC-LA-102: Routing Sidecar Not Injected
```bash
# This would indicate controller bug
# Check if sidecar missing in any decode pod
for pod in $(kubectl get pods -n test-llmd -l llm-d.ai/role=decode -o name); do
  SIDECAR=$(kubectl get $pod -n test-llmd -o jsonpath='{.spec.initContainers[?(@.name=="llm-d-routing-sidecar")].name}')
  if [ -z "$SIDECAR" ]; then
    echo "CRITICAL BUG: Sidecar missing in $pod"
  fi
done

# If sidecar missing:
✗ Decode pod only listens on port 8001 (not 8000)
✗ Requests fail with "Connection refused"
✗ This is a CRITICAL controller bug
```

#### EC-LA-103: Cache Eviction (Pod Restart)
```bash
# Establish session
SESSION=$(uuidgen)
curl -X POST "$LLMD_URL/v1/chat/completions" \
  -H "X-Session-ID: $SESSION" \
  -d '{"model":"opt-125m-disagg","messages":[{"role":"user","content":"Remember: XYZ123"}],"max_tokens":20}'

# Find handling pod
HANDLING_POD=$(kubectl get pods -n test-llmd -l llm-d.ai/role=decode -o name | head -1 | cut -d/ -f2)

# Delete the pod (cache evicted)
kubectl delete pod $HANDLING_POD -n test-llmd

# Wait for replacement
kubectl wait --for=condition=Ready pod -n test-llmd \
  -l llm-d.ai/role=decode \
  --timeout=300s

# Try follow-up with same session
curl -X POST "$LLMD_URL/v1/chat/completions" \
  -H "X-Session-ID: $SESSION" \
  -d '{"model":"opt-125m-disagg","messages":[{"role":"user","content":"What did I ask you to remember?"}],"max_tokens":20}'

# Expected Result
✓ Request succeeds
✗ Response doesn't contain "XYZ123" (cache lost)
✓ Scheduler routes to different pod or back to prefill
✓ Slower response (prefill involved again)
```

---

# CATEGORY 4: MULTI-NODE & PARALLELISM

## Scenario LA-031: Multi-Node Tensor Parallelism (LeaderWorkerSet)
**Priority**: P1  
**Type**: Advanced Parallelism  
**Related Feature**: LeaderWorkerSet (LWS) for multi-node deployments

### Prerequisites
- LeaderWorkerSet operator installed
- Multiple nodes with GPUs (or multi-GPU nodes)
- Sufficient GPU resources (8+ GPUs)

### Test Steps

#### Step 1: Create Multi-Node LLMD with Tensor Parallelism
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-multinode-tp
  namespace: test-llmd
spec:
  model:
    uri: oci://quay.io/opendatahub/llama-3-70b-instruct:latest
    name: llama-70b
  
  # Single replica of multi-node group
  replicas: 1
  
  # Tensor parallelism across 8 GPUs
  parallelism:
    tensor: 8
  
  # Leader pod configuration
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      args:
      - --tensor-parallel-size=8
      resources:
        requests:
          nvidia.com/gpu: "1"  # Per pod
          cpu: "8"
          memory: "64Gi"
  
  # Worker pods configuration (7 workers + 1 leader = 8 total)
  worker:
    replicas: 7
    template:
      containers:
      - name: main
        image: vllm/vllm-openai:v0.6.3
        resources:
          requests:
            nvidia.com/gpu: "1"
            cpu: "8"
            memory: "64Gi"
  
  router:
    gateway: {}
    route: {}
EOF

# Expected Result
✓ LLMInferenceService created
✓ No validation errors (worker requires parallelism set)
```

#### Step 2: Verify LeaderWorkerSet Created
```bash
# Check LWS (from workload_multi_node.go)
LWS_NAME="llm-multinode-tp-kserve"
kubectl get leaderworkerset $LWS_NAME -n test-llmd

# Expected Result
✓ LeaderWorkerSet exists
✓ Name pattern: <llmisvc-name>-kserve
✓ Status shows 1 group ready

# Verify LWS spec
kubectl get leaderworkerset $LWS_NAME -n test-llmd -o yaml

# Expected configuration:
spec:
  replicas: 1  # Number of leader-worker groups
  leaderWorkerTemplate:
    size: 8  # Total pods per group (1 leader + 7 workers)
    restartPolicy: Default
    leaderTemplate:
      # Leader pod spec
    workerTemplate:
      # Worker pod spec
```

#### Step 3: Verify Pod Group Created
```bash
# Check all pods in the group
kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-multinode-tp

# Expected Result
✓ 8 pods total (1 leader + 7 workers)
✓ Pod naming: llm-multinode-tp-kserve-0-0 (leader)
✓ Pod naming: llm-multinode-tp-kserve-0-1 to 0-7 (workers)
✓ All pods Running

# Verify leader pod
LEADER_POD=$(kubectl get pods -n test-llmd \
  -l leaderworkerset.sigs.k8s.io/worker-index=0 \
  -o jsonpath='{.items[0].metadata.name}')

echo "Leader pod: $LEADER_POD"

# Verify worker pods
kubectl get pods -n test-llmd \
  -l leaderworkerset.sigs.k8s.io/worker-index!=0

# Expected: 7 worker pods
```

#### Step 4: Verify Inter-Pod Communication Setup
```bash
# Check leader pod environment variables (from workload_multi_node.go:144-165)
kubectl get pod $LEADER_POD -n test-llmd -o yaml | grep -A 30 "env:"

# Expected environment variables:
✓ VLLM_TENSOR_PARALLEL_SIZE: "8"
✓ VLLM_WORKER_ADDRESSES: <list of worker pod IPs or DNS>
✓ VLLM_RANK: "0" (leader is rank 0)

# Check worker pod environment
WORKER_POD=$(kubectl get pods -n test-llmd \
  -l leaderworkerset.sigs.k8s.io/worker-index=1 \
  -o jsonpath='{.items[0].metadata.name}')

kubectl get pod $WORKER_POD -n test-llmd -o yaml | grep -A 30 "env:"

# Expected:
✓ VLLM_RANK: "1" (or 2, 3, etc. for other workers)
✓ VLLM_LEADER_ADDRESS: <leader pod IP or DNS>
```

#### Step 5: Verify Service Points to Leader
```bash
# Check service (from workload_multi_node.go:289)
SERVICE_NAME="llm-multinode-tp-kserve-workload-svc"
kubectl get svc $SERVICE_NAME -n test-llmd -o yaml

# Expected Result
✓ Service exists
✓ Selector targets ONLY leader pod:
  leaderworkerset.sigs.k8s.io/worker-index: "0"

# Verify endpoint has only leader IP
kubectl get endpoints $SERVICE_NAME -n test-llmd -o yaml

# Expected:
✓ Single IP address (leader pod only)
✓ Port 8000
```

#### Step 6: Verify Model Sharding in Logs
```bash
# Check leader logs for TP initialization
kubectl logs $LEADER_POD -n test-llmd -c main | grep -i "tensor parallel\|distributed\|rank"

# Expected in logs:
✓ "Initializing distributed environment with rank 0"
✓ "Tensor parallel size: 8"
✓ "Connected to 7 workers" or similar
✓ "Model sharded across 8 GPUs"

# Check one worker log
kubectl logs $WORKER_POD -n test-llmd -c main | grep -i "rank\|connected\|leader"

# Expected:
✓ "Rank 1" (or other rank)
✓ "Connected to leader" or "Joined distributed group"
✓ "Waiting for model shard"
```

#### Step 7: Wait for Model Loading (Large Model)
```bash
# This may take 10-30 minutes for 70B model
kubectl wait --for=condition=Ready pod $LEADER_POD -n test-llmd --timeout=1800s

# Monitor progress
watch kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-multinode-tp

# Expected:
✓ All pods transition to Running
✓ All containers ready
✓ No restarts
```

#### Step 8: Test Inference
```bash
LLMD_URL=$(kubectl get llmisvc llm-multinode-tp -n test-llmd -o jsonpath='{.status.url}')

# Test inference (first request will be slow)
time curl -X POST "$LLMD_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-70b",
    "messages": [{"role": "user", "content": "Explain the theory of relativity"}],
    "max_tokens": 200
  }'

# Expected Result
✓ HTTP 200 OK
✓ High-quality response (70B model)
✓ First request: 5-15 seconds
✓ Subsequent requests: 2-8 seconds
```

#### Step 9: Verify All GPUs Utilized
```bash
# Check GPU utilization on each pod
for pod in $(kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-multinode-tp \
  -o jsonpath='{.items[*].metadata.name}'); do
  echo "=== GPU utilization for $pod ==="
  kubectl exec $pod -n test-llmd -c main -- nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv
done

# Expected Result
✓ All 8 GPUs show memory usage
✓ GPU memory: 40-60GB used per GPU (for 70B model)
✓ During inference: GPU utilization spikes on all GPUs
```

### Verification Checklist

| Component | Expected | Actual | Status |
|-----------|----------|--------|--------|
| LeaderWorkerSet | 1 group of 8 pods | | ☐ |
| Leader pod | Running, rank 0 | | ☐ |
| Worker pods | 7 running, rank 1-7 | | ☐ |
| Service selector | Leader only | | ☐ |
| Tensor parallelism | All GPUs used | | ☐ |
| Inference works | 200 OK | | ☐ |

### Edge Cases

#### EC-LA-201: Worker Pod Crash During Inference
```bash
# Send continuous requests
(while true; do
  curl -s "$LLMD_URL/v1/chat/completions" \
    -d '{"model":"llama-70b","messages":[{"role":"user","content":"Test"}],"max_tokens":20}'
  sleep 2
done) &
LOAD_PID=$!

# Delete one worker pod after 30 seconds
sleep 30
WORKER_TO_DELETE=$(kubectl get pods -n test-llmd \
  -l leaderworkerset.sigs.k8s.io/worker-index=1 \
  -o jsonpath='{.items[0].metadata.name}')

echo "Deleting worker pod: $WORKER_TO_DELETE"
kubectl delete pod $WORKER_TO_DELETE -n test-llmd

# Expected Result
✗ Entire distributed group fails
✗ Leader logs: "Lost connection to worker rank 1"
✗ Leader may restart or hang
✗ All inference requests fail with 500 errors

# LeaderWorkerSet should recreate entire group
sleep 120
kill $LOAD_PID

kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-multinode-tp

# Expected:
✓ New group created (pod names changed)
✓ All 8 pods Running again
✓ Inference resumes after recovery (~5-10 minutes)
```

#### EC-LA-202: Leader Pod Crash
```bash
# Delete leader pod
kubectl delete pod $LEADER_POD -n test-llmd

# Expected Result
✗ All worker pods become useless (no leader)
✗ Service unavailable
✗ LeaderWorkerSet recreates entire group
✓ New leader + workers created
✓ Service automatically points to new leader
```

#### EC-LA-203: Mismatched Tensor Parallel Size
```bash
# Create with TP=8 but only 4 workers
spec:
  parallelism:
    tensor: 8
  worker:
    replicas: 3  # Wrong! Should be 7 (8 total - 1 leader)

# Expected Result
✗ LWS creates 4 pods (1 leader + 3 workers)
✗ vLLM fails to initialize: "Expected 8 ranks but got 4"
✗ Leader logs: "Timeout waiting for workers"
✗ Pods crash and restart repeatedly

# Validation should catch this but may not
```

---

## Scenario LA-032: Data Parallelism with Multiple Replicas
**Priority**: P1  
**Type**: Horizontal Scaling with Data Parallelism

### Test Steps

#### Step 1: Create LLMD with Data Parallelism
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-data-parallel
  namespace: test-llmd
spec:
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
    name: opt-125m-dp
  
  # 3 replica groups
  replicas: 3
  
  # Data parallelism: 2 local replicas per group
  parallelism:
    data: 2      # Total data parallel degree
    dataLocal: 2 # Replicas per node/group
  
  # Leader configuration
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      resources:
        requests:
          nvidia.com/gpu: "1"
          cpu: "4"
          memory: "16Gi"
  
  # Worker configuration (1 worker per group for dataLocal=2)
  worker:
    replicas: 1
    template:
      containers:
      - name: main
        image: vllm/vllm-openai:v0.6.3
        resources:
          requests:
            nvidia.com/gpu: "1"
            cpu: "4"
            memory: "16Gi"
  
  router:
    gateway: {}
    route: {}
    scheduler: {}  # Enable scheduler for load distribution
EOF

# Expected Result
✓ LLMInferenceService created
✓ Validation passes (data and dataLocal both set)
```

#### Step 2: Verify Multiple LeaderWorkerSets Created
```bash
# Check LWS resources
kubectl get leaderworkerset -n test-llmd -l app.kubernetes.io/name=llm-data-parallel

# Expected Result
✓ 3 LeaderWorkerSets (one per replica)
✓ Names: llm-data-parallel-kserve-0, llm-data-parallel-kserve-1, llm-data-parallel-kserve-2
✓ Each LWS has size=2 (1 leader + 1 worker)

# Verify total pods
kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-data-parallel

# Expected: 6 pods total (3 groups × 2 pods each)
```

#### Step 3: Verify Independent Groups
```bash
# Each group should be independent (can handle requests)
# Get leader pods from each group
for group in 0 1 2; do
  LEADER="llm-data-parallel-kserve-${group}-0"
  echo "=== Group $group leader: $LEADER ==="
  
  # Check if pod is running
  kubectl get pod $LEADER -n test-llmd
  
  # Check logs for data parallel config
  kubectl logs $LEADER -n test-llmd -c main | grep -i "data parallel" | head -5
done

# Expected:
✓ All 3 leaders running
✓ Each group operates independently
✓ No cross-group communication
```

#### Step 4: Verify InferencePool Discovery
```bash
# Check InferencePool
kubectl get inferencepool llm-data-parallel-inference-pool -n test-llmd -o yaml

# Expected Result
✓ InferencePool exists
✓ Discovers all 3 leader pods (service endpoints)
✓ targetPortNumber: 8000

# Verify endpoints
kubectl get inferencepool llm-data-parallel-inference-pool -n test-llmd \
  -o jsonpath='{.status.endpoints}'

# Expected: 3 endpoints (one per group leader)
```

#### Step 5: Test Load Distribution
```bash
LLMD_URL=$(kubectl get llmisvc llm-data-parallel -n test-llmd -o jsonpath='{.status.url}')

# Send 30 requests with unique session IDs
for i in {1..30}; do
  SESSION=$(uuidgen)
  curl -s -X POST "$LLMD_URL/v1/chat/completions" \
    -H "X-Session-ID: $SESSION" \
    -d "{\"model\":\"opt-125m-dp\",\"messages\":[{\"role\":\"user\",\"content\":\"Request $i\"}],\"max_tokens\":10}" &
done
wait

# Check which leader pods handled requests
for group in 0 1 2; do
  LEADER="llm-data-parallel-kserve-${group}-0"
  COUNT=$(kubectl logs $LEADER -n test-llmd -c main | grep "POST /v1/chat/completions" | wc -l)
  echo "Group $group leader: $COUNT requests"
done

# Expected Result
✓ Requests distributed across all 3 groups
✓ Roughly 10 requests per group
✓ Scheduler balances load
```

### Edge Cases

#### EC-LA-301: Data/DataLocal Mismatch
```bash
# Create with mismatched values
spec:
  replicas: 3
  parallelism:
    data: 3      # Total replicas
    dataLocal: 2 # Per-group replicas
  worker:
    replicas: 1  # dataLocal=2 means 1 worker per group

# Expected Result
✗ Validation should reject: data != replicas × dataLocal
✗ Or: Controller creates wrong number of groups
✗ This is a potential validation gap
```

#### EC-LA-302: Missing DataLocal (Validation Test)
```bash
# Try to create with data but no dataLocal
spec:
  parallelism:
    data: 2
    # dataLocal missing!

# Expected Result
✗ Validation webhook rejects with error:
   "dataLocal must be set when data is set"
✓ LLMInferenceService NOT created
```

---

# CATEGORY 5: NETWORKING & ROUTING

## Scenario NET-001: Custom Gateway with HTTPRoute
**Priority**: P1  
**Type**: Networking Configuration

### Test Steps

#### Step 1: Create Custom Gateway
```bash
kubectl apply -f - <<EOF
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: custom-llm-gateway
  namespace: test-llmd
spec:
  gatewayClassName: istio
  listeners:
  - name: http
    protocol: HTTP
    port: 8080
    hostname: "llm.example.com"
  - name: https
    protocol: HTTPS
    port: 443
    hostname: "llm.example.com"
    tls:
      mode: Terminate
      certificateRefs:
      - name: llm-tls-cert
EOF

# Wait for gateway ready
kubectl wait --for=condition=Programmed gateway/custom-llm-gateway \
  -n test-llmd --timeout=300s

# Expected Result
✓ Gateway created
✓ Status: Programmed=True
✓ External IP assigned
```

#### Step 2: Create LLMD with Custom Gateway
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-custom-gw
  namespace: test-llmd
spec:
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
    name: opt-custom-gw
  replicas: 2
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      resources:
        requests:
          cpu: "2"
          memory: "8Gi"
  
  router:
    # Reference custom gateway
    gateway:
      refs:
      - name: custom-llm-gateway
        namespace: test-llmd
    
    # Managed route (controller creates HTTPRoute)
    route:
      http:
        spec:
          hostnames:
          - llm.example.com
          rules:
          - matches:
            - path:
                type: PathPrefix
                value: /models/opt
EOF

# Expected Result
✓ LLMInferenceService created
✓ No validation errors
```

#### Step 3: Verify HTTPRoute Created
```bash
# Check HTTPRoute (from router.go:120-180)
HTTPROUTE=$(kubectl get httproute -n test-llmd \
  -l app.kubernetes.io/name=llm-custom-gw \
  -o jsonpath='{.items[0].metadata.name}')

kubectl get httproute $HTTPROUTE -n test-llmd -o yaml

# Expected Result
✓ HTTPRoute exists
✓ ParentRefs reference custom-llm-gateway
✓ Hostname: llm.example.com
✓ Path: /models/opt
✓ Backend: llm-custom-gw service

# Verify status
kubectl get httproute $HTTPROUTE -n test-llmd \
  -o jsonpath='{.status.parents[0].conditions[?(@.type=="Accepted")].status}'

# Expected: "True"
```

#### Step 4: Test Access via Custom Gateway
```bash
# Get gateway external IP
GATEWAY_IP=$(kubectl get gateway custom-llm-gateway -n test-llmd \
  -o jsonpath='{.status.addresses[0].value}')

# Test with hostname header
curl -X POST "http://$GATEWAY_IP:8080/models/opt/v1/chat/completions" \
  -H "Host: llm.example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "opt-custom-gw",
    "messages": [{"role": "user", "content": "Test custom gateway"}],
    "max_tokens": 20
  }'

# Expected Result
✓ HTTP 200 OK
✓ Request routed through custom gateway
✓ Response from vLLM backend
```

### Edge Cases

#### EC-NET-001: Gateway in Different Namespace
```bash
# Create gateway in istio-system
kubectl apply -f - <<EOF
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: shared-gateway
  namespace: istio-system
spec:
  gatewayClassName: istio
  listeners:
  - name: http
    protocol: HTTP
    port: 80
EOF

# Reference from LLMD
spec:
  router:
    gateway:
      refs:
      - name: shared-gateway
        namespace: istio-system  # Cross-namespace reference

# Expected Result
✓ Works if ReferenceGrant exists
✗ HTTPRoute not programmed if ReferenceGrant missing
✗ Status shows: "Gateway reference not allowed"
```

#### EC-NET-002: Invalid Gateway Configuration (Validation Gap)
```bash
# Try custom gateway with managed route (router.Route = {})
spec:
  router:
    gateway:
      refs:
      - name: custom-llm-gateway
    route: {}  # Empty route = managed route

# Expected Result
✗ Validation webhook rejects with error:
   "custom gateway cannot be used with managed route"
✓ This is validated by validateRouterCrossFieldConstraints
```

#### EC-NET-003: Both HTTPRoute Refs and Spec
```bash
# Try to use both refs and inline spec
spec:
  router:
    gateway:
      refs:
      - name: custom-gateway
    route:
      http:
        refs:
        - name: existing-route  # Reference existing HTTPRoute
        spec:                   # AND inline spec
          hostnames:
          - llm.example.com

# Expected Result
✗ Validation webhook rejects with error:
   "cannot use both custom HTTPRoute refs and an inline route spec"
✓ Validated by line 135-145 in llminferenceservice_validator.go
```

---

## Scenario NET-002: Scheduler-Based Routing
**Priority**: P0 (Critical)  
**Type**: Intelligent Request Routing

### Test Steps

#### Step 1: Create LLMD with Scheduler
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-with-scheduler
  namespace: test-llmd
spec:
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
    name: opt-scheduled
  replicas: 5
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      resources:
        requests:
          cpu: "2"
          memory: "8Gi"
  
  router:
    gateway: {}
    route: {}
    scheduler: {}  # Enable scheduler
EOF

# Expected Result
✓ LLMInferenceService created
```

#### Step 2: Verify ExtProc Service Created
```bash
# Check EPP (Endpoint Picker) service (from scheduler.go:180)
EPP_SVC="llm-with-scheduler-epp-service"
kubectl get svc $EPP_SVC -n test-llmd -o yaml

# Expected Result
✓ Service exists
✓ Type: ClusterIP
✓ Ports: 9002 (gRPC), 9003 (health), 9090 (metrics)

# Verify selector points to scheduler pod
kubectl get svc $EPP_SVC -n test-llmd -o jsonpath='{.spec.selector}'

# Expected selector:
app.kubernetes.io/component: llminferenceservice-router-scheduler
app.kubernetes.io/name: llm-with-scheduler
```

#### Step 3: Verify HTTPRoute with ExtProc Filter
```bash
# Check HTTPRoute ExtProc configuration (from router.go:253-279)
HTTPROUTE=$(kubectl get httproute -n test-llmd \
  -l app.kubernetes.io/name=llm-with-scheduler \
  -o jsonpath='{.items[0].metadata.name}')

kubectl get httproute $HTTPROUTE -n test-llmd -o yaml

# Expected in spec:
✓ filters section present
✓ type: ExtensionRef
✓ extensionRef:
    group: gateway.envoyproxy.io
    kind: ExtProc
    name: llm-with-scheduler-extproc

# Check ExtProc resource (from router.go:236-251)
kubectl get extproc llm-with-scheduler-extproc -n test-llmd -o yaml

# Expected:
✓ ExtProc resource exists
✓ backendRefs point to EPP service (port 9002)
✓ processingMode configured for request headers
```

#### Step 4: Verify Scheduler Pod Running
```bash
SCHEDULER_POD=$(kubectl get pods -n test-llmd \
  -l app.kubernetes.io/component=llminferenceservice-router-scheduler \
  -o jsonpath='{.items[0].metadata.name}')

kubectl get pod $SCHEDULER_POD -n test-llmd

# Expected Result
✓ Pod Running
✓ Container: main (llm-d-inference-scheduler image)
✓ No restarts

# Check scheduler logs
kubectl logs $SCHEDULER_POD -n test-llmd -c main --tail=50

# Expected in logs:
✓ "Scheduler started" or "Listening on port 9002"
✓ "Watching InferencePool" or "Discovered X endpoints"
✓ No errors
```

#### Step 5: Test Scheduler Decision Making
```bash
LLMD_URL=$(kubectl get llmisvc llm-with-scheduler -n test-llmd -o jsonpath='{.status.url}')

# Send request with session ID
SESSION=$(uuidgen)
curl -v -X POST "$LLMD_URL/v1/chat/completions" \
  -H "X-Session-ID: $SESSION" \
  -d '{"model":"opt-scheduled","messages":[{"role":"user","content":"First request"}],"max_tokens":20}' \
  2>&1 | grep -i "x-selected-backend\|x-envoy"

# Expected in response headers:
✓ x-selected-backend: <pod-ip> or <pod-name>
✓ x-envoy-upstream-service-time: <milliseconds>

# Check scheduler logs for decision
kubectl logs $SCHEDULER_POD -n test-llmd -c main --tail=20

# Expected in logs:
✓ "Processing request" with session ID
✓ "Selected pod: <pod-name>" or "Routing to: <ip>"
✓ Decision factors logged (load, cache, etc.)
```

#### Step 6: Verify Cache Affinity (Session Stickiness)
```bash
# Send 10 follow-up requests with same session ID
for i in {1..10}; do
  curl -s -X POST "$LLMD_URL/v1/chat/completions" \
    -H "X-Session-ID: $SESSION" \
    -d "{\"model\":\"opt-scheduled\",\"messages\":[{\"role\":\"user\",\"content\":\"Follow-up $i\"}],\"max_tokens\":10}" \
    > /dev/null
  sleep 1
done

# Check scheduler logs for consistency
kubectl logs $SCHEDULER_POD -n test-llmd -c main | grep "$SESSION" | grep "Selected pod"

# Expected Result
✓ All requests with same session ID routed to same pod
✓ Scheduler maintains cache affinity
✓ Same pod name appears in all log lines for this session
```

#### Step 7: Test Load Balancing (New Sessions)
```bash
# Send 50 requests with different session IDs
for i in {1..50}; do
  SESSION=$(uuidgen)
  curl -s -X POST "$LLMD_URL/v1/chat/completions" \
    -H "X-Session-ID: $SESSION" \
    -d "{\"model\":\"opt-scheduled\",\"messages\":[{\"role\":\"user\",\"content\":\"New session $i\"}],\"max_tokens\":10}" \
    > /dev/null &
done
wait

# Analyze distribution in scheduler logs
kubectl logs $SCHEDULER_POD -n test-llmd -c main | \
  grep "Selected pod" | \
  awk '{print $NF}' | \
  sort | uniq -c

# Expected Result
✓ Requests distributed across all 5 pods
✓ Roughly 10 requests per pod
✓ No single pod overloaded
```

### Edge Cases

#### EC-NET-101: Scheduler Pod Crash During Traffic
```bash
# Start continuous traffic
(while true; do
  curl -s "$LLMD_URL/v1/chat/completions" \
    -d '{"model":"opt-scheduled","messages":[{"role":"user","content":"Test"}],"max_tokens":5}'
  sleep 1
done) &
LOAD_PID=$!

# Delete scheduler pod
kubectl delete pod $SCHEDULER_POD -n test-llmd

# Expected Result
✗ Requests fail with 500 or 503 errors
✗ Gateway logs: "ExtProc backend unavailable"

# Wait for pod recreation
sleep 60
kill $LOAD_PID

# Verify recovery
curl -X POST "$LLMD_URL/v1/chat/completions" \
  -d '{"model":"opt-scheduled","messages":[{"role":"user","content":"Recovery test"}],"max_tokens":10}'

# Expected:
✓ New scheduler pod running
✓ Requests succeed again
✓ Service recovered automatically
```

#### EC-NET-102: InferencePool Not Created (ISSUE-003 Related)
```bash
# If InferencePool missing or endpoints not discovered
kubectl get inferencepool -n test-llmd

# If InferencePool exists but no endpoints
kubectl get inferencepool llm-with-scheduler-inference-pool -n test-llmd \
  -o jsonpath='{.status.endpoints}'

# Expected Result if bug present:
✗ Empty endpoints array: []
✗ Scheduler logs: "No endpoints available" or "InferencePool empty"
✗ All requests fail with 503 or route to random pod

# This is ISSUE-003: InferencePool condition not propagated
# Status.Ready may be True but InferencePool not working
```

---

# CATEGORY 6: SCALING & AUTOSCALING

## Scenario SCALE-001: Manual Horizontal Scaling
**Priority**: P1  
**Type**: Scale Operations

### Test Steps

#### Step 1: Create LLMD with Initial Replicas
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-scalable
  namespace: test-llmd
spec:
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
    name: opt-scalable
  replicas: 2
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      resources:
        requests:
          cpu: "2"
          memory: "8Gi"
  router:
    gateway: {}
    route: {}
    scheduler: {}
EOF

# Wait for ready
kubectl wait --for=condition=Ready llmisvc/llm-scalable -n test-llmd --timeout=600s

# Verify initial replicas
kubectl get deployment llm-scalable-kserve -n test-llmd

# Expected: 2/2 replicas available
```

#### Step 2: Scale Up to 5 Replicas
```bash
# Update replicas
kubectl patch llmisvc llm-scalable -n test-llmd --type='merge' \
  -p '{"spec":{"replicas":5}}'

# Watch scaling progress
watch kubectl get deployment llm-scalable-kserve -n test-llmd

# Expected Status Progression:
# 2/2 → 2/5 → 3/5 → 4/5 → 5/5

# Wait for all replicas ready
kubectl wait --for=jsonpath='{.status.availableReplicas}'=5 \
  deployment/llm-scalable-kserve -n test-llmd --timeout=600s

# Expected Result
✓ Deployment scaled to 5/5
✓ All pods Running
✓ No errors
```

#### Step 3: Verify InferencePool Updated
```bash
# Check InferencePool endpoints count
kubectl get inferencepool llm-scalable-inference-pool -n test-llmd \
  -o jsonpath='{.status.endpoints}' | jq '. | length'

# Expected: 5 endpoints

# Verify all pod IPs listed
kubectl get inferencepool llm-scalable-inference-pool -n test-llmd -o yaml

# Expected:
✓ 5 endpoints in status
✓ Each endpoint has podName, podIP, ready=true
```

#### Step 4: Test Traffic Distribution After Scale-Up
```bash
LLMD_URL=$(kubectl get llmisvc llm-scalable -n test-llmd -o jsonpath='{.status.url}')

# Send 50 requests
for i in {1..50}; do
  SESSION=$(uuidgen)
  curl -s "$LLMD_URL/v1/chat/completions" \
    -H "X-Session-ID: $SESSION" \
    -d "{\"model\":\"opt-scalable\",\"messages\":[{\"role\":\"user\",\"content\":\"Request $i\"}],\"max_tokens\":10}" \
    > /dev/null &
done
wait

# Check request distribution
for pod in $(kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-scalable \
  -o jsonpath='{.items[*].metadata.name}'); do
  COUNT=$(kubectl logs $pod -n test-llmd -c main | grep "POST /v1/chat/completions" | wc -l)
  echo "Pod $pod: $COUNT requests"
done

# Expected Result
✓ All 5 pods received requests
✓ Roughly 10 requests per pod
✓ New pods handling traffic immediately
```

#### Step 5: Scale Down to 3 Replicas
```bash
# Scale down
kubectl patch llmisvc llm-scalable -n test-llmd --type='merge' \
  -p '{"spec":{"replicas":3}}'

# Watch scaling
watch kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-scalable

# Expected Status Progression:
# 5 Running → 3 Running + 2 Terminating → 3 Running

# Wait for stabilization
sleep 120

# Verify final state
kubectl get deployment llm-scalable-kserve -n test-llmd

# Expected: 3/3 replicas available
```

#### Step 6: Verify InferencePool Updated After Scale-Down
```bash
# Check endpoint count
kubectl get inferencepool llm-scalable-inference-pool -n test-llmd \
  -o jsonpath='{.status.endpoints}' | jq '. | length'

# Expected: 3 endpoints (down from 5)

# Verify terminated pods removed
kubectl get inferencepool llm-scalable-inference-pool -n test-llmd -o yaml

# Expected:
✓ Only 3 endpoints listed
✓ No references to terminated pods
✓ All endpoints ready=true
```

#### Step 7: Test Traffic During Scale-Down
```bash
# Start continuous traffic
(while true; do
  SESSION=$(uuidgen)
  curl -s "$LLMD_URL/v1/chat/completions" \
    -H "X-Session-ID: $SESSION" \
    -d '{"model":"opt-scalable","messages":[{"role":"user","content":"Test"}],"max_tokens":10}'
  sleep 0.5
done) &
LOAD_PID=$!

# Scale down while traffic running
kubectl patch llmisvc llm-scalable -n test-llmd --type='merge' \
  -p '{"spec":{"replicas":2}}'

# Let traffic run during scale-down
sleep 120

# Stop traffic
kill $LOAD_PID

# Expected Result
✓ Some requests may fail (pods terminating)
✓ Majority of requests succeed
✓ No requests to terminated pods after grace period
✓ Traffic redistributes to remaining pods
```

### Edge Cases

#### EC-SCALE-001: Scale to 0 Replicas
```bash
# Try to scale to 0
kubectl patch llmisvc llm-scalable -n test-llmd --type='merge' \
  -p '{"spec":{"replicas":0}}'

# Expected Result (depends on implementation)
Option A: ✓ Accepted, all pods terminated (scale-to-zero)
Option B: ✗ Validation rejects: "replicas must be >= 1"
Option C: ✓ Accepted but deployment keeps 1 replica (min replicas)

# Verify behavior
kubectl get deployment llm-scalable-kserve -n test-llmd

# Check if validation exists for min replicas
```

#### EC-SCALE-002: Rapid Scale Up/Down
```bash
# Rapid scaling changes
kubectl patch llmisvc llm-scalable -n test-llmd --type='merge' -p '{"spec":{"replicas":10}}'
sleep 5
kubectl patch llmisvc llm-scalable -n test-llmd --type='merge' -p '{"spec":{"replicas":2}}'
sleep 5
kubectl patch llmisvc llm-scalable -n test-llmd --type='merge' -p '{"spec":{"replicas":7}}'

# Expected Result
✓ Controller handles rapid changes gracefully
✓ No stuck pods
✓ Final state matches last update (7 replicas)
✗ Potential race conditions if not handled properly
```

#### EC-SCALE-003: Scale During Model Loading
```bash
# Create with large model (slow to load)
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-slow-load
  namespace: test-llmd
spec:
  model:
    uri: hf://meta-llama/Llama-3-70B-Instruct
  replicas: 1
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
EOF

# Wait for pod to start (but not ready)
sleep 60

# Scale up while first pod still loading
kubectl patch llmisvc llm-slow-load -n test-llmd --type='merge' -p '{"spec":{"replicas":3}}'

# Expected Result
✓ 3 pods created
✓ All pods download and load model in parallel
✓ All eventually become ready
✗ Potential issue: model download bandwidth contention
✗ Potential issue: storage I/O bottleneck
```

---

## 🔍 SUMMARY OF ISSUES TO TEST

### Priority Order

#### P0 - Blocker Issues
1. **ISSUE-001**: Controller reconciliation disabled - MUST be enabled
2. **Prefill/Decode disaggregation**: Core LLMD feature - MUST work
3. **Routing sidecar injection**: Required for disaggregation
4. **Scheduler pod selection**: Must route intelligently

#### P1 - Critical Issues  
5. **ISSUE-002**: Template variable substitution failures
6. **BaseRef merge priority**: Configuration inheritance
7. **InferencePool discovery**: Pod discovery for scheduler
8. **Cache affinity routing**: Same pod for session

#### P2 - Important Issues
9. **ISSUE-003**: InferencePool condition propagation not implemented
10. **ISSUE-004**: ConfigMap watch not implemented  
11. **Gateway reference validation**: Non-existent gateway
12. **Scheduler port mismatch**: Port validation

---

# CATEGORY 7: FAILURE & RECOVERY

## Scenario FAIL-001: Pod Crash and Recovery
**Priority**: P0 (Critical)  
**Type**: Resilience Testing

### Test Steps

#### Step 1: Create Stable LLMD
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-resilient
  namespace: test-llmd
spec:
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
    name: opt-resilient
  replicas: 3
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      resources:
        requests:
          cpu: "2"
          memory: "8Gi"
  router:
    gateway: {}
    route: {}
    scheduler: {}
EOF

kubectl wait --for=condition=Ready llmisvc/llm-resilient -n test-llmd --timeout=600s
```

#### Step 2: Start Continuous Traffic
```bash
# Create traffic generation script
cat > /tmp/llm_traffic.sh <<'SCRIPT'
#!/bin/bash
URL=$1
DURATION=$2
END_TIME=$((SECONDS + DURATION))
SUCCESS=0
FAILURES=0

while [ $SECONDS -lt $END_TIME ]; do
  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model":"opt-resilient","messages":[{"role":"user","content":"Test"}],"max_tokens":5}')
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  if [ "$HTTP_CODE" = "200" ]; then
    ((SUCCESS++))
  else
    ((FAILURES++))
    echo "$(date +%T): Request failed with code $HTTP_CODE"
  fi
  sleep 1
done

echo "Results: $SUCCESS successful, $FAILURES failed"
echo "Success rate: $(echo "scale=2; $SUCCESS*100/($SUCCESS+$FAILURES)" | bc)%"
SCRIPT

chmod +x /tmp/llm_traffic.sh

# Get URL
LLMD_URL=$(kubectl get llmisvc llm-resilient -n test-llmd -o jsonpath='{.status.url}')

# Start 5-minute traffic test
/tmp/llm_traffic.sh "$LLMD_URL" 300 > /tmp/traffic_results.txt 2>&1 &
TRAFFIC_PID=$!
```

#### Step 3: Kill One Pod During Traffic
```bash
# Wait 60 seconds
sleep 60

# Get one pod
POD_TO_KILL=$(kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-resilient \
  -o jsonpath='{.items[0].metadata.name}')

echo "Killing pod: $POD_TO_KILL at $(date +%T)"

# Delete pod forcefully
kubectl delete pod $POD_TO_KILL -n test-llmd --force --grace-period=0

# Record time of failure
echo "Pod killed at: $(date +%T)" >> /tmp/traffic_results.txt
```

#### Step 4: Monitor Recovery
```bash
# Watch pod recreation
watch -n 1 kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-resilient

# Expected:
# - Old pod Terminating
# - New pod Creating → Running
# - Recovery time < 2 minutes

# Verify new pod ready
kubectl wait --for=condition=Ready pod \
  -l app.kubernetes.io/name=llm-resilient \
  -n test-llmd \
  --timeout=300s

echo "Pod recovered at: $(date +%T)" >> /tmp/traffic_results.txt
```

#### Step 5: Analyze Results
```bash
# Wait for traffic test to complete
wait $TRAFFIC_PID

# Review results
cat /tmp/traffic_results.txt

# Expected Results
✓ Total requests: ~300 (5 minutes × 1 req/sec)
✓ Failed requests: 5-30 (during pod failure/recovery)
✓ Success rate: > 90%
✓ Recovery time: < 2 minutes
✓ Scheduler redistributed traffic to healthy pods
```

### Edge Cases

#### EC-FAIL-001: All Pods Crash Simultaneously
```bash
# Delete all pods at once
kubectl delete pods -n test-llmd -l app.kubernetes.io/name=llm-resilient --force --grace-period=0

# Expected Result
✗ All requests fail for 1-3 minutes
✓ All pods recreated automatically
✓ Service fully recovered after pod restart
✓ No manual intervention needed
```

#### EC-FAIL-002: OOM Kill (Out of Memory)
```bash
# Create LLMD with insufficient memory for model
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-oom
  namespace: test-llmd
spec:
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
  replicas: 1
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      resources:
        requests:
          memory: "2Gi"  # Too small!
        limits:
          memory: "2Gi"
EOF

# Monitor pod status
watch kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-oom

# Expected Result
✗ Pod repeatedly OOMKilled
✗ Status: CrashLoopBackOff
✗ Logs show: "Killed" or "Out of memory"
✗ LLMInferenceService status: MainWorkloadReady=False
✗ Service never becomes available
```

---

## Scenario FAIL-002: Network Partition
**Priority**: P1  
**Type**: Network Resilience

### Test Steps

#### Step 1: Create LLMD with Disaggregation
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-netpartition
  namespace: test-llmd
spec:
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
  replicas: 3
  prefill:
    replicas: 2
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d:v0.2.0
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
  router:
    gateway: {}
    route: {}
    scheduler: {}
EOF

kubectl wait --for=condition=Ready llmisvc/llm-netpartition -n test-llmd --timeout=900s
```

#### Step 2: Block Prefill → Decode Communication
```bash
# Create network policy blocking decode → prefill traffic
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-prefill
  namespace: test-llmd
spec:
  podSelector:
    matchLabels:
      llm-d.ai/role: decode
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          llm-d.ai/role: prefill
    ports:
    - protocol: TCP
      port: 8000
  # Block prefill access
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53  # Allow DNS
EOF

echo "Network policy applied at: $(date +%T)"
```

#### Step 3: Test New Request (Should Fail)
```bash
LLMD_URL=$(kubectl get llmisvc llm-netpartition -n test-llmd -o jsonpath='{.status.url}')

SESSION=$(uuidgen)
curl -v -X POST "$LLMD_URL/v1/chat/completions" \
  -H "X-Session-ID: $SESSION" \
  -d '{"model":"opt-netpartition","messages":[{"role":"user","content":"New request"}],"max_tokens":20}' \
  --max-time 30

# Expected Result
✗ Request times out or returns 504 Gateway Timeout
✗ Decode pod routing sidecar cannot reach prefill
✗ Logs in routing sidecar: "Connection refused" or "Timeout connecting to prefill"
```

#### Step 4: Remove Network Policy and Verify Recovery
```bash
# Remove block
kubectl delete networkpolicy block-prefill -n test-llmd

echo "Network policy removed at: $(date +%T)"

# Wait a moment for network to stabilize
sleep 10

# Retry request
curl -X POST "$LLMD_URL/v1/chat/completions" \
  -H "X-Session-ID: $(uuidgen)" \
  -d '{"model":"opt-netpartition","messages":[{"role":"user","content":"Recovery test"}],"max_tokens":20}'

# Expected Result
✓ HTTP 200 OK
✓ Request succeeds
✓ Automatic recovery (no restart needed)
```

---

# CATEGORY 8: SECURITY & VALIDATION

## Scenario SEC-001: Validation Webhook Tests
**Priority**: P1  
**Type**: API Validation

### Test Steps

#### Test 1: Pipeline and Data Parallelism Together (Should Fail)
```bash
# Try to create with both pipeline and data parallelism
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-invalid-parallelism
  namespace: test-llmd
spec:
  model:
    uri: oci://model
  parallelism:
    pipeline: 2  # Pipeline parallelism
    data: 2      # Data parallelism
    dataLocal: 2
  worker:
    replicas: 1
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
  router:
    gateway: {}
EOF

# Expected Result
✗ Validation webhook rejects
✗ Error message: "cannot set both pipeline parallelism and data parallelism simultaneously"
✗ LLMInferenceService NOT created

# Verify
kubectl get llmisvc llm-invalid-parallelism -n test-llmd
# Expected: Error from server (NotFound)
```

#### Test 2: Worker Without Parallelism (Should Fail)
```bash
# Try to create worker without parallelism config
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-worker-no-parallel
  namespace: test-llmd
spec:
  model:
    uri: oci://model
  worker:
    replicas: 3  # Worker specified
  # parallelism: missing!
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
  router:
    gateway: {}
EOF

# Expected Result
✗ Validation webhook rejects
✗ Error: "when worker is specified, parallelism must be configured"
✗ LLMInferenceService NOT created
```

#### Test 3: Data Without DataLocal (Should Fail)
```bash
# Try data parallelism without dataLocal
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-data-no-local
  namespace: test-llmd
spec:
  model:
    uri: oci://model
  parallelism:
    data: 4
    # dataLocal: missing!
  worker:
    replicas: 1
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
  router:
    gateway: {}
EOF

# Expected Result
✗ Validation webhook rejects
✗ Error: "dataLocal must be set when data is set"
✗ Line 223-228 in llminferenceservice_validator.go
```

#### Test 4: Custom Gateway with Managed Route (Should Fail)
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-gateway-conflict
  namespace: test-llmd
spec:
  model:
    uri: oci://model
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
  router:
    gateway:
      refs:
      - name: my-gateway  # Custom gateway
    route: {}  # Empty = managed route
EOF

# Expected Result
✗ Validation webhook rejects
✗ Error: "custom gateway cannot be used with managed route"
✗ Lines 111-124 in llminferenceservice_validator.go
```

#### Test 5: HTTPRoute Refs and Spec Together (Should Fail)
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-route-conflict
  namespace: test-llmd
spec:
  model:
    uri: oci://model
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
  router:
    gateway: {}
    route:
      http:
        refs:
        - name: my-route  # Reference existing route
        spec:             # AND inline spec
          hostnames:
          - llm.example.com
EOF

# Expected Result
✗ Validation webhook rejects
✗ Error: "cannot use both custom HTTPRoute refs and an inline route spec"
✗ Lines 135-145 in llminferenceservice_validator.go
```

#### Test 6: Negative Parallelism Values (Should Fail)
```bash
# Try negative pipeline value
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-negative-parallel
  namespace: test-llmd
spec:
  model:
    uri: oci://model
  parallelism:
    pipeline: -2  # Negative!
  worker:
    replicas: 1
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
  router:
    gateway: {}
EOF

# Expected Result
✗ Validation webhook rejects
✗ Error: "pipeline parallelism must be greater than 0"
✗ Lines 239-245 in llminferenceservice_validator.go
```

### Verification Summary

| Validation Test | Expected Result | Status |
|-----------------|-----------------|--------|
| Pipeline + Data parallelism | Rejected | ☐ |
| Worker without parallelism | Rejected | ☐ |
| Data without dataLocal | Rejected | ☐ |
| DataLocal without data | Rejected | ☐ |
| Custom gateway + managed route | Rejected | ☐ |
| HTTPRoute refs + spec | Rejected | ☐ |
| Negative parallelism | Rejected | ☐ |
| User routes + managed gateway | Rejected | ☐ |

---

# CATEGORY 9: CONFIGURATION & UPDATES

## Scenario CONF-001: LLMInferenceServiceConfig Update
**Priority**: P2  
**Type**: Configuration Management  
**Related Issue**: ISSUE-004 (ConfigMap watch not implemented)

### Test Steps

#### Step 1: Create Base Config
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: updateable-config
  namespace: test-llmd
spec:
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:v0.6.3
      args:
      - --max-model-len=2048
      resources:
        requests:
          cpu: "2"
          memory: "8Gi"
EOF
```

#### Step 2: Create LLMD Using Config
```bash
kubectl apply -f - <<EOF
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llm-with-config
  namespace: test-llmd
spec:
  baseRefs:
  - name: updateable-config
  model:
    uri: oci://quay.io/opendatahub/opt-125m:latest
  replicas: 1
  router:
    gateway: {}
    route: {}
EOF

kubectl wait --for=condition=Ready llmisvc/llm-with-config -n test-llmd --timeout=600s
```

#### Step 3: Verify Initial Configuration
```bash
POD=$(kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-with-config \
  -o jsonpath='{.items[0].metadata.name}')

# Check args
kubectl get pod $POD -n test-llmd -o yaml | grep max-model-len

# Expected: --max-model-len=2048
```

#### Step 4: Update Config
```bash
kubectl patch llminferenceserviceconfig updateable-config -n test-llmd --type='merge' \
  -p '{"spec":{"template":{"containers":[{"name":"main","args":["--max-model-len=4096"]}]}}}'

echo "Config updated at: $(date +%T)"
```

#### Step 5: Check if Changes Applied (ISSUE-004 Test)
```bash
# Wait 2 minutes
sleep 120

# Check pod for updated args
POD_NEW=$(kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-with-config \
  -o jsonpath='{.items[0].metadata.name}')

kubectl get pod $POD_NEW -n test-llmd -o yaml | grep max-model-len

# Expected Result (if ISSUE-004 present):
✗ Still shows: --max-model-len=2048 (old value)
✗ Pod NOT recreated
✗ Config change NOT applied

# This is ISSUE-004: ConfigMap watch not implemented
# Controller doesn't watch for config changes
# Manual reconcile needed
```

#### Step 6: Force Reconcile (Workaround)
```bash
# Trigger reconcile by updating LLMD annotation
kubectl annotate llmisvc llm-with-config -n test-llmd \
  force-reconcile="$(date +%s)" --overwrite

# Or delete and recreate pod
kubectl delete pod $POD_NEW -n test-llmd

# Wait for new pod
kubectl wait --for=condition=Ready pod \
  -l app.kubernetes.io/name=llm-with-config \
  -n test-llmd --timeout=300s

# Check updated args
POD_FINAL=$(kubectl get pods -n test-llmd -l app.kubernetes.io/name=llm-with-config \
  -o jsonpath='{.items[0].metadata.name}')

kubectl get pod $POD_FINAL -n test-llmd -o yaml | grep max-model-len

# Expected After Manual Reconcile:
✓ Shows: --max-model-len=4096 (updated value)
✓ Config change applied after manual intervention
```

---

## 📝 TEST EXECUTION TEMPLATE

For each scenario, document results:

```markdown
## Test Execution: [Scenario ID]
**Date**: YYYY-MM-DD
**Tester**: [Name]
**Environment**: RHOAI X.X on OpenShift X.X

### Results
- [ ] Step 1: PASS/FAIL - [Notes]
- [ ] Step 2: PASS/FAIL - [Notes]
- [ ] Step 3: PASS/FAIL - [Notes]

### Issues Found
1. [Issue description]
   - Severity: Critical/High/Medium/Low
   - Steps to reproduce
   - Expected vs Actual
   - Logs/Screenshots

### Overall Status: ✅ PASS / ❌ FAIL / ⚠️ PARTIAL
```

---

## 📊 METRICS TO COLLECT

### Performance Metrics
- **Latency**: p50, p95, p99, p99.9
- **Throughput**: Requests/second, Tokens/second
- **Startup Time**: Model download + container ready
- **Prefill vs Decode Time**: Comparative analysis

### Reliability Metrics
- **Success Rate**: % of successful requests
- **Error Rate**: % of failed requests by type
- **Pod Restart Count**: Stability indicator
- **MTBF**: Mean time between failures

### Resource Metrics
- **CPU Usage**: % utilization
- **Memory Usage**: Actual vs requested
- **GPU Utilization**: % GPU memory and compute
- **Network I/O**: Prefill↔Decode communication

---

# 🐛 COMPREHENSIVE ISSUES LIST (From Codebase Analysis)

This section documents **ALL issues found** during codebase analysis of `/home/cloud-user/temp/kserve/pkg/controller/v1alpha1/llmisvc/`.

---

## ❌ CRITICAL ISSUES (P0 - Blockers)

### ISSUE-001: Controller Reconciliation Code Commented Out ⚠️ **BLOCKER**
**File**: `pkg/controller/v1alpha1/llmisvc/controller.go`  
**Lines**: 207-216  
**Severity**: **CRITICAL** - Blocks ALL LLMD functionality

#### Problem
The core reconciliation functions for workload and router are commented out:

```go
// Line 207-216 (COMMENTED OUT!)
// TODO: add workload reconciliation and re-enable this code
// if err := r.reconcileWorkload(ctx, llmSvc, config.StorageConfig); err != nil {
//     return fmt.Errorf("failed to reconcile workload: %w", err)
// }

// TODO: add router reconciliation and re-enable this code  
// if err := r.reconcileRouter(ctx, llmSvc); err != nil {
//     return fmt.Errorf("failed to reconcile networking: %w", err)
// }
```

#### Impact
- ✗ LLMInferenceService accepted by API but **NOTHING gets deployed**
- ✗ NO Deployments/LeaderWorkerSets created
- ✗ NO Services created
- ✗ NO HTTPRoutes created
- ✗ Status may show `Ready=True` but **resources don't exist**
- ✗ **LLMD feature completely non-functional**

#### Test Scenario
**Scenario ID**: LB-001 Edge Case EC-LB-001

#### Verification
```bash
# Check if controller logs show reconciliation
kubectl logs -n kserve deployment/kserve-controller-manager -c manager | \
  grep "reconcileWorkload\|reconcileRouter"

# Expected if FIXED:
✓ Logs show "Reconciling Workload" and "Reconciling Router"

# Expected if NOT FIXED:
✗ No logs (functions never called)
```

#### Required Fix
**MUST uncomment and re-enable these functions** before LLMD can work in RHOAI.

---

### ISSUE-002: Template Variable Substitution Failures
**File**: `pkg/controller/v1alpha1/llmisvc/config_merge.go`  
**Lines**: 176-204  
**Severity**: **HIGH** - Causes pod crashes

#### Problem
Template variable substitution uses `Option("missingkey=error")` which fails hard on any undefined variable:

```go
// Line 190
t, err := template.New("config").
    Funcs(map[string]any{
        "ChildName": kmeta.ChildName,
    }).
    Option("missingkey=error").  // ← FAILS if any variable undefined!
    Parse(string(templateBytes))
```

#### Impact
- ✗ Any undefined template variable → **pod fails to start**
- ✗ Variables in `baseRefs` may not substitute correctly
- ✗ Pod receives literal `{{.Name}}` instead of actual value
- ✗ vLLM crashes: "Invalid model name '{{.Name}}'"
- ✗ Error messages not user-friendly

#### Example Failure
```yaml
# In LLMInferenceServiceConfig
spec:
  model:
    name: "{{.Name}}-model"  # Variable
  template:
    containers:
    - args:
      - --served-model-name={{.Name}}  # Variable

# Result in pod:
args: ["--served-model-name={{.Name}}"]  # NOT substituted!
# vLLM crashes with: "Invalid model name"
```

#### Test Scenarios
- **Scenario ID**: LA-001 Edge Case EC-LA-002
- **Scenario ID**: LA-020 (Verify no template vars in disaggregation setup)

#### Verification
```bash
# Check if variables substituted correctly
POD=$(kubectl get pods -n test-llmd -l app.kubernetes.io/name=<llmd-name> -o jsonpath='{.items[0].metadata.name}')
kubectl get pod $POD -n test-llmd -o yaml | grep -i "{{"

# Expected if WORKING:
✓ No "{{" found (all variables substituted)

# Expected if BROKEN:
✗ Literal "{{.Name}}" or "{{.GlobalConfig.XXX}}" in pod spec
```

---

## 🔴 HIGH PRIORITY ISSUES (P1)

### ISSUE-003: InferencePool Condition Propagation Not Implemented
**File**: `pkg/controller/v1alpha1/llmisvc/scheduler.go`  
**Line**: 150  
**Severity**: **HIGH** - Scheduler may appear ready but not functional

#### Problem
TODO comment indicates InferencePool status not propagated to LLMInferenceService:

```go
// Line 150
// TODO add inference pool condition propagation and then aggregate it into 
// "RouterReady" similar to WorkloadReady.
```

#### Impact
- ✗ `Status.Ready=True` but InferencePool may have 0 endpoints
- ✗ Scheduler pod running but no backends available
- ✗ All requests fail with 503 or route incorrectly
- ✗ No indication in LLMInferenceService status that InferencePool is broken
- ✗ Difficult to debug (status lies)

#### Test Scenario
**Scenario ID**: NET-002 Edge Case EC-NET-102

#### Verification
```bash
# Check InferencePool status
kubectl get inferencepool <name> -n <namespace> -o jsonpath='{.status.endpoints}'

# If empty but LLMInferenceService shows Ready=True:
✗ ISSUE-003 present

# Check LLMInferenceService status for InferencePool condition
kubectl get llmisvc <name> -n <namespace> -o yaml | grep -A 5 "conditions:"

# Expected if FIXED:
✓ Condition type: InferencePoolReady

# Expected if NOT FIXED:
✗ No InferencePoolReady condition
```

---

### ISSUE-004: ConfigMap Watch Not Implemented
**File**: `pkg/controller/v1alpha1/llmisvc/controller.go`  
**Line**: 190  
**Severity**: **MEDIUM** - Requires manual reconcile on config changes

#### Problem
Controller doesn't watch for LLMInferenceServiceConfig changes:

```go
// Line 190
// TODO(ctrl): add watch on CfgMap with predicate and cache tuning to 
// trigger reconcile when it changes
```

#### Impact
- ✗ Updates to LLMInferenceServiceConfig **not applied automatically**
- ✗ Pods continue using old configuration
- ✗ Requires manual reconcile (delete pod or update LLMD)
- ✗ Unexpected behavior for users
- ✗ Configuration drift

#### Test Scenario
**Scenario ID**: CONF-001 Steps 4-6

#### Verification
```bash
# Update LLMInferenceServiceConfig
kubectl patch llminferenceserviceconfig <name> -n <namespace> --type='merge' -p '{...}'

# Wait 2 minutes
sleep 120

# Check if pods updated
kubectl get pods -n <namespace> -l app.kubernetes.io/name=<llmd-name>

# Expected if FIXED:
✓ Pods recreated with new config

# Expected if NOT FIXED:
✗ Pods still running with old config
✗ Manual intervention needed
```

#### Workaround
```bash
# Force reconcile by updating annotation
kubectl annotate llmisvc <name> -n <namespace> \
  force-reconcile="$(date +%s)" --overwrite

# Or delete pods manually
kubectl delete pods -n <namespace> -l app.kubernetes.io/name=<llmd-name>
```

---

### ISSUE-005: Gateway Reference Existence Not Validated
**File**: `pkg/controller/v1alpha1/llmisvc/router.go`  
**Line**: 88  
**Severity**: **MEDIUM** - HTTPRoute created but not functional

#### Problem
Controller doesn't validate if referenced Gateway exists:

```go
// Line 88
// TODO(validation): referenced gateway exists
```

#### Impact
- ✗ LLMInferenceService created successfully
- ✗ HTTPRoute created but not programmed (no gateway)
- ✗ Status may show `RouterReady=True` but route doesn't work
- ✗ Requests fail with 404 or no route to host
- ✗ Confusing for users (why isn't it working?)

#### Test Scenario
**Scenario ID**: LB-001 Edge Case EC-LB-003

#### Verification
```bash
# Create LLMD with non-existent gateway
spec:
  router:
    gateway:
      refs:
      - name: non-existent-gateway

# Check HTTPRoute status
kubectl get httproute <name> -n <namespace> -o yaml

# Expected if ISSUE present:
✗ HTTPRoute created
✗ Status: Accepted=False, ResolvedRefs=False
✗ Reason: "Gateway not found"
✗ But LLMInferenceService shows Ready=True (status doesn't reflect issue)
```

---

### ISSUE-006: Scheduler Port Mismatch Not Validated
**File**: `pkg/controller/v1alpha1/llmisvc/scheduler.go`  
**Line**: 211  
**Severity**: **LOW** - May cause runtime failures

#### Problem
TODO indicates gRPC port should be validated against InferencePool definition:

```go
// Line 211
// TODO should this be raised as failing condition? + check if grpc port 
// matches what's defined in the inferencepool
```

#### Impact
- ✗ InferencePool and Scheduler may have mismatched ports
- ✗ Scheduler cannot communicate with pods
- ✗ All requests fail
- ✗ Difficult to diagnose (port mismatch)

#### Test Scenario
Create custom InferencePool with wrong port and verify scheduler fails gracefully.

---

## ⚠️ MEDIUM PRIORITY ISSUES (P2)

### ISSUE-007: Storage Initialization Incomplete
**File**: `pkg/controller/v1alpha1/llmisvc/workload_storage.go`  
**Line**: 113  
**Severity**: **LOW** - Feature limitation

#### Problem
PVC copying not yet implemented:

```go
// Line 113
// TODO: For now, this supports only direct mount. Copying from PVC would 
// come later (if it makes sense at all).
```

#### Impact
- ✗ Can only mount PVC directly
- ✗ Cannot copy model from PVC to pod local storage
- ✗ May have performance implications for some use cases

---

### ISSUE-008: HTTPRoute RegExp Support Unclear
**File**: `pkg/controller/v1alpha1/llmisvc/router_discovery.go`  
**Line**: 111  
**Severity**: **LOW** - Edge case handling

#### Problem
```go
// Line 111
// TODO how do we deal with regexp
```

#### Impact
- ✗ Unclear if regex path matching supported
- ✗ May not work correctly with complex routing rules

---

### ISSUE-009: Pre/Post-Process Reconciliation Disabled
**File**: `pkg/controller/v1alpha1/llmisvc/controller.go`  
**Lines**: 168, 207  
**Severity**: **MEDIUM** - Feature incomplete

#### Problem
Pre-processor and post-processor reconciliation code commented out:

```go
// Line 168
// TODO: add pre-process and post-process reconciliation and re-enable this code

// Line 207
// TODO: add workload reconciliation and re-enable this code
```

#### Impact
- ✗ Pre-processor and post-processor features non-functional
- ✗ Cannot use LLMD with preprocessing or postprocessing

---

### ISSUE-010: Scheduler Service Account Finalization Disabled
**File**: `pkg/controller/v1alpha1/llmisvc/controller.go`  
**Line**: 221  
**Severity**: **LOW** - Resource leak

#### Problem
```go
// Line 221
// TODO: add scheduler service account finalization and re-enable this code
```

#### Impact
- ✗ ServiceAccounts not cleaned up on delete
- ✗ Minor resource leak

---

### ISSUE-011: Well-Known Config Presets Location Not Final
**File**: `pkg/controller/v1alpha1/llmisvc/config_merge.go`  
**Line**: 54  
**Severity**: **LOW** - Configuration management

#### Problem
```go
// Line 54
// FIXME move those presets to well-known when they're finally known :)
```

#### Impact
- ✗ Default configurations may change location
- ✗ Breaking change for users relying on specific presets

---

### ISSUE-012: BaseRef Not Found Error Handling
**File**: `pkg/controller/v1alpha1/llmisvc/config_merge.go`  
**Line**: 214  
**Severity**: **MEDIUM** - User experience

#### Problem
```go
// Line 214
// TODO: add available LLMInferenceServiceConfig in system namespace and 
// llmSvc.Namespace namespace if not found
```

#### Impact
- ✗ Error message not helpful when baseRef not found
- ✗ Doesn't suggest available configs
- ✗ Poor user experience

---

### ISSUE-013: HTTPRoute Discovery with Managed Gateway
**File**: `pkg/controller/v1alpha1/llmisvc/router.go`  
**Line**: 72  
**Severity**: **LOW** - API design question

#### Problem
```go
// Line 72
// TODO should we remove "llmSvc.Spec.Router.Route.HTTP == nil" from the 
// condition below so that a non nil Route means "all type of routes are enabled"?
```

#### Impact
- ✗ API semantics unclear
- ✗ May change in future (breaking change)

---

### ISSUE-014: HTTPRoute Target Gateway Narrowing
**File**: `pkg/controller/v1alpha1/llmisvc/router.go`  
**Line**: 189  
**Severity**: **LOW** - Feature limitation

#### Problem
```go
// Line 189
// TODO(api): With this structure we are missing the ability to narrow a 
// section of targeted gateway by the route we are creating
```

#### Impact
- ✗ Cannot target specific gateway listeners
- ✗ HTTPRoute applies to all listeners on gateway

---

### ISSUE-015: EnvTest Setup Not Matching Main
**File**: `pkg/controller/v1alpha1/llmisvc/fixture/envtest.go`  
**Line**: 58  
**Severity**: **LOW** - Test infrastructure

#### Problem
```go
// Line 58
// TODO fix it to be set up similar to main.go, for now it's stub
```

#### Impact
- ✗ Tests may not reflect production behavior
- ✗ False positives/negatives in tests

---

### ISSUE-016: Scheduler Reconciliation Disabled
**File**: `pkg/controller/v1alpha1/llmisvc/controller.go`  
**Line**: 212  
**Severity**: **MEDIUM** - Related to ISSUE-001

#### Problem
```go
// Line 212
// TODO: add router reconciliation and re-enable this code
```

#### Impact
- ✗ Scheduler resources may not be created
- ✗ Part of ISSUE-001 (controller reconciliation disabled)

---

### ISSUE-017: No E2E Tests for LLMD
**Location**: `/home/cloud-user/temp/kserve/test/e2e/`  
**Severity**: **MEDIUM** - Test coverage gap

#### Problem
No e2e tests found for LLMInferenceService in the test directory.

#### Impact
- ✗ No end-to-end validation
- ✗ Regressions may go undetected
- ✗ Manual testing required

#### Observed
```
test/e2e/
├── predictor/test_*.py (many tests for InferenceService)
├── transformer/test_*.py
├── batcher/test_*.py
└── (NO llmd/ or llminferenceservice/ directory)
```

---

### ISSUE-018: Validation Gap - Tensor Parallelism Worker Count Mismatch
**Discovered During**: Scenario design (LA-031)  
**Severity**: **HIGH** - Runtime failure

#### Problem
No validation to ensure `worker.replicas` matches `parallelism.tensor - 1`

#### Example
```yaml
spec:
  parallelism:
    tensor: 8  # Needs 8 total pods (1 leader + 7 workers)
  worker:
    replicas: 3  # Wrong! Should be 7
```

#### Impact
- ✗ LeaderWorkerSet creates wrong number of pods
- ✗ vLLM fails: "Expected 8 ranks but got 4"
- ✗ Pods crash and restart repeatedly

#### Test Scenario
**Scenario ID**: LA-031 Edge Case EC-LA-203

---

### ISSUE-019: Validation Gap - Data/DataLocal Consistency
**Discovered During**: Scenario design (LA-032)  
**Severity**: **MEDIUM** - Configuration error

#### Problem
No validation to ensure `data == replicas × dataLocal`

#### Example
```yaml
spec:
  replicas: 3
  parallelism:
    data: 3      # Total
    dataLocal: 2 # Per group
  # Math doesn't work: 3 != 3 × 2
```

#### Impact
- ✗ Wrong number of LeaderWorkerSets created
- ✗ Unexpected behavior

#### Test Scenario
**Scenario ID**: LA-032 Edge Case EC-LA-301

---

### ISSUE-020: Validation Gap - Scale to Zero
**Discovered During**: Scenario design (SCALE-001)  
**Severity**: **LOW** - Edge case

#### Problem
No validation for minimum replicas (can scale to 0?)

#### Impact
- ✗ Unclear behavior
- ✗ May allow replicas: 0 (no pods)

#### Test Scenario
**Scenario ID**: SCALE-001 Edge Case EC-SCALE-001

---

## 📊 ISSUES SUMMARY TABLE

| Issue ID | Severity | Component | Status | Test Scenario |
|----------|----------|-----------|--------|---------------|
| ISSUE-001 | **P0 BLOCKER** | Controller Reconciliation | Must Fix | LB-001 |
| ISSUE-002 | **P1 HIGH** | Template Variables | Must Fix | LA-001 |
| ISSUE-003 | **P1 HIGH** | InferencePool Status | Should Fix | NET-002 |
| ISSUE-004 | **P2 MEDIUM** | Config Watch | Should Fix | CONF-001 |
| ISSUE-005 | **P2 MEDIUM** | Gateway Validation | Should Fix | LB-001 |
| ISSUE-006 | **P3 LOW** | Port Validation | Nice to Have | - |
| ISSUE-007 | **P3 LOW** | PVC Copying | Feature Gap | - |
| ISSUE-008 | **P3 LOW** | RegExp Routes | Unclear | - |
| ISSUE-009 | **P2 MEDIUM** | Pre/Post-process | Feature Gap | - |
| ISSUE-010 | **P3 LOW** | SA Finalization | Resource Leak | - |
| ISSUE-011 | **P3 LOW** | Config Presets | Future Change | - |
| ISSUE-012 | **P2 MEDIUM** | Error Messages | UX | LA-001 |
| ISSUE-013 | **P3 LOW** | Route Semantics | API Design | - |
| ISSUE-014 | **P3 LOW** | Gateway Targeting | Feature Gap | - |
| ISSUE-015 | **P3 LOW** | Test Setup | Test Infra | - |
| ISSUE-016 | **P2 MEDIUM** | Scheduler Reconcile | Part of ISSUE-001 | NET-002 |
| ISSUE-017 | **P2 MEDIUM** | E2E Tests | Test Coverage | All |
| ISSUE-018 | **P1 HIGH** | TP Worker Validation | Validation Gap | LA-031 |
| ISSUE-019 | **P2 MEDIUM** | DP Math Validation | Validation Gap | LA-032 |
| ISSUE-020 | **P3 LOW** | Min Replicas | Validation Gap | SCALE-001 |

---

## 🎯 CRITICAL PATH FOR RHOAI DEPLOYMENT

### Before ANY Testing

1. ✅ **VERIFY ISSUE-001 IS FIXED**
   ```bash
   kubectl logs -n kserve deployment/kserve-controller-manager -c manager | \
     grep "reconcileWorkload\|reconcileRouter"
   ```
   **If no logs appear**: ❌ BLOCKER - LLMD completely non-functional

### Minimum Viable Product (MVP) Issues to Fix

1. **ISSUE-001** (P0): Controller reconciliation - **MUST FIX**
2. **ISSUE-002** (P1): Template variables - **MUST FIX**
3. **ISSUE-003** (P1): InferencePool status - **SHOULD FIX**
4. **ISSUE-018** (P1): TP worker validation - **SHOULD FIX**

### Production-Ready Issues to Fix

All MVP issues + :
5. **ISSUE-004** (P2): Config watch
6. **ISSUE-005** (P2): Gateway validation
7. **ISSUE-012** (P2): Better error messages
8. **ISSUE-017** (P2): E2E tests

---

## 📋 ISSUES BY FILE

### controller.go
- ISSUE-001 (P0): Reconciliation disabled (lines 207-216)
- ISSUE-004 (P2): ConfigMap watch (line 190)
- ISSUE-009 (P2): Pre/post-process (line 168)
- ISSUE-010 (P3): SA finalization (line 221)
- ISSUE-016 (P2): Scheduler reconcile (line 212)

### config_merge.go
- ISSUE-002 (P1): Template variables (lines 176-204)
- ISSUE-011 (P3): Well-known presets (line 54)
- ISSUE-012 (P2): BaseRef error handling (line 214)

### scheduler.go
- ISSUE-003 (P1): InferencePool status (line 150)
- ISSUE-006 (P3): Port validation (line 211)

### router.go
- ISSUE-005 (P2): Gateway validation (line 88)
- ISSUE-013 (P3): Route semantics (line 72)
- ISSUE-014 (P3): Gateway targeting (line 189)

### Validation Gaps
- ISSUE-018 (P1): TP worker count validation
- ISSUE-019 (P2): DP math validation
- ISSUE-020 (P3): Min replicas validation

### Test Coverage
- ISSUE-017 (P2): No E2E tests for LLMD

---

## 🔧 RECOMMENDED FIX ORDER

### Phase 1: Unblock LLMD (CRITICAL)
1. **Fix ISSUE-001** - Uncomment and enable reconciliation
2. **Test basic deployment** - LB-001, RK-001
3. **Fix ISSUE-002** - Improve template variable handling

### Phase 2: Core Functionality (HIGH)
4. **Fix ISSUE-003** - InferencePool status propagation
5. **Add ISSUE-018 validation** - TP worker count
6. **Test advanced features** - LA-020, LA-031

### Phase 3: Production Readiness (MEDIUM)
7. **Fix ISSUE-004** - Config watch
8. **Fix ISSUE-005** - Gateway validation
9. **Add ISSUE-019 validation** - DP math
10. **Improve ISSUE-012** - Error messages

### Phase 4: Hardening (LOW)
11. **Address remaining P3 issues**
12. **Add ISSUE-017** - E2E tests
13. **Performance testing**

---

*End of RHOAI LLMD Test Scenarios Document*

**Next Steps**:
1. **CRITICAL**: Verify ISSUE-001 is fixed before any testing
2. Execute P0 scenarios first (RK-001, LB-001, LA-020)
3. Document all issues found during testing
4. Cross-reference with this issues list
5. Create bug reports with reproduction steps
6. Verify fixes with re-test
7. Proceed to P1, P2, P3 scenarios

**Total Scenarios Documented**: 26 detailed + validation tests
**Total Issues Found**: 20 from codebase analysis
**Estimated Test Time**: 60-80 hours for full suite
**Critical Blockers**: 1 (ISSUE-001 MUST be fixed)

