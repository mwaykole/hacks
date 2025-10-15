# LLMD & KServe Complete Textbook - Part 4 (FINAL)
## Hands-On Labs, Troubleshooting, Production Guide, and Appendices

---

# Part V: Hands-On Labs

---

## Chapter 18: Lab 1 - Your First LLMD Service

### Lab Overview

**Goal:** Deploy a simple LLM service and make your first inference request

**Prerequisites:**
- Kubernetes cluster with GPU nodes
- kubectl configured
- KServe installed
- At least 1 NVIDIA GPU available

**Time:** 30 minutes

### Step 1: Create Namespace

```bash
kubectl create namespace llm-lab
kubectl config set-context --current --namespace=llm-lab
```

### Step 2: Create Simple LLMD Service

Create `lab1-simple-llm.yaml`:

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-8b-simple
  namespace: llm-lab
spec:
  model:
    uri: hf://meta-llama/Llama-3.2-1B-Instruct  # Small model for testing
    name: llama-1b
  
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
        limits:
          nvidia.com/gpu: "1"
          cpu: "4"
          memory: "16Gi"
      env:
      - name: HF_TOKEN
        valueFrom:
          secretKeyRef:
            name: hf-token  # Create this if needed
            key: token
            optional: true
  
  router:
    gateway:
      refs:
      - name: llm-gateway
        namespace: istio-system
    route:
      http: {}
```

Apply:

```bash
kubectl apply -f lab1-simple-llm.yaml
```

### Step 3: Monitor Deployment

**Watch the LLMInferenceService:**

```bash
kubectl get llmisvc llama-8b-simple -w
```

Expected output:
```
NAME              READY   URL
llama-8b-simple   False   
llama-8b-simple   False   
llama-8b-simple   True    https://gateway/llm-lab/llama-8b-simple
```

**Check pods:**

```bash
kubectl get pods -l app.kubernetes.io/name=llama-8b-simple
```

Expected:
```
NAME                                    READY   STATUS    RESTARTS   AGE
llama-8b-simple-kserve-abc123-xyz       2/2     Running   0          2m
```

**Check pod details:**

```bash
kubectl describe pod llama-8b-simple-kserve-abc123-xyz
```

Look for:
- Init Container: `storage-initializer` (downloads model)
- Container: `main` (vLLM server)
- GPU allocation: `nvidia.com/gpu: 1`

**Check logs:**

```bash
# Storage initializer logs
kubectl logs llama-8b-simple-kserve-abc123-xyz -c storage-initializer

# vLLM logs
kubectl logs llama-8b-simple-kserve-abc123-xyz -c main -f
```

Wait for:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 4: Test the Service

**Get the service URL:**

```bash
GATEWAY_URL=$(kubectl get llmisvc llama-8b-simple -o jsonpath='{.status.url}')
echo $GATEWAY_URL
```

**Test with curl:**

```bash
curl -X POST $GATEWAY_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-1b",
    "messages": [
      {"role": "user", "content": "Say hello in 5 words"}
    ],
    "max_tokens": 20,
    "temperature": 0.7
  }'
```

Expected response:
```json
{
  "id": "chat-123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "llama-1b",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello there, nice to meet!"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 7,
    "total_tokens": 17
  }
}
```

**Test streaming:**

```bash
curl -X POST $GATEWAY_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-1b",
    "messages": [
      {"role": "user", "content": "Count from 1 to 5"}
    ],
    "stream": true
  }'
```

You should see tokens streaming!

### Step 5: Check Metrics

**vLLM metrics:**

```bash
kubectl port-forward svc/llama-8b-simple-kserve-svc 8000:8000
# In another terminal:
curl http://localhost:8000/metrics
```

Look for:
- `vllm:num_requests_running`
- `vllm:generation_tokens_total`
- `vllm:time_to_first_token_seconds`

### Step 6: Cleanup

```bash
kubectl delete llmisvc llama-8b-simple
```

**Lab Complete! ✅**

**What you learned:**
- How to create an LLMD service
- How to monitor deployment
- How to test inference
- How to check metrics

---

## Chapter 19: Lab 2 - Disaggregated Prefill/Decode

### Lab Overview

**Goal:** Deploy a production-style prefill/decode split service with scheduler

**Prerequisites:**
- Lab 1 completed
- At least 4 GPUs available (2 for prefill, 2 for decode)
- Gateway API and Scheduler installed

**Time:** 45 minutes

### Step 1: Create Config Template

First, let's create reusable configs:

`lab2-vllm-base-config.yaml`:

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: vllm-base-config
  namespace: llm-lab
spec:
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      command: ["vllm", "serve"]
      args:
      - /mnt/models
      - --port=8000
      - --dtype=bfloat16
      - --gpu-memory-utilization=0.9
      - --enable-prefix-caching
      - --max-model-len=4096
      env:
      - name: VLLM_LOGGING_LEVEL
        value: INFO
      volumeMounts:
      - name: shm
        mountPath: /dev/shm
    volumes:
    - name: shm
      emptyDir:
        medium: Memory
        sizeLimit: 4Gi
```

Apply:

```bash
kubectl apply -f lab2-vllm-base-config.yaml
```

### Step 2: Create Disaggregated Service

`lab2-disaggregated-llm.yaml`:

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-8b-pd
  namespace: llm-lab
