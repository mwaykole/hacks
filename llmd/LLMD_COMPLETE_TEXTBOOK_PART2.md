# LLMD & KServe Complete Textbook - Part 2
## Continued from Part 1

---

# Part III: The Components

---

## Chapter 9: Envoy and Gateway API

### What is Envoy?

Envoy is a high-performance proxy that sits at the edge of your application, handling:
- Request routing
- Load balancing
- TLS termination
- Observability (metrics, traces, logs)
- Advanced traffic management

**Why Envoy for LLM serving?**
- Battle-tested at massive scale (used by Lyft, Google, AWS)
- Rich extension system (filters, external processors)
- Native support for gRPC and HTTP/2
- Excellent observability
- Can make routing decisions based on request content

### Envoy Architecture (Simplified)

```
┌────────────────────────────────────────────────────────┐
│                    Envoy Proxy                         │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────┐ │
│  │  Listeners   │ → │   Filters    │ → │  Clusters │ │
│  │  (ports)     │   │  (logic)     │   │  (backends)│ │
│  └──────────────┘   └──────────────┘   └───────────┘ │
│       │                    │                   │      │
│       │                    ▼                   │      │
│       │            ┌──────────────┐            │      │
│       │            │  ExtProc     │            │      │
│       │            │  (Scheduler) │            │      │
│       │            └──────────────┘            │      │
│       │                                        │      │
└───────┼────────────────────────────────────────┼──────┘
        │                                        │
    Client request                        Backend pods
```

**Components:**

**1. Listener**
- Binds to a port (e.g., :80, :443)
- Accepts incoming connections
- Applies filter chain

**2. Filters**
- Process requests (e.g., routing, auth)
- Can call external services (ExtProc)
- Modify requests/responses

**3. Clusters**
- Groups of backend endpoints
- Health checking
- Load balancing algorithms

**4. ExtProc (External Processing)**
- Call external service during request processing
- Get routing decision from Scheduler
- Modify headers, body, routing

### Gateway API (Kubernetes-Native)

Gateway API is the modern, Kubernetes-native way to configure ingress, replacing the older Ingress resource.

**Why Gateway API?**
- **Expressive:** Can model complex routing
- **Extensible:** Support for filters, backends
- **Role-oriented:** Separation of concerns
- **Type-safe:** Strong CRD validation
- **Multi-provider:** Works with Envoy, Istio, etc.

**Gateway API Resources:**

```
┌─────────────────────────────────────────────────────┐
│  Gateway API Resource Hierarchy                     │
└─────────────────────────────────────────────────────┘

GatewayClass (cluster-scoped)
  └─ Defines Gateway implementation (Envoy, Istio, etc.)
     │
     └─ Gateway (namespace-scoped)
        └─ Represents a load balancer
           │
           └─ HTTPRoute (namespace-scoped)
              └─ Defines routing rules
                 │
                 └─ Backend
                    └─ Service, InferencePool, etc.
```

**Example Configuration:**

```yaml
# GatewayClass (typically pre-installed)
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: envoy
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller
---
# Gateway (the load balancer)
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: llm-gateway
  namespace: istio-system
spec:
  gatewayClassName: envoy
  listeners:
  - name: http
    port: 80
    protocol: HTTP
    allowedRoutes:
      namespaces:
        from: All  # Allow routes from any namespace
---
# HTTPRoute (routing rules)
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: my-llm-route
  namespace: default
spec:
  parentRefs:
  - name: llm-gateway
    namespace: istio-system
  
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /default/my-llm
    
    filters:
    - type: URLRewrite
      urlRewrite:
        path:
          type: ReplacePrefixMatch
          replacePrefixMatch: /
    
    backendRefs:
    - group: inference.networking.x-k8s.io
      kind: InferencePool
      name: my-llm-inference-pool
      port: 8000
```

**How it works:**

