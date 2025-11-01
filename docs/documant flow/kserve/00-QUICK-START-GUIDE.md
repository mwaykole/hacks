# KServe Quick Start Guide

## Overview

This is a quick reference guide to help you navigate the KServe documentation. All diagrams use **Mermaid flowcharts** for visualization.

## 🚀 5-Minute Understanding

### What is KServe?

KServe is a **Kubernetes-native platform** for serving both **Generative AI (LLMs)** and **Predictive AI (traditional ML)** models at scale.

```mermaid
flowchart LR
    You[You] -->|Deploy Model| KServe[KServe]
    KServe -->|Creates| Pod[Inference Pod]
    Pod -->|Serves| Model[Your ML Model]
    Client[Clients] -->|Request| Model
    Model -->|Prediction| Client
    
    style KServe fill:#e1f5ff
    style Pod fill:#fff4e1
    style Model fill:#99ff99
```

### Core Concepts

```mermaid
flowchart TB
    subgraph Concepts["Core Concepts"]
        ISVC[InferenceService<br/>Main resource you create]
        Predictor[Predictor<br/>Serves your model]
        Runtime[ServingRuntime<br/>How to run model]
        Storage[Storage<br/>Where model is stored]
    end
    
    You[You] -->|1. Create| ISVC
    ISVC -->|2. Specifies| Runtime
    ISVC -->|3. Loads from| Storage
    ISVC -->|4. Deploys| Predictor
    
    style ISVC fill:#e1f5ff
    style Predictor fill:#fff4e1
    style Runtime fill:#f0e1ff
    style Storage fill:#e1ffe1
```

## 📖 Documentation Roadmap

### By Experience Level

#### **Beginner** (Start Here)
```mermaid
flowchart LR
    Start[Start] -->|1| Overview[Overall Architecture<br/>📄 01]
    Overview -->|2| DataPlane[Data Plane<br/>📄 03]
    DataPlane -->|3| Storage[Storage Initializer<br/>📄 04]
    Storage -->|4| Predictor[Predictor Runtime<br/>📄 05]
    
    style Overview fill:#99ff99
    style DataPlane fill:#99ff99
    style Storage fill:#99ff99
    style Predictor fill:#99ff99
```

**Start with**: 
1. [Overall Architecture](./01-KSERVE-OVERALL-ARCHITECTURE.md) - Big picture
2. [Data Plane Components](./03-DATA-PLANE-COMPONENTS.md) - How it works
3. [Storage Initializer](./04-STORAGE-INITIALIZER.md) - Model loading
4. [Predictor Runtime](./05-PREDICTOR-RUNTIME.md) - Model serving

#### **Intermediate** (Deep Dive)
```mermaid
flowchart TB
    Controller[InferenceService Controller<br/>📄 02] 
    Transformer[Transformer Component<br/>📄 06]
    Explainer[Explainer Component<br/>📄 07]
    Graph[InferenceGraph<br/>📄 08]
    
    Controller --> Transformer
    Transformer --> Explainer
    Explainer --> Graph
    
    style Controller fill:#99ccff
    style Transformer fill:#99ccff
    style Explainer fill:#99ccff
    style Graph fill:#99ccff
```

**Continue with**:
- [InferenceService Controller](./02-INFERENCESERVICE-CONTROLLER.md) - Control plane

#### **Advanced** (Expert Level)
```mermaid
flowchart LR
    ModelMesh[ModelMesh<br/>📄 09]
    Knative[Knative<br/>📄 10]
    Autoscale[Autoscaling<br/>📄 11]
    Protocols[Protocols<br/>📄 12]
    
    ModelMesh --> Knative
    Knative --> Autoscale
    Autoscale --> Protocols
    
    style ModelMesh fill:#ff99cc
    style Knative fill:#ff99cc
    style Autoscale fill:#ff99cc
    style Protocols fill:#ff99cc
```

### By Use Case

#### **Deploying LLMs / Generative AI**

```mermaid
flowchart TB
    Start[Want to Deploy LLM]
    
    Start --> Arch[📄 01: Overall Architecture<br/>Section: Generative AI Features]
    Arch --> Predictor[📄 05: Predictor Runtime<br/>Section: LLM-Specific Features]
    Predictor --> Storage[📄 04: Storage Initializer<br/>Load Large Models]
    Storage --> Deploy[Ready to Deploy!]
    
    style Start fill:#e1f5ff
    style Deploy fill:#99ff99
```

**Key Topics**:
- vLLM Runtime
- GPU Memory Management
- KV Cache Offloading
- OpenAI Protocol
- Streaming Responses

#### **Deploying Traditional ML Models**

```mermaid
flowchart TB
    Start[Want to Deploy ML Model]
    
    Start --> Arch[📄 01: Overall Architecture<br/>Section: Predictive AI Features]
    Arch --> DataPlane[📄 03: Data Plane Components<br/>Component Overview]
    DataPlane --> Predictor[📄 05: Predictor Runtime<br/>Select Framework]
    Predictor --> Deploy[Ready to Deploy!]
    
    style Start fill:#fff4e1
    style Deploy fill:#99ff99
```