spec:
  # Inherit base config
  baseRefs:
  - name: vllm-base-config
  
  model:
    uri: hf://meta-llama/Llama-3-8B-Instruct
    name: llama-8b
    criticality: Normal
  
  # Prefill workload (compute-intensive)
  prefill:
    replicas: 1  # Start with 1, scale later
    parallelism:
      tensor: 2  # 2 GPUs for prefill
    template:
      containers:
      - name: main
        env:
        - name: VLLM_PREFILL_MODE
          value: "true"
        resources:
          requests:
            nvidia.com/gpu: "2"
            cpu: "8"
            memory: "32Gi"
          limits:
            nvidia.com/gpu: "2"
  
  # Decode workload (memory-intensive)
  replicas: 2  # 2 decode pods
  parallelism:
    tensor: 1  # 1 GPU per decode pod
  template:
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "1"
          cpu: "4"
          memory: "16Gi"
        limits:
          nvidia.com/gpu: "1"
  
  # Enable scheduler for intelligent routing
  router:
    gateway:
      refs:
      - name: llm-gateway
        namespace: istio-system
    route:
      http: {}
    scheduler:
      pool:
        spec:
          selector:
            matchLabels:
              app.kubernetes.io/name: llama-8b-pd
          targetPortNumber: 8000
```

Apply:

```bash
kubectl apply -f lab2-disaggregated-llm.yaml
```

### Step 3: Monitor Deployment

**Watch all resources:**

```bash
# LLMInferenceService
kubectl get llmisvc llama-8b-pd -w

# Deployments
kubectl get deploy | grep llama-8b-pd

# Pods
kubectl get pods -l app.kubernetes.io/name=llama-8b-pd
```

Expected pods:
```
NAME                                           READY   STATUS    AGE
llama-8b-pd-kserve-prefill-abc123              2/2     Running   3m   ← Prefill
llama-8b-pd-kserve-workload-def456             3/3     Running   3m   ← Decode (note: 3 containers!)
llama-8b-pd-kserve-workload-ghi789             3/3     Running   3m   ← Decode
llama-8b-pd-kserve-router-scheduler-jkl012     1/1     Running   3m   ← Scheduler
```

**Check pod labels:**

```bash
kubectl get pods -l llm-d.ai/role=prefill --show-labels
kubectl get pods -l llm-d.ai/role=decode --show-labels
```

**Verify containers in decode pod:**

```bash
kubectl get pod llama-8b-pd-kserve-workload-def456 -o json | \
  jq '.spec.initContainers[].name, .spec.containers[].name'
```

Expected:
```
"storage-initializer"        ← Init
"llm-d-routing-sidecar"      ← Init (but restartPolicy: Always)
"main"                       ← Main container
```

### Step 4: Test Prefill/Decode Flow

**First request (triggers prefill):**

```bash
URL=$(kubectl get llmisvc llama-8b-pd -o jsonpath='{.status.url}')

time curl -X POST $URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-8b",
    "messages": [
      {"role": "user", "content": "Write a haiku about clouds"}
    ],
    "max_tokens": 50,
    "stream": true
  }' | tee /tmp/response1.txt
```

**Watch the flow:**

Terminal 1 (Scheduler logs):
```bash
kubectl logs -f deploy/llama-8b-pd-kserve-router-scheduler
```

Terminal 2 (Decode pod routing sidecar):
```bash
POD=$(kubectl get pod -l llm-d.ai/role=decode -o jsonpath='{.items[0].metadata.name}')
kubectl logs -f $POD -c llm-d-routing-sidecar
```

Look for:
```
[Scheduler] Received request, selecting pod...
[Scheduler] Selected: decode-pod-1 (score: 0.85)
[Sidecar] New conversation, forwarding to prefill
[Sidecar] Prefill returned first token: "White"
[Sidecar] Storing KV cache for session: sess-abc-123
[Sidecar] Continuing with local decode
```

**Second request (uses decode only):**

```bash
time curl -X POST $URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-8b",
    "messages": [
      {"role": "user", "content": "Write a haiku about clouds"},
      {"role": "assistant", "content": "White puffs drift slowly..."},
      {"role": "user", "content": "Write another about rain"}
    ],
    "max_tokens": 50
  }' | tee /tmp/response2.txt
```

Notice:
- **Second request is FASTER** (no prefill!)
- Sidecar logs show: "Using cached KV"

### Step 5: Observe Scheduler Metrics

```bash
kubectl port-forward svc/llama-8b-pd-epp-service 9090:9090
# In another terminal:
curl http://localhost:9090/metrics | grep scheduler
```

Look for:
```
scheduler_requests_total{profile="prefill"} 1
scheduler_requests_total{profile="decode"} 1
scheduler_pod_score{pod="decode-pod-0"} 2.4
scheduler_pod_score{pod="decode-pod-1"} 0.75
scheduler_cache_hits_total 1
scheduler_cache_misses_total 1
```

### Step 6: Scale Up

```bash
kubectl patch llmisvc llama-8b-pd --type merge -p '{
  "spec": {
    "replicas": 4,
    "prefill": {
      "replicas": 2
    }
  }
}'
```

Watch scaling:
```bash
kubectl get pods -l app.kubernetes.io/name=llama-8b-pd -w
```

### Step 7: Load Test

Install `hey` (HTTP load generator):
```bash
go install github.com/rakyll/hey@latest
```

Load test:
```bash
hey -z 30s -c 10 -m POST \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-8b","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}' \
  $URL/v1/chat/completions