```
1. Request arrives: http://gateway/default/my-llm/v1/chat/completions

2. Gateway receives on port 80

3. HTTPRoute matches:
   Path: /default/my-llm ✓

4. URLRewrite filter:
   /default/my-llm/v1/chat/completions
   → /v1/chat/completions

5. Backend selection:
   Look up InferencePool: my-llm-inference-pool
   Get list of pod IPs

6. (Optional) Call ExtProc (Scheduler):
   "Which pod from the pool?"
   Scheduler: "Use 10.244.1.7"

7. Forward to pod:
   POST http://10.244.1.7:8000/v1/chat/completions
```

### ExtProc (External Processing) Protocol

ExtProc allows Envoy to call an external service during request processing. This is how the Scheduler gets involved!

**ExtProc Flow:**

```
┌────────────────────────────────────────────────────┐
│  Client Request Flow with ExtProc                  │
└────────────────────────────────────────────────────┘

Client
  │
  │ 1. HTTP Request
  ▼
Envoy (Listener)
  │
  │ 2. Filter Chain
  ▼
ExtProc Filter
  │
  │ 3. gRPC call → Scheduler
  │    ProcessingRequest {
  │      headers: {...}
  │      body: {...}
  │    }
  ▼
Scheduler (EPP)
  │
  │ 4. Analyze request
  │    • Query InferencePool
  │    • Check pod metrics
  │    • Apply scoring
  │
  │ 5. ProcessingResponse {
  │      response: {
  │        header_mutation: {
  │          set_headers: [
  │            {key: "x-target-pod", value: "10.244.1.7"}
  │          ]
  │        }
  │      }
  │    }
  ▼
Envoy
  │
  │ 6. Apply mutations
  │    Set header: x-target-pod: 10.244.1.7
  │
  │ 7. Route to specific pod
  ▼
Backend Pod (10.244.1.7)
  │
  │ 8. Process request
  ▼
Response back to client
```

**ExtProc Configuration in LLMD:**

```yaml
# In HTTPRoute (automatically created by controller)
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: my-llm-route
spec:
  rules:
  - backendRefs:
    - group: inference.networking.x-k8s.io
      kind: InferencePool
      name: my-llm-inference-pool
      
      # ExtProc configuration
      extensionRef:
        group: inference.networking.x-k8s.io
        kind: Service
        name: my-llm-epp-service  # Points to Scheduler
        namespace: default
        failureMode: FailOpen      # Continue even if Scheduler fails
```

**ExtProc Benefits:**
- Scheduler doesn't need to handle HTTP directly
- Envoy maintains connection pooling
- Clean separation of concerns
- Can fail open (fallback to round-robin)

### Putting It Together: Request Flow

```
┌─────────────────────────────────────────────────────┐
│  Complete Request Flow (with all components)        │
└─────────────────────────────────────────────────────┘

1. Client Request
   │
   ├─ POST https://llm.example.com/default/my-llm/v1/chat/completions
   │
   ▼

2. DNS Resolution
   │
   ├─ llm.example.com → Gateway LoadBalancer IP
   │
   ▼

3. Gateway (Envoy) - Listener
   │
   ├─ TLS termination
   ├─ Parse HTTP/2 request
   │
   ▼

4. Gateway - Route Matching
   │
   ├─ Find HTTPRoute matching /default/my-llm
   ├─ Apply filters (URLRewrite)
   │
   ▼

5. Gateway - ExtProc Call
   │
   ├─ gRPC call to Scheduler
   ├─ Send: request headers, path, body snippet
   │
   ▼

6. Scheduler (EPP)
   │
   ├─ Query InferencePool (get available pods)
   ├─ Check metrics (load, queue depth)
   ├─ Score each pod
   ├─ Select best: decode-pod-7 (IP: 10.244.1.7)
   ├─ Return: x-target-pod: 10.244.1.7
   │
   ▼

7. Gateway - Apply Decision
   │
   ├─ Set routing target to 10.244.1.7:8000
   ├─ Open connection to pod
   │
   ▼

8. Decode Pod - Routing Sidecar
   │
   ├─ Receives request on :8000
   ├─ Checks if prefill needed
   │  ├─ New conversation? → Forward to prefill pod
   │  └─ Existing? → Forward to local :8001
   │
   ▼

9. vLLM (Prefill or Decode)
   │
   ├─ Process request
   ├─ Generate tokens
   ├─ Stream response
   │
   ▼

10. Response Path
    │
    ├─ Pod → Routing Sidecar → Gateway → Client
    │
    ▼

11. Client Receives Streaming Response
    │
    └─ data: {"choices": [{"delta": {"content": "Hello"}}]}
```