**Key Topics**:
- TensorFlow/PyTorch/SKLearn
- Transformer (Pre/Post-processing)
- Explainer (Model Interpretability)
- Batching

#### **High-Scale Multi-Model Serving**

```mermaid
flowchart TB
    Start[Need High-Density Serving]
    
    Start --> Arch[📄 01: Overall Architecture<br/>Section: ModelMesh Mode]
    Arch --> Deploy[Ready for ModelMesh!]
    
    style Start fill:#f0e1ff
    style Deploy fill:#99ff99
```

#### **Auto-Scaling Setup**

```mermaid
flowchart TB
    Start[Need Auto-Scaling]
    
    Start --> Mode{Deployment Mode?}
    Mode -->|Serverless| Knative[📄 10: Knative Integration]
    Mode -->|Raw K8s| HPA[📄 11: Autoscaling<br/>Section: HPA]
    
    style Start fill:#e1ffe1
```

## 📋 Component Quick Reference

```mermaid
flowchart TB
    subgraph ControlPlane["Control Plane"]
        Controller[InferenceService Controller<br/>Manages lifecycle<br/>Doc 02]
    end
    
    subgraph DataPlane["Data Plane"]
        Storage[Storage Initializer<br/>Loads models<br/>Doc 04]
        Predictor[Predictor<br/>Serves model<br/>Doc 05]
        Optional[Transformer + Explainer<br/>Pre/Post-process<br/>Doc 06, 07]
    end
    
    subgraph Integration["Integration"]
        Knative[Knative<br/>Serverless<br/>Doc 10]
        ModelMesh[ModelMesh<br/>Multi-model<br/>Doc 09]
    end
    
    ControlPlane -->|Orchestrates| DataPlane
    ControlPlane -->|Uses| Integration
    
    style ControlPlane fill:#e1f5ff
    style DataPlane fill:#fff4e1
    style Integration fill:#f0e1ff
```

## 🎯 Common Tasks

### Task 1: Deploy Your First Model

```mermaid
flowchart LR
    Read1[Read:<br/>Overall Architecture] -->
    Read2[Read:<br/>Predictor Runtime] -->
    Read3[Read:<br/>Storage Initializer] -->
    Deploy[Deploy!]
    
    style Deploy fill:#99ff99
```

**Documentation Path**:
1. [Overall Architecture](./01-KSERVE-OVERALL-ARCHITECTURE.md) → Deployment Modes
2. [Predictor Runtime](./05-PREDICTOR-RUNTIME.md) → Select your framework
3. [Storage Initializer](./04-STORAGE-INITIALIZER.md) → Configure storage

### Task 2: Add Pre-processing

```mermaid
flowchart LR
    Have[Have Basic Deployment] -->
    Read[Read:<br/>Transformer Component] -->
    Add[Add Transformer]
    
    style Add fill:#99ff99
```

**Documentation Path**:
- Coming: [Transformer Component](./06-TRANSFORMER-COMPONENT.md)

### Task 3: Enable Auto-Scaling

```mermaid
flowchart LR
    Have[Have Deployment] -->
    Check{Serverless?}
    Check -->|Yes| Knative[Read: Knative]
    Check -->|No| HPA[Read: Autoscaling]
    Knative --> Configure[Configure]
    HPA --> Configure
    
    style Configure fill:#99ff99
```

**Documentation Path**:
- Coming: [Knative Integration](./10-KNATIVE-INTEGRATION.md)
- Coming: [Autoscaling Mechanisms](./11-AUTOSCALING-MECHANISMS.md)

### Task 4: Setup Canary Deployment

```mermaid
flowchart LR
    Have[Have Deployment] -->
    Read[Read:<br/>InferenceService Controller<br/>Traffic Management] -->
    Deploy[Deploy Canary]
    
    style Deploy fill:#99ff99
```

**Documentation Path**:
- [InferenceService Controller](./02-INFERENCESERVICE-CONTROLLER.md) → Traffic Management

## 🔍 Find Information About...

### Components

| Component | Documentation | Key Topics |
|-----------|--------------|------------|
| **InferenceService** | [📄 02](./02-INFERENCESERVICE-CONTROLLER.md) | CRD, Reconciliation, Webhooks |
| **Storage** | [📄 04](./04-STORAGE-INITIALIZER.md) | S3, GCS, Azure, PVC, HTTP |
| **Predictor** | [📄 05](./05-PREDICTOR-RUNTIME.md) | Runtimes, GPU, LLMs |
| **Transformer** | 🔜 06 | Pre/Post-processing |
| **Explainer** | 🔜 07 | Model interpretability |
| **Router** | 🔜 08 | InferenceGraph, Pipelines |

### Features

| Feature | Where to Find |
|---------|---------------|
| **LLM Serving** | [📄 05](./05-PREDICTOR-RUNTIME.md) → LLM Features |
| **GPU Support** | [📄 05](./05-PREDICTOR-RUNTIME.md) → GPU Management |
| **Batching** | [📄 05](./05-PREDICTOR-RUNTIME.md) → Dynamic Batching |
| **Scale-to-Zero** | [📄 01](./01-KSERVE-OVERALL-ARCHITECTURE.md) + 🔜 10 |
| **Canary Rollout** | [📄 02](./02-INFERENCESERVICE-CONTROLLER.md) → Traffic |
| **Model Caching** | [📄 04](./04-STORAGE-INITIALIZER.md) + [📄 05](./05-PREDICTOR-RUNTIME.md) |