```

Observe:
- Scheduler distributing load
- Decode pods sharing work
- Prefill pods handling new sessions

### Step 8: Cleanup

```bash
kubectl delete llmisvc llama-8b-pd
kubectl delete llmisvcc vllm-base-config
```

**Lab Complete! ✅**

**What you learned:**
- How to configure prefill/decode split
- How routing sidecar works
- How scheduler distributes load
- How to monitor and scale

---

## Chapter 20: Lab 3 - Production Deployment

### Lab Overview

**Goal:** Deploy a production-ready LLM service with all best practices

**Features:**
- Resource limits and QoS
- Health checks and readiness
- Monitoring and alerting
- High availability
- Security (TLS, RBAC)

**Time:** 60 minutes

### Step 1: Create Production Namespace

```bash
kubectl create namespace llm-prod

# Enable monitoring
kubectl label namespace llm-prod monitoring=enabled

# Create service account
kubectl create serviceaccount llm-sa -n llm-prod
```

### Step 2: Create TLS Secret

```bash
# Generate self-signed cert (or use real cert)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/tls.key \
  -out /tmp/tls.crt \
  -subj "/CN=llm-prod-service/O=llm-prod"

kubectl create secret tls llm-tls \
  --cert=/tmp/tls.crt \
  --key=/tmp/tls.key \
  -n llm-prod
```

### Step 3: Production Config Template

`prod-config.yaml`:

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceServiceConfig
metadata:
  name: prod-vllm-config
  namespace: llm-prod
spec:
  template:
    serviceAccountName: llm-sa
    
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      fsGroup: 1000
      seccompProfile:
        type: RuntimeDefault
    
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d:v0.2.0
      
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
        readOnlyRootFilesystem: false
      
      command: ["vllm", "serve"]
      args:
      - /mnt/models
      - --port=8000
      - --dtype=bfloat16
      - --gpu-memory-utilization=0.85  # Leave headroom
      - --enable-prefix-caching
      - --max-model-len=8192
      - --max-num-seqs=256
      - --trust-remote-code=false  # Security
      
      env:
      - name: VLLM_LOGGING_LEVEL
        value: INFO
      - name: VLLM_LOG_JSON
        value: "true"  # Structured logging
      
      # Readiness probe
      readinessProbe:
        httpGet:
          path: /health
          port: 8000
          scheme: HTTPS
        initialDelaySeconds: 60
        periodSeconds: 10
        timeoutSeconds: 5
        failureThreshold: 3
      
      # Liveness probe
      livenessProbe:
        httpGet:
          path: /health
          port: 8000
          scheme: HTTPS
        initialDelaySeconds: 120
        periodSeconds: 30
        timeoutSeconds: 10
        failureThreshold: 3
      
      # Resource limits (Guaranteed QoS)
      resources:
        requests:
          nvidia.com/gpu: "1"
          cpu: "4"
          memory: "16Gi"
        limits:
          nvidia.com/gpu: "1"
          cpu: "4"
          memory: "16Gi"
      
      volumeMounts:
      - name: shm
        mountPath: /dev/shm
      - name: tls-certs
        mountPath: /etc/tls
        readOnly: true
    
    volumes:
    - name: shm
      emptyDir:
        medium: Memory
        sizeLimit: 8Gi
    - name: tls-certs
      secret:
        secretName: llm-tls
```

Apply:
```bash
kubectl apply -f prod-config.yaml
```

### Step 4: Production Service

`prod-llm-service.yaml`:

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: llama-prod
  namespace: llm-prod
  labels:
    app: llm-service
    env: production
    tier: ml-inference
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
spec:
  baseRefs:
  - name: prod-vllm-config
  
  model:
    uri: hf://meta-llama/Llama-3-8B-Instruct
    name: llama-8b-prod
    criticality: Critical  # High priority
  
  # Prefill: High availability (2 replicas)
  prefill:
    replicas: 2
    parallelism:
      tensor: 4
    template:
      affinity:
        podAntiAffinity:  # Spread across nodes
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  llm-d.ai/role: prefill
              topologyKey: kubernetes.io/hostname
      containers:
      - name: main
        env:
        - name: VLLM_PREFILL_MODE
          value: "true"
        resources:
          requests:
            nvidia.com/gpu: "4"
            cpu: "16"
            memory: "64Gi"
          limits:
            nvidia.com/gpu: "4"
            cpu: "16"
            memory: "64Gi"
  
  # Decode: Horizontal scaling (min 4, can scale to 16)
  replicas: 4
  parallelism:
    tensor: 1
  template:
    affinity:
      podAntiAffinity:
        preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchLabels:
                llm-d.ai/role: decode
            topologyKey: kubernetes.io/hostname
    containers:
    - name: main
      resources:
        requests:
          nvidia.com/gpu: "1"
          cpu: "4"
          memory: "16Gi"
        limits:
          nvidia.com/gpu: "1"
          cpu: "4"
          memory: "16Gi"
  
  router:
    gateway:
      refs:
      - name: prod-gateway
        namespace: istio-system
    route:
      http:
        spec:
          rules:
          - matches:
            - path:
                type: PathPrefix
                value: /llm-prod/llama-prod
            filters:
            - type: URLRewrite
              urlRewrite:
                path:
                  type: ReplacePrefixMatch
                  replacePrefixMatch: /
    scheduler:
      pool: {}