---

## Chapter 10: The Scheduler (EPP)

### What is EPP?

EPP (Endpoint Picker) is the intelligent scheduler component from the llm-d project. It makes smart routing decisions based on:
- Pod availability and health
- Current load per pod
- KV cache locality (does a pod have the conversation's cache?)
- Model criticality/priority
- Custom scoring algorithms

**Why "Endpoint Picker"?**
- Picks the best endpoint (pod) for each request
- Pluggable architecture (add your own scorers)
- Works via Envoy's ExtProc protocol

### Scheduler Architecture

```
┌─────────────────────────────────────────────────────┐
│            Scheduler (EPP) Architecture              │
└─────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Scheduler Pod                                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  gRPC Server (ExtProc)                         │ │
│  │  • Port 9002                                   │ │
│  │  • Receives requests from Envoy                │ │
│  │  • Returns routing decisions                   │ │
│  └────────────┬───────────────────────────────────┘ │
│               │                                      │
│               ▼                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Profile Handler                               │ │
│  │  • Detects request type (prefill vs decode)    │ │
│  │  • Applies appropriate profile                 │ │
│  └────────────┬───────────────────────────────────┘ │
│               │                                      │
│               ▼                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Plugin Pipeline                               │ │
│  │  ┌──────────────────────────────────────────┐ │ │
│  │  │ 1. Filter Plugin                         │ │ │
│  │  │    • Filter to prefill or decode pods    │ │ │
│  │  ├──────────────────────────────────────────┤ │ │
│  │  │ 2. Scorer Plugins                        │ │ │
│  │  │    • Prefix Cache Scorer (weight: 2.0)   │ │ │
│  │  │    • Load-Aware Scorer (weight: 1.0)     │ │ │
│  │  │    • Criticality Scorer (weight: 0.5)    │ │ │
│  │  ├──────────────────────────────────────────┤ │ │
│  │  │ 3. Picker Plugin                         │ │ │
│  │  │    • Select pod with highest score       │ │ │
│  │  └──────────────────────────────────────────┘ │ │
│  └────────────┬───────────────────────────────────┘ │
│               │                                      │
│               ▼                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  InferencePool Client                          │ │
│  │  • Watches InferencePool CRD                   │ │
│  │  • Maintains list of available pods            │ │
│  │  • Updates on pod changes                      │ │
│  └────────────┬───────────────────────────────────┘ │
│               │                                      │
│               ▼                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Metrics Client                                │ │
│  │  • Scrapes pod metrics (Prometheus)            │ │
│  │  • Tracks load, queue depth, etc.              │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Prometheus Exporter                           │ │
│  │  • Port 9090                                   │ │
│  │  • Exports scheduler metrics                   │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Health Server                                 │ │
│  │  • Port 9003                                   │ │
│  │  • Readiness & liveness checks                 │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### Scheduling Profiles

The Scheduler uses different "profiles" for different request types:

**Profile 1: Prefill Profile**
```
Used when: Request needs prefill (new conversation)

Plugins:
  1. prefill-filter
     • Keep only pods with label: llm-d.ai/role=prefill
     • Remove all decode pods
  
  2. prefix-cache-scorer (weight: 2.0)
     • Score higher if pod has matching prefix in cache
     • Helps reuse common prompt prefixes
  
  3. load-aware-scorer (weight: 1.0)
     • Score based on current load
     • Lower load = higher score
  
  4. max-score-picker
     • Select pod with highest total score

Example:
  Pods available:
    prefill-pod-0: cache=0.3, load=0.5 → score = (2.0×0.3 + 1.0×0.5) = 1.1
    prefill-pod-1: cache=0.8, load=0.7 → score = (2.0×0.8 + 1.0×0.3) = 1.9 ✓
  
  Pick: prefill-pod-1
```

**Profile 2: Decode Profile**
```
Used when: Request continues existing conversation

Plugins:
  1. decode-filter
     • Keep only pods with label: llm-d.ai/role=decode
     • Remove all prefill pods
  
  2. prefix-cache-scorer (weight: 2.0)
     • HIGH priority: Does pod have this conversation's KV?
     • Huge score boost if yes
  
  3. load-aware-scorer (weight: 1.0)
     • Prefer less-loaded pods
  
  4. max-score-picker

Example:
  Conversation ID: "session-abc-123"
  
  Pods available:
    decode-pod-0: has-kv=NO,  load=0.2 → score = (2.0×0.0 + 1.0×0.8) = 0.8
    decode-pod-1: has-kv=YES, load=0.5 → score = (2.0×1.0 + 1.0×0.5) = 2.5 ✓
    decode-pod-2: has-kv=NO,  load=0.1 → score = (2.0×0.0 + 1.0×0.9) = 0.9
  
  Pick: decode-pod-1 (even though more loaded, KV locality wins!)
```

### Scoring Algorithm Deep Dive

Let's walk through a real scheduling decision:

**Scenario:**
- 4 decode pods available
- Request is follow-up in conversation "conv-xyz"

**Step 1: Query InferencePool**
```yaml
apiVersion: inference.networking.x-k8s.io/v1alpha2
kind: InferencePool
metadata:
  name: my-llm-inference-pool
status:
  targets:
    - name: decode-pod-0
      address: 10.244.1.5
      ready: true
      metadata:
        sessions: ["conv-abc", "conv-def"]
    - name: decode-pod-1
      address: 10.244.1.6
      ready: true
      metadata:
        sessions: ["conv-xyz", "conv-ghi"]  # ← Has our session!
    - name: decode-pod-2
      address: 10.244.1.7
      ready: true
      metadata:
        sessions: ["conv-jkl"]
    - name: decode-pod-3
      address: 10.244.1.8
      ready: false  # Not ready, skip
```

**Step 2: Filter**
```
Input: 4 pods
Filter: ready == true
Output: 3 pods (0, 1, 2)
```

**Step 3: Score Each Pod**

**Pod 0:**
```
Prefix Cache Scorer:
  • Has session "conv-xyz"? NO
  • Score: 0.0

Load-Aware Scorer:
  • Current QPS: 5
  • Max QPS: 20
  • Load: 5/20 = 0.25
  • Score: 1.0 - 0.25 = 0.75

Total: (2.0 × 0.0) + (1.0 × 0.75) = 0.75
```

**Pod 1:**
```
Prefix Cache Scorer:
  • Has session "conv-xyz"? YES ✓
  • Score: 1.0

Load-Aware Scorer:
  • Current QPS: 12
  • Max QPS: 20
  • Load: 12/20 = 0.60
  • Score: 1.0 - 0.60 = 0.40

Total: (2.0 × 1.0) + (1.0 × 0.40) = 2.40 ✓ HIGHEST
```

**Pod 2:**
```
Prefix Cache Scorer:
  • Has session "conv-xyz"? NO
  • Score: 0.0

Load-Aware Scorer:
  • Current QPS: 2
  • Max QPS: 20
  • Load: 2/20 = 0.10
  • Score: 1.0 - 0.10 = 0.90

Total: (2.0 × 0.0) + (1.0 × 0.90) = 0.90
```

**Step 4: Pick Winner**
```
Scores:
  Pod 0: 0.75
  Pod 1: 2.40 ✓
  Pod 2: 0.90

Selected: Pod 1 (10.244.1.6)
```

**Step 5: Return to Envoy**
```
ProcessingResponse {
  response: {
    header_mutation: {
      set_headers: [
        {
          header: {key: "x-target-pod", value: "10.244.1.6"}
        }
      ]
    }
  }
}
```

### Scheduler Metrics

The Scheduler exposes Prometheus metrics for monitoring:

```
# Scheduling decisions
scheduler_requests_total{profile="decode",decision="selected"} 1234
scheduler_requests_total{profile="prefill",decision="selected"} 567

# Pod scores
scheduler_pod_score{pod="decode-pod-0",profile="decode"} 0.75
scheduler_pod_score{pod="decode-pod-1",profile="decode"} 2.40
scheduler_pod_score{pod="decode-pod-2",profile="decode"} 0.90

# Decision latency
scheduler_decision_duration_seconds{profile="decode"} 0.002

# Cache hit rate
scheduler_cache_hits_total{profile="decode"} 890
scheduler_cache_misses_total{profile="decode"} 110
```

### Custom Scoring Plugins

You can write custom scorers! Here's the interface:

```go
type ScorerPlugin interface {
    Name() string
    Score(ctx context.Context, request *Request, pod *Pod) float64
}

// Example: GPU memory scorer
type GPUMemoryScorer struct {
    weight float64
}

func (s *GPUMemoryScorer) Score(ctx context.Context, req *Request, pod *Pod) float64 {
    // Get GPU memory usage from pod metrics
    memUsed := pod.Metrics.GPUMemoryUsedBytes
    memTotal := pod.Metrics.GPUMemoryTotalBytes
    memAvail := memTotal - memUsed
    
    // Score based on available memory
    // More available = higher score
    return (float64(memAvail) / float64(memTotal)) * s.weight
}
```

---

## Chapter 11: Routing Sidecar

### What is the Routing Sidecar?

The routing sidecar is a small proxy that sits next to the vLLM decode container. Its job is to:
1. Receive requests on port 8000 (external)
2. Decide: "Does this need prefill or can decode handle it?"
3. Route accordingly:
   - New conversation → Forward to prefill pod
   - Follow-up → Forward to local decode (port 8001)
4. Manage KV cache metadata
5. Stream response back to client

**Why a sidecar?**
- Decode container can focus on inference
- Sidecar handles routing logic
- Can be updated independently
- Clean separation of concerns

### Sidecar Architecture

```
┌────────────────────────────────────────────────────┐
│  Decode Pod                                        │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │  Routing Sidecar Container                   │ │
│  │  (llm-d-routing-sidecar)                     │ │
│  │                                              │ │
│  │  Port 8000 (external)                        │ │
│  │  ┌────────────────────────────────────────┐ │ │
│  │  │  HTTP Server                           │ │ │
│  │  │  • Receives requests                   │ │ │
│  │  │  • TLS termination                     │ │ │
│  │  └────────┬───────────────────────────────┘ │ │
│  │           │                                 │ │
│  │           ▼                                 │ │
│  │  ┌────────────────────────────────────────┐ │ │
│  │  │  Session Manager                       │ │ │
│  │  │  • Track active sessions               │ │ │
│  │  │  • Store KV cache metadata             │ │ │
│  │  │  • LRU eviction when full              │ │ │
│  │  └────────┬───────────────────────────────┘ │ │
│  │           │                                 │ │
│  │           ▼                                 │ │
│  │  ┌────────────────────────────────────────┐ │ │
│  │  │  Router Logic                          │ │ │
│  │  │  • Check: prefill needed?              │ │ │
│  │  │  • YES: Forward to prefill             │ │ │
│  │  │  • NO:  Forward to local decode        │ │ │
│  │  └─┬────────────────────────────────────┬─┘ │ │
│  │    │                                    │   │ │
│  └────┼────────────────────────────────────┼───┘ │
│       │                                    │     │
│       │ To prefill pod                     │     │
│       │ (HTTPS)                            │     │
│       ▼                                    ▼     │
│  ┌──────────────┐                  ┌───────────┐│
│  │ Prefill Pod  │                  │ vLLM      ││
│  │ :8000        │                  │ Decode    ││
│  └──────────────┘                  │ :8001     ││
│   (external)                       └───────────┘│
│                                    (internal)   │
└────────────────────────────────────────────────────┘
```

### How the Sidecar Decides

**Decision Tree:**

```
Request arrives at sidecar
  │
  ├─ Extract session ID from request
  │
  ├─ Check session manager
  │  │
  │  ├─ Session exists in cache?
  │  │  ├─ YES → KV cache available
  │  │  │        └─ Route to LOCAL DECODE (:8001)
  │  │  │
  │  │  └─ NO → Need prefill
  │  │           ├─ Query InferencePool for prefill pod
  │  │           ├─ Forward to PREFILL POD (:8000)
  │  │           ├─ Receive response + KV metadata
  │  │           ├─ Store KV in session manager
  │  │           └─ Continue with decode
  │
  └─ Stream response to client
```

### Request Flow Examples

**Example 1: First Message (Prefill Needed)**

```
┌─────────────────────────────────────────────────┐
│  Client Request                                 │
└─────────────────────────────────────────────────┘
POST https://decode-pod-1:8000/v1/chat/completions
Body: {
  "model": "llama-3-8b",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}

         ↓

┌─────────────────────────────────────────────────┐
│  Sidecar: Session Manager                       │
└─────────────────────────────────────────────────┘
// Generate or extract session ID
sessionID := extractOrGenerate(request)  // "sess-abc-123"

// Check cache
sessions := {
  "sess-xyz-789": {kv: {...}, lastUsed: ...}
}
hasCachedKV := sessions[sessionID]  // nil (not found)

Decision: PREFILL NEEDED

         ↓

┌─────────────────────────────────────────────────┐
│  Sidecar: Forward to Prefill                    │
└─────────────────────────────────────────────────┘
// Discover prefill pod (from InferencePool or config)
prefillPod := "https://prefill-pod-0:8000"

// Forward request
resp := httpPost(prefillPod, request)

         ↓

┌─────────────────────────────────────────────────┐
│  Prefill Pod: Process                           │
└─────────────────────────────────────────────────┘
vLLM prefill:
  • Tokenize: "Hello!" → [15339, 0]
  • Run prefill phase
  • Generate first token: "Hi"
  • Build KV cache
  • Return:
    {
      "choices": [{
        "delta": {"content": "Hi"},
        "kv_metadata": {
          "session_id": "sess-abc-123",
          "kv_handle": "kv://prefill-0/abc123",
          "tokens_processed": 2
        }
      }]
    }

         ↓

┌─────────────────────────────────────────────────┐
│  Sidecar: Store KV and Continue                 │
└─────────────────────────────────────────────────┘
// Store KV metadata
sessions["sess-abc-123"] = {
  kv: "kv://prefill-0/abc123",
  tokens: 2,
  lastUsed: now()
}

// Forward to local decode for remaining tokens
decodeReq := {
  "kv_handle": "kv://prefill-0/abc123",
  "continue_from": "Hi"
}
resp := httpPost("http://localhost:8001", decodeReq)

         ↓

┌─────────────────────────────────────────────────┐
│  Local vLLM Decode: Continue Generation         │
└─────────────────────────────────────────────────┘
vLLM decode:
  • Load KV from handle
  • Generate: "!" "How" "can" "I" "help"...
  • Stream tokens

         ↓

┌─────────────────────────────────────────────────┐
│  Sidecar: Stream to Client                      │
└─────────────────────────────────────────────────┘
Stream response:
data: {"choices": [{"delta": {"content": "Hi"}}]}
data: {"choices": [{"delta": {"content": "!"}}]}
data: {"choices": [{"delta": {"content": " How"}}]}
...
```

**Example 2: Follow-up Message (Decode Only)**

```
┌─────────────────────────────────────────────────┐
│  Client Request                                 │
└─────────────────────────────────────────────────┘
POST https://decode-pod-1:8000/v1/chat/completions
Body: {
  "model": "llama-3-8b",
  "messages": [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "What's 2+2?"}  ← New message
  ]
}

         ↓