### Deployment Modes

```mermaid
flowchart TB
    Question[Which Mode?]
    
    Question -->|Want Scale-to-Zero| Serverless[Serverless Mode<br/>📄 01, 10]
    Question -->|Want Simplicity| Raw[Raw K8s Mode<br/>📄 01]
    Question -->|Want Multi-Model| MM[ModelMesh Mode<br/>📄 01, 09]
    
    style Serverless fill:#e1f5ff
    style Raw fill:#fff4e1
    style MM fill:#f0e1ff
```

## 📊 Documentation Status

| Document | Status | Topics Covered |
|----------|--------|----------------|
| 📄 00 Quick Start | ✅ Complete | Navigation guide |
| 📄 01 Overall Architecture | ✅ Complete | Full architecture |
| 📄 02 InferenceService Controller | ✅ Complete | Control plane |
| 📄 03 Data Plane Components | ✅ Complete | Runtime components |
| 📄 04 Storage Initializer | ✅ Complete | Model loading |
| 📄 05 Predictor Runtime | ✅ Complete | Model serving |
| 📄 06 Transformer | 🔜 Coming | Pre/Post-processing |
| 📄 07 Explainer | 🔜 Coming | Interpretability |
| 📄 08 InferenceGraph | 🔜 Coming | Routing, Pipelines |
| 📄 09 ModelMesh | 🔜 Coming | Multi-model serving |
| 📄 10 Knative | 🔜 Coming | Serverless |
| 📄 11 Autoscaling | 🔜 Coming | Scaling mechanisms |
| 📄 12 Protocols | 🔜 Coming | V1, V2, OpenAI |

## 🎓 Learning Paths

### Path 1: Quick Deployment (30 minutes)
```
Overall Architecture (10m) 
    ↓
Predictor Runtime (10m)
    ↓
Storage Initializer (10m)
    ↓
Deploy your first model!
```

### Path 2: Full Understanding (2 hours)
```
Overall Architecture (15m)
    ↓
InferenceService Controller (30m)
    ↓
Data Plane Components (30m)
    ↓
Storage Initializer (20m)
    ↓
Predictor Runtime (25m)
    ↓
Expert level!
```

### Path 3: LLM Specialist (1 hour)
```
Overall Architecture → Generative AI (15m)
    ↓
Predictor Runtime → LLM Features (30m)
    ↓
Storage Initializer → Large Models (15m)
    ↓
Deploy LLMs!
```

## 🚦 Getting Started Checklist

- [ ] Read [Overall Architecture](./01-KSERVE-OVERALL-ARCHITECTURE.md)
- [ ] Understand deployment modes
- [ ] Choose your serving runtime
- [ ] Configure storage for your model
- [ ] Review [Predictor Runtime](./05-PREDICTOR-RUNTIME.md) for your framework
- [ ] Deploy your first InferenceService
- [ ] Test inference endpoint
- [ ] Set up monitoring
- [ ] Configure autoscaling
- [ ] Deploy to production!

## 🔗 External Resources

### Official Documentation
- [KServe Website](https://kserve.github.io/website/)
- [KServe GitHub](https://github.com/kserve/kserve)
- [Getting Started Guide](https://kserve.github.io/website/docs/getting-started)

### Related Projects
- [OpenDataHub KServe](https://github.com/opendatahub-io/kserve)
- [Knative Serving](https://knative.dev/docs/serving/)
- [ModelMesh](https://github.com/kserve/modelmesh-serving)

## 💡 Tips for Using This Documentation

1. **Start with the flowcharts**: Visual understanding first
2. **Follow the links**: Documentation is interconnected
3. **Use the search guide**: In README.md
4. **Check "Related Components"**: At the end of each doc
5. **Refer to examples**: YAML specs provided throughout

## ❓ FAQ Navigation

**Q: How do I deploy an LLM?**
→ [Overall Architecture](./01-KSERVE-OVERALL-ARCHITECTURE.md) → Generative AI
→ [Predictor Runtime](./05-PREDICTOR-RUNTIME.md) → LLM Features

**Q: How does autoscaling work?**
→ [Overall Architecture](./01-KSERVE-OVERALL-ARCHITECTURE.md) → Autoscaling
→ Coming: Autoscaling Mechanisms

**Q: How do I load models from S3?**
→ [Storage Initializer](./04-STORAGE-INITIALIZER.md) → S3 Download Flow

**Q: What's the difference between deployment modes?**
→ [Overall Architecture](./01-KSERVE-OVERALL-ARCHITECTURE.md) → Deployment Modes

**Q: How do I add pre-processing?**
→ Coming: [Transformer Component](./06-TRANSFORMER-COMPONENT.md)

---

**Ready to dive in?** Start with the [Overall Architecture](./01-KSERVE-OVERALL-ARCHITECTURE.md)!