```

Apply:
```bash
kubectl apply -f prod-llm-service.yaml
```

### Step 5: Setup Monitoring

**ServiceMonitor (if using Prometheus Operator):**

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: llama-prod-metrics
  namespace: llm-prod
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: llama-prod
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

**PrometheusRule (Alerting):**

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: llama-prod-alerts
  namespace: llm-prod
spec:
  groups:
  - name: llm-inference
    interval: 30s
    rules:
    - alert: LLMHighLatency
      expr: |
        histogram_quantile(0.95, 
          rate(vllm:time_to_first_token_seconds_bucket[5m])
        ) > 2.0
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High P95 TTFT latency"
        description: "P95 time-to-first-token is {{ $value }}s"
    
    - alert: LLMHighErrorRate
      expr: |
        rate(vllm:request_error_total[5m]) > 0.05
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "High error rate"
        description: "Error rate is {{ $value | humanizePercentage }}"
    
    - alert: LLMGPUMemoryHigh
      expr: |
        vllm:gpu_cache_usage_perc > 95
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "GPU memory near capacity"
```

### Step 6: Setup HPA (Horizontal Pod Autoscaler)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llama-prod-decode-hpa
  namespace: llm-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llama-prod-kserve
  minReplicas: 4
  maxReplicas: 16
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: vllm_num_requests_running
      target:
        type: AverageValue
        averageValue: "10"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50  # Scale up 50% at a time
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5min before scale down
      policies:
      - type: Pods
        value: 1  # Scale down 1 pod at a time
        periodSeconds: 120
```

### Step 7: Deploy Grafana Dashboard

```bash
# Import dashboard JSON
kubectl create configmap llm-dashboard \
  --from-file=dashboard.json=<(cat <<'EOF'
{
  "dashboard": {
    "title": "LLM Production Metrics",
    "panels": [
      {
        "title": "Requests/sec",
        "targets": [{
          "expr": "rate(vllm:generation_tokens_total[1m])"
        }]
      },
      {
        "title": "P95 TTFT",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(vllm:time_to_first_token_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "GPU Utilization",
        "targets": [{
          "expr": "vllm:gpu_cache_usage_perc"
        }]
      }
    ]
  }
}
EOF
) -n llm-prod
```

### Step 8: Production Testing

**Smoke test:**
```bash
URL=$(kubectl get llmisvc llama-prod -n llm-prod -o jsonpath='{.status.url}')
curl -X POST $URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-8b-prod","messages":[{"role":"user","content":"Test"}],"max_tokens":5}'
```

**Load test (30 min, realistic traffic):**
```bash
hey -z 30m -c 50 -q 10 -m POST \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-8b-prod","messages":[{"role":"user","content":"Tell me a fact"}],"max_tokens":50}' \
  $URL/v1/chat/completions > /tmp/load-test-results.txt
```

**Monitor during load test:**
```bash
watch -n 5 'kubectl top pod -n llm-prod | grep llama-prod'
watch -n 2 'kubectl get hpa -n llm-prod'
```

### Step 9: Verify Production Readiness

**Checklist:**
```bash
# ✓ All pods running
kubectl get pods -n llm-prod | grep llama-prod

# ✓ Readiness probes passing
kubectl get pods -n llm-prod -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# ✓ HPA configured
kubectl get hpa -n llm-prod

# ✓ Metrics available
kubectl port-forward -n llm-prod svc/llama-prod-kserve-svc 8000:8000
curl http://localhost:8000/metrics | grep vllm

# ✓ Alerts configured
kubectl get prometheusrule -n llm-prod

# ✓ No errors in logs
kubectl logs -n llm-prod -l app.kubernetes.io/name=llama-prod --tail=100 | grep -i error
```

**Lab Complete! ✅**

**What you learned:**
- Production-grade configuration
- Security best practices
- Monitoring and alerting
- Autoscaling
- High availability

---

# Part VI: Operations

---

## Chapter 22: Monitoring and Observability

### Metrics to Monitor

**1. Request Metrics**

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `vllm:num_requests_running` | Active requests | > 100 per pod |
| `vllm:num_requests_waiting` | Queued requests | > 50 |
| `vllm:request_error_total` | Failed requests | > 5% error rate |
| `vllm:request_success_total` | Successful requests | - |

**2. Latency Metrics**

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `vllm:time_to_first_token_seconds` | TTFT (P50, P95, P99) | P95 > 2s |
| `vllm:time_per_output_token_seconds` | TPOT (P50, P95, P99) | P95 > 100ms |
| `vllm:e2e_request_latency_seconds` | End-to-end latency | P95 > 10s |

**3. Resource Metrics**

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `vllm:gpu_cache_usage_perc` | KV cache usage | > 90% |
| `vllm:gpu_memory_usage_bytes` | GPU VRAM usage | > 90% of capacity |
| `container_gpu_utilization` | GPU compute usage | < 20% (underutilization) |

**4. Scheduler Metrics**

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `scheduler_requests_total` | Total scheduled | - |
| `scheduler_pod_score` | Pod scores | - |
| `scheduler_cache_hits_total` | Cache hits | Low hit rate |
| `scheduler_decision_duration_seconds` | Scheduling latency | > 10ms |

### Grafana Dashboards

**Overview Dashboard:**

```json
{
  "dashboard": {
    "title": "LLMD Overview",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [{
          "expr": "sum(rate(vllm:request_success_total[5m]))",
          "legendFormat": "Requests/sec"
        }]
      },
      {
        "id": 2,
        "title": "Latency Distribution",
        "type": "heatmap",
        "targets": [{
          "expr": "rate(vllm:time_to_first_token_seconds_bucket[5m])"
        }]
      },
      {
        "id": 3,
        "title": "Active Pods",
        "type": "stat",
        "targets": [{
          "expr": "count(up{job=\"llm-service\"})"
        }]
      },
      {
        "id": 4,
        "title": "GPU Memory Usage",
        "type": "gauge",
        "targets": [{
          "expr": "vllm:gpu_cache_usage_perc",
          "legendFormat": "Pod {{pod}}"
        }],
        "thresholds": [
          {"value": 0, "color": "green"},
          {"value": 80, "color": "yellow"},
          {"value": 90, "color": "red"}
        ]
      }
    ]
  }
}
```

### Logging Best Practices

**1. Structured Logging (JSON)**

```yaml
env:
- name: VLLM_LOG_JSON
  value: "true"