┌─────────────────────────────────────────────────┐
│  Sidecar: Session Manager                       │
└─────────────────────────────────────────────────┘
sessionID := extractOrGenerate(request)  // "sess-abc-123"

// Check cache
hasCachedKV := sessions[sessionID]  // Found! ✓
kvHandle := sessions[sessionID].kv  // "kv://prefill-0/abc123"

Decision: USE LOCAL DECODE (No prefill needed!)

         ↓

┌─────────────────────────────────────────────────┐
│  Sidecar: Forward to Local Decode               │
└─────────────────────────────────────────────────┘
// NO external call to prefill!
// Go straight to local decode

decodeReq := {
  "kv_handle": kvHandle,
  "new_messages": [
    {"role": "user", "content": "What's 2+2?"}
  ]
}
resp := httpPost("http://localhost:8001", decodeReq)

         ↓

┌─────────────────────────────────────────────────┐
│  Local vLLM Decode: Process                     │
└─────────────────────────────────────────────────┘
vLLM decode:
  • Load existing KV cache (conversation history)
  • Process only new tokens: "What's 2+2?"
  • Update KV cache
  • Generate: "2" "+" "2" "=" "4" "!"
  • Stream tokens

         ↓

┌─────────────────────────────────────────────────┐
│  Sidecar: Stream to Client                      │
└─────────────────────────────────────────────────┘
Stream response:
data: {"choices": [{"delta": {"content": "2"}}]}
data: {"choices": [{"delta": {"content": "+"}}]}
data: {"choices": [{"delta": {"content": "2"}}]}
data: {"choices": [{"delta": {"content": "="}}]}
data: {"choices": [{"delta": {"content": "4"}}]}
...