```

Output:
```json
{
  "timestamp": "2025-10-14T10:30:45.123Z",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "req-abc-123",
  "model": "llama-8b",
  "duration_ms": 1250,
  "tokens_generated": 45,
  "ttft_ms": 150
}
```

**2. Log Aggregation (Fluent Bit → Elasticsearch)**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
data:
  fluent-bit.conf: |
    [INPUT]
        Name tail
        Path /var/log/containers/*llama-prod*.log
        Parser docker
        Tag kube.*
    
    [FILTER]
        Name kubernetes
        Match kube.*
        Kube_URL https://kubernetes.default.svc:443
    
    [FILTER]
        Name parser
        Match kube.*
        Key_Name log
        Parser json
    
    [OUTPUT]
        Name es
        Match kube.*
        Host elasticsearch.logging.svc
        Port 9200
        Index llm-logs
```

**3. Log Queries (Useful patterns)**

```bash
# Find slow requests
kubectl logs -n llm-prod -l app=llama-prod | \
  jq 'select(.duration_ms > 5000)'

# Count errors by type
kubectl logs -n llm-prod -l app=llama-prod | \
  jq -r 'select(.level=="ERROR") | .error_type' | \
  sort | uniq -c

# Trace a specific request
kubectl logs -n llm-prod -l app=llama-prod | \
  jq 'select(.request_id=="req-abc-123")'
```

### Distributed Tracing (OpenTelemetry)

**Enable tracing in vLLM:**

```yaml
env:
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: "http://jaeger-collector:4317"
- name: OTEL_SERVICE_NAME
  value: "vllm-llama-prod"
```

**Trace spans:**
```
Request: chat/completions
├─ Span: tokenization (5ms)
├─ Span: scheduler.select_pod (2ms)
├─ Span: prefill.forward (150ms)
│  ├─ Span: attention.layer_0 (15ms)
│  ├─ Span: attention.layer_1 (15ms)
│  └─ ...
└─ Span: decode.generate (1200ms)
   ├─ Span: token_0 (30ms)
   ├─ Span: token_1 (30ms)
   └─ ...
```

---

## Chapter 23: Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Pods Stuck in Pending

**Symptoms:**
```bash
$ kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
llama-prod-kserve-abc123       0/2     Pending   0          5m
```

**Diagnosis:**
```bash
kubectl describe pod llama-prod-kserve-abc123
```

**Possible Causes:**

**1. No GPUs available**
```
Events:
  Warning  FailedScheduling  0/3 nodes available: 3 Insufficient nvidia.com/gpu
```

**Solution:**
```bash
# Check GPU capacity
kubectl describe node | grep -A 5 "nvidia.com/gpu"

# Scale down other workloads or add GPU nodes
```

**2. Resource requests too high**
```
Events:
  Warning  FailedScheduling  0/3 nodes available: 3 Insufficient memory
```

**Solution:**
```bash
# Reduce resource requests
kubectl patch llmisvc llama-prod --type merge -p '{
  "spec": {
    "template": {
      "containers": [{
        "name": "main",
        "resources": {
          "requests": {"memory": "8Gi"}
        }
      }]
    }
  }
}'
```

#### Issue 2: OOM (Out of Memory) Killed

**Symptoms:**
```bash
$ kubectl get pods
NAME                           READY   STATUS      RESTARTS   AGE
llama-prod-kserve-abc123       0/2     OOMKilled   5          10m
```

**Diagnosis:**
```bash
kubectl describe pod llama-prod-kserve-abc123
```

Output:
```
Last State:     Terminated
  Reason:       OOMKilled
  Exit Code:    137
```

**Possible Causes:**

**1. GPU memory exhausted (VRAM)**
```bash
# Check vLLM logs
kubectl logs llama-prod-kserve-abc123 -c main --previous
```

Look for:
```
torch.cuda.OutOfMemoryError: CUDA out of memory.
Tried to allocate 2.00 GiB (GPU 0; 79.32 GiB total capacity)
```

**Solution:**
```yaml
# Reduce GPU memory usage
args:
- --gpu-memory-utilization=0.80  # Lower from 0.90
- --max-model-len=4096  # Reduce context length
- --max-num-seqs=128  # Reduce concurrent requests
```

**2. KV cache too large**

**Solution:**
```yaml
args:
- --kv-cache-dtype=fp8  # Use quantized cache
- --max-model-len=2048  # Reduce max context
```

#### Issue 3: Slow First Token (High TTFT)

**Symptoms:**
```bash
$ curl -w "@curl-format.txt" ...
time_to_first_token: 5.234s  # Should be < 1s
```

**Diagnosis:**
```bash
# Check prefill pod metrics
kubectl port-forward svc/llama-prod-kserve-prefill-svc 8000:8000
curl http://localhost:8000/metrics | grep time_to_first_token
```

**Possible Causes:**

**1. Prefill underprovisioned**

**Solution:**
```bash
# Scale up prefill pods
kubectl patch llmisvc llama-prod --type merge -p '{
  "spec": {
    "prefill": {
      "replicas": 4
    }
  }
}'

# Increase prefill TP
kubectl patch llmisvc llama-prod --type merge -p '{
  "spec": {
    "prefill": {
      "parallelism": {
        "tensor": 8
      }
    }
  }
}'
```

**2. Prefill pod far from decode pod (network latency)**

**Solution:**
```yaml
# Add pod affinity
spec:
  prefill:
    template:
      affinity:
        podAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  llm-d.ai/role: decode
              topologyKey: kubernetes.io/hostname
```

#### Issue 4: 503 Service Unavailable

**Symptoms:**
```bash
$ curl https://gateway/llm-prod/llama-prod/v1/chat/completions
{"error": "Service Unavailable"}
```

**Diagnosis:**
```bash
# Check HTTPRoute status
kubectl get httproute llama-prod-kserve-route -o yaml

# Check InferencePool
kubectl get inferencepool llama-prod-inference-pool -o yaml
```

**Possible Causes:**

**1. No ready pods in InferencePool**

```yaml
status:
  targets: []  # Empty!
```

**Solution:**
```bash
# Check pod readiness
kubectl get pods -l app.kubernetes.io/name=llama-prod

# Check readiness probe logs
kubectl describe pod <pod-name>
```

**2. Scheduler unhealthy**

**Solution:**
```bash
kubectl get pod -l app.kubernetes.io/component=scheduler
kubectl logs -l app.kubernetes.io/component=scheduler --tail=100
```

#### Issue 5: Model Download Fails

**Symptoms:**
```bash
$ kubectl logs llama-prod-kserve-abc123 -c storage-initializer
ERROR: Failed to download model from hf://meta-llama/Llama-3-8B-Instruct
```

**Diagnosis:**
```bash
kubectl logs llama-prod-kserve-abc123 -c storage-initializer
```

**Possible Causes:**

**1. Missing HuggingFace token**

**Solution:**
```bash
# Create secret
kubectl create secret generic hf-token \
  --from-literal=token=hf_... \
  -n llm-prod

# Reference in LLMD
spec:
  template:
    containers:
    - name: main
      env:
      - name: HF_TOKEN
        valueFrom:
          secretKeyRef:
            name: hf-token
            key: token
```

**2. Network/proxy issues**

**Solution:**
```yaml
spec:
  template:
    containers:
    - name: main
      env:
      - name: HTTP_PROXY
        value: "http://proxy.company.com:8080"
      - name: HTTPS_PROXY
        value: "http://proxy.company.com:8080"
```

### Debugging Checklist

```bash
#!/bin/bash
# debug-llmd.sh

NAMESPACE="llm-prod"
SERVICE="llama-prod"

echo "=== 1. Check LLMInferenceService Status ==="
kubectl get llmisvc $SERVICE -n $NAMESPACE -o yaml

echo -e "\n=== 2. Check All Pods ==="
kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=$SERVICE

echo -e "\n=== 3. Check Resource Usage ==="
kubectl top pod -n $NAMESPACE -l app.kubernetes.io/name=$SERVICE

echo -e "\n=== 4. Check Events ==="
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -20

echo -e "\n=== 5. Check Logs (Last 50 lines) ==="
for pod in $(kubectl get pod -n $NAMESPACE -l app.kubernetes.io/name=$SERVICE -o name); do
  echo "Logs from $pod:"
  kubectl logs -n $NAMESPACE $pod --tail=50 --all-containers
done

echo -e "\n=== 6. Check HTTPRoute ==="
kubectl get httproute -n $NAMESPACE -l app.kubernetes.io/name=$SERVICE -o yaml

echo -e "\n=== 7. Check InferencePool ==="
kubectl get inferencepool -n $NAMESPACE -o yaml

echo -e "\n=== 8. Check Scheduler ==="
kubectl get pod -n $NAMESPACE -l app.kubernetes.io/component=scheduler
kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=scheduler --tail=30
```

Run:
```bash
chmod +x debug-llmd.sh
./debug-llmd.sh > debug-output.txt
```

---

## Chapter 24: Capacity Planning

### Sizing Guidelines

**Model Memory Requirements (FP16/BF16):**

| Model | Parameters | VRAM (FP16) | VRAM (INT8) | VRAM (INT4) |
|-------|-----------|-------------|-------------|-------------|
| Llama-3-1B | 1B | ~2 GB | ~1 GB | ~0.5 GB |
| Llama-3-8B | 8B | ~16 GB | ~8 GB | ~4 GB |
| Llama-3-13B | 13B | ~26 GB | ~13 GB | ~7 GB |
| Llama-3-70B | 70B | ~140 GB | ~70 GB | ~35 GB |
| Llama-3-405B | 405B | ~810 GB | ~405 GB | ~203 GB |
| Mixtral-8x7B | 47B | ~94 GB | ~47 GB | ~24 GB |

**Add overhead for KV cache:**
```
Total VRAM = Model + KV Cache + Activations

KV Cache per request ≈ 
  (layers × hidden_dim × 2 × seq_len × precision_bytes) / 1024³

Example (Llama-3-8B, 2048 tokens, FP16):
  (32 × 4096 × 2 × 2048 × 2) / 1024³ ≈ 1 GB per request

If serving 10 concurrent requests: +10 GB
Total: 16 GB (model) + 10 GB (KV) = 26 GB
```