MUCH FASTER! No prefill overhead! ✅
```

### Sidecar Configuration

```yaml
# Automatically injected by LLMD controller
initContainers:
- name: llm-d-routing-sidecar
  image: ghcr.io/llm-d/llm-d:v0.2.0
  command: ["/llm-d-routing-sidecar"]
  args:
  - --port=8000
  - --decoder-port=8001
  - --decoder-use-tls=true
  - --prefiller-use-tls=true
  - --prefill-url=https://my-llm-kserve-prefill-svc:8000
  - --connector=nixlv2
  - --cert-path=/etc/ssl/certs
  - --enable-ssrf-protection=true
  
  env:
  - name: INFERENCE_POOL_NAMESPACE
    value: default
  - name: INFERENCE_POOL_NAME
    value: my-llm-inference-pool
  
  ports:
  - containerPort: 8000
    protocol: TCP
    name: http
  
  restartPolicy: Always  # Runs continuously (not truly an init container)
```

**Key Configuration:**
- `--decoder-port`: Local vLLM decode port
- `--prefill-url`: Prefill service URL
- `--connector`: KV transfer protocol (nixlv2, tcp, etc.)
- `restartPolicy: Always`: Makes it run as sidecar

### Session Management and LRU Eviction

The sidecar has limited memory for session cache:

```
┌─────────────────────────────────────────────────┐
│  Session Cache (LRU)                            │
├─────────────────────────────────────────────────┤
│  Max Size: 1000 sessions                        │
│                                                 │
│  sess-newest:  {kv: ..., lastUsed: now()-1m}    │
│  sess-abc-123: {kv: ..., lastUsed: now()-5m}    │
│  sess-xyz-789: {kv: ..., lastUsed: now()-10m}   │
│  ...                                            │
│  sess-oldest:  {kv: ..., lastUsed: now()-60m}   │ ← Evicted first
└─────────────────────────────────────────────────┘
```

**Eviction Policy:**
- When cache is full and new session arrives
- Evict least recently used (LRU)
- Evicted session will need prefill again if it returns

**Tuning:**
```yaml
env:
- name: SESSION_CACHE_SIZE
  value: "2000"  # Increase if you have memory
```

---

*Continuing with more chapters...*