**GPU Selection:**

| GPU | VRAM | Best For |
|-----|------|----------|
| L4 | 24 GB | Llama-3-8B, Llama-3-13B (INT8) |
| L40 | 48 GB | Llama-3-13B, Llama-3-70B (TP=2) |
| A100 (40GB) | 40 GB | Llama-3-13B, Llama-3-70B (TP=2) |
| A100 (80GB) | 80 GB | Llama-3-70B (TP=2), Llama-3-405B (TP=8+) |
| H100 | 80 GB | Llama-3-70B (TP=2), Llama-3-405B (TP=8+) |
| H200 | 144 GB | Llama-3-70B (TP=1!), Llama-3-405B (TP=6+) |

### Throughput Estimation

**Tokens per second per GPU:**

```
Theoretical max tokens/sec = 
  (GPU TFLOPS × Utilization) / (Model FLOP per token)

Llama-3-8B on H100:
  ≈ 989 TFLOPS × 0.5 / (16 × 10⁹ FLOP/token)
  ≈ 31 tokens/sec/GPU (decode)

Reality check: Actual ≈ 20-25 tokens/sec (due to memory bandwidth)
```

**Requests per second:**

```
RPS = (Tokens/sec per GPU × Num GPUs) / Avg tokens per request

Example:
  • 4 decode pods × 1 GPU each
  • 20 tokens/sec/GPU
  • Average response: 100 tokens
  
  RPS = (20 × 4) / 100 = 0.8 RPS = 2880 requests/hour
```

### Cost Optimization

**Strategy 1: Quantization**

```yaml
# INT8 quantization (2x memory reduction, minimal accuracy loss)
args:
- --quantization=int8

# INT4 quantization (4x memory reduction, some accuracy loss)
args:
- --quantization=int4-awq  # or int4-gptq
```

**Benefits:**
- 2-4x smaller model
- Fit larger models on same GPU
- Can increase batch size

**Strategy 2: Disaggregation**

```
Without disaggregation:
  8 GPUs × 8 hours/day = 64 GPU-hours
  Utilization: 35%
  Effective: 22.4 GPU-hours
  Cost: $50/GPU-hour × 64 = $3,200/day

With disaggregation:
  Prefill: 2 GPUs × 8 hours = 16 GPU-hours (90% util)
  Decode: 4 GPUs × 8 hours = 32 GPU-hours (80% util)
  Total: 48 GPU-hours
  Effective: 40 GPU-hours
  Cost: $50/GPU-hour × 48 = $2,400/day
  
Savings: $800/day (25%)
```

**Strategy 3: Spot/Preemptible Instances**

```yaml
# Tolerate spot instance interruptions
spec:
  template:
    nodeSelector:
      cloud.google.com/gke-spot: "true"
    tolerations:
    - key: cloud.google.com/gke-spot
      operator: Equal
      value: "true"
      effect: NoSchedule
```

Savings: 60-80% on cloud GPU costs

---

# Appendices

---

## Appendix A: CRD Reference

### LLMInferenceService

**API Group:** `serving.kserve.io/v1alpha1`  
**Kind:** `LLMInferenceService`  
**Short Name:** `llmisvc`

**Spec Fields:**

```yaml
spec:
  # Model configuration
  model:
    uri: string           # Required: Model location
    name: string          # Required: Model name for API
    criticality: string   # Optional: Critical|Normal|Sheddable
    lora:                 # Optional: LoRA adapters
      adapters: []
  
  # Config inheritance
  baseRefs: []            # Optional: Config templates
  
  # Main workload (decode in P/D mode)
  replicas: int           # Required: Number of pods
  parallelism:            # Optional: GPU parallelism
    tensor: int
    pipeline: int
    data: int
    expert: bool
  template:               # Required: Pod template
    spec: PodSpec
  
  # Prefill workload (enables P/D)
  prefill:                # Optional
    replicas: int
    parallelism: {}
    template: {}
  
  # Multi-node worker
  worker:                 # Optional
    containers: []
  
  # Networking
  router:                 # Optional
    gateway: {}           # Gateway config
    route: {}             # HTTPRoute config
    ingress: {}           # Ingress config (alternative)
    scheduler: {}         # Scheduler config
```

**Status Fields:**

```yaml
status:
  conditions:
    - type: Ready
      status: True|False
    - type: HTTPRoutesReady
    - type: InferencePoolReady
    - type: MainWorkloadReady
    - type: PrefillWorkloadReady
    - type: SchedulerWorkloadReady
  url: string             # Service endpoint
```

### InferencePool

**API Group:** `inference.networking.x-k8s.io/v1alpha2`  
**Kind:** `InferencePool`

```yaml
spec:
  selector:               # Pod selector
    matchLabels: {}
  targetPortNumber: int   # Backend port
  extensionRef:           # ExtProc (Scheduler)
    kind: Service
    name: string
    failureMode: string   # FailOpen|FailClosed
```

### InferenceModel

**API Group:** `inference.networking.x-k8s.io/v1alpha2`  
**Kind:** `InferenceModel`

```yaml
spec:
  modelName: string       # Model identifier
  poolRef:                # Link to InferencePool
    kind: InferencePool
    name: string
  criticality: string     # Critical|Normal|Sheddable
```

---

## Appendix B: Command Reference

### kubectl Commands

```bash
# List LLMInferenceServices
kubectl get llmisvc
kubectl get llmisvc -A  # All namespaces

# Describe
kubectl describe llmisvc my-llm

# Get YAML
kubectl get llmisvc my-llm -o yaml

# Edit
kubectl edit llmisvc my-llm

# Delete
kubectl delete llmisvc my-llm

# Scale
kubectl patch llmisvc my-llm --type merge -p '{"spec":{"replicas":4}}'

# Check status
kubectl get llmisvc my-llm -o jsonpath='{.status.conditions}'

# Get URL
kubectl get llmisvc my-llm -o jsonpath='{.status.url}'
```

### Debugging Commands

```bash
# Get all resources
kubectl get all -l app.kubernetes.io/name=my-llm

# Check pods by role
kubectl get pods -l llm-d.ai/role=prefill
kubectl get pods -l llm-d.ai/role=decode

# Logs
kubectl logs -f pod/my-llm-kserve-abc123 -c main
kubectl logs pod/my-llm-kserve-abc123 -c llm-d-routing-sidecar

# Execute in pod
kubectl exec -it pod/my-llm-kserve-abc123 -c main -- bash

# Port forward
kubectl port-forward svc/my-llm-kserve-svc 8000:8000

# Resource usage
kubectl top pod -l app.kubernetes.io/name=my-llm

# Events
kubectl get events --sort-by='.lastTimestamp' | grep my-llm
```

---

## Appendix C: Glossary

**Disaggregated Serving:** Splitting LLM inference into separate prefill and decode deployments

**EPP (Endpoint Picker):** The scheduler component that selects optimal pods for requests

**ExtProc (External Processing):** Envoy protocol for calling external services during request processing

**Gateway API:** Kubernetes-native ingress/routing API (successor to Ingress)

**InferencePool:** CRD that lists available pods for a model service

**InferenceModel:** CRD that describes model metadata and links to InferencePool

**KV Cache:** Key-Value cache storing attention weights from previous tokens

**LeaderWorkerSet:** Kubernetes controller for managing multi-pod groups

**LLMD:** LLMInferenceService, a KServe CRD for deploying LLMs

**llm-d:** Open-source distributed LLM inference framework

**PagedAttention:** vLLM's memory-efficient KV cache management algorithm

**Prefill:** Phase of LLM inference that processes the input prompt

**Decode:** Phase of LLM inference that generates output tokens

**Routing Sidecar:** Proxy in decode pods that routes to prefill or local decode

**Scheduler:** Component that intelligently routes requests to pods

**Tensor Parallelism (TP):** Distributing model layers across multiple GPUs

**TTFT (Time To First Token):** Latency from request to first output token

**TPOT (Time Per Output Token):** Latency per generated token

**vLLM:** High-performance LLM inference engine

---

## Appendix D: Resources

### Official Documentation

- **KServe:** https://kserve.github.io/kserve/
- **llm-d:** https://llm-d.ai
- **vLLM:** https://docs.vllm.ai
- **Gateway API:** https://gateway-api.sigs.k8s.io/
- **LeaderWorkerSet:** https://github.com/kubernetes-sigs/lws

### GitHub Repositories

- **KServe:** https://github.com/kserve/kserve
- **ODH KServe (with LLMD):** https://github.com/opendatahub-io/kserve
- **llm-d:** https://github.com/llm-d/llm-d
- **ODH Model Controller:** https://github.com/opendatahub-io/odh-model-controller
- **vLLM:** https://github.com/vllm-project/vllm

### Community

- **KServe Slack:** https://kserve.slack.com
- **llm-d Slack:** https://llm-d.ai/slack
- **llm-d Calendar:** https://red.ht/llm-d-public-calendar
- **Google Group:** https://groups.google.com/g/llm-d-contributors

### Papers and Blogs

- **PagedAttention:** https://arxiv.org/abs/2309.06180
- **Disaggregated Serving:** https://llm-d.ai/blog/intelligent-inference-scheduling-with-llm-d
- **llm-d v0.3 Release:** https://llm-d.ai/blog/llm-d-v0.3-expanded-hardware-faster-perf-and-igw-ga

---

## Conclusion

Congratulations! You've completed the LLMD & KServe Complete Textbook.

You now understand:
- ✅ How LLM inference works (prefill vs decode)
- ✅ Why Kubernetes and KServe for LLM serving
- ✅ The llm-d architecture and philosophy
- ✅ LLMD (LLMInferenceService) CRD and all components
- ✅ Envoy, Gateway API, ExtProc, and intelligent routing
- ✅ The Scheduler (EPP) and how it makes decisions
- ✅ Routing sidecar and KV cache management
- ✅ vLLM and PagedAttention
- ✅ GPU parallelism strategies
- ✅ Multi-node deployments with LeaderWorkerSet
- ✅ Production deployment best practices
- ✅ Monitoring, troubleshooting, and capacity planning

**Next Steps:**
1. Deploy your first LLMD service (Lab 1)
2. Try disaggregated serving (Lab 2)
3. Deploy to production (Lab 3)
4. Contribute to llm-d or KServe!

**Keep Learning:**
- Join the community Slack channels
- Attend weekly standups and SIG meetings
- Read the latest llm-d blog posts
- Experiment with new features

**Good luck with your LLM serving journey! 🚀**

---

**End of Textbook**

*Version 1.0 - October 14, 2025*


