# Component-Wise Documentation

## 📋 Navigation Guide

Welcome to the **Component-Wise Documentation**! This folder contains complete, flowchart-based documentation for each deployment mode and the overall system architecture.

---

## 📚 Available Documents

| Document | Description | Coverage | Difficulty |
|----------|-------------|----------|------------|
| **[OVERALL-FULL-FLOW.md](./OVERALL-FULL-FLOW.md)** | Complete system overview with all components and deployment mode comparison | 100% | ⭐⭐ Moderate |
| **[RAW-KUBERNETES-DEPLOYMENT.md](./RAW-KUBERNETES-DEPLOYMENT.md)** | Raw K8s deployment with all features and configurations | 100% | ⭐⭐ Moderate |
| **[SERVERLESS-DEPLOYMENT.md](./SERVERLESS-DEPLOYMENT.md)** | Serverless mode with Knative, autoscaling, and traffic management | 100% | ⭐⭐ Moderate |
| **[LLM-D-DEPLOYMENT.md](./LLM-D-DEPLOYMENT.md)** | LLM-D mode with P/D disaggregation, caching, and all advanced features | 100% | ⭐⭐⭐ Advanced |

---

## 🎯 Which Document Should I Read?

### I Want to Understand...

**The Overall System**
→ Start with [OVERALL-FULL-FLOW.md](./OVERALL-FULL-FLOW.md)
- System architecture
- All components explained
- Deployment mode comparison
- Decision trees for choosing modes

**Raw Kubernetes Deployment**
→ Read [RAW-KUBERNETES-DEPLOYMENT.md](./RAW-KUBERNETES-DEPLOYMENT.md)
- When to use Raw K8s
- Basic features (HPA, storage, multi-model)
- Simple deployment scenarios
- Best for traditional ML models

**Serverless Deployment**
→ Read [SERVERLESS-DEPLOYMENT.md](./SERVERLESS-DEPLOYMENT.md)
- Scale-to-zero capabilities
- Knative autoscaling
- Traffic splitting (canary, blue-green)
- InferenceGraph pipelines
- Best for variable traffic patterns

**LLM Deployment (Advanced)**
→ Read [LLM-D-DEPLOYMENT.md](./LLM-D-DEPLOYMENT.md)
- All 5 LLM-D components
- Disaggregated prefill/decode
- KV-cache awareness
- Multi-node distributed inference
- Cost optimization for LLMs
- Best for large language models

---

## 🔍 Quick Feature Finder

### Looking for Specific Features?

| Feature | Found In | Page Ref |
|---------|----------|----------|
| **Autoscaling** | All docs | Throughout |
| **Scale-to-Zero** | Serverless, LLM-D | Core feature |
| **GPU Management** | Raw, Serverless, LLM-D | Resource sections |
| **Multi-Model Serving** | Raw, Serverless | Multi-model sections |
| **InferenceGraph** | Serverless | Pipeline section |
| **Traffic Splitting** | Serverless | Traffic mgmt |
| **Caching** | LLM-D | Routing section |
| **Prefill/Decode** | LLM-D | P/D section |
| **KV-Cache** | LLM-D | KV-Cache Manager |
| **Distributed Inference** | LLM-D | Multi-node section |
| **Cost Optimization** | All docs | Optimization sections |
| **Failover & Retry** | All docs | Troubleshooting |

---

## 📖 Reading Order Recommendations

### For Beginners
1. Start with main folder's [SIMPLE-ARCHITECTURE-FLOWS.md](../SIMPLE-ARCHITECTURE-FLOWS.md)
2. Then read [OVERALL-FULL-FLOW.md](./OVERALL-FULL-FLOW.md)
3. Pick deployment mode: [RAW](./RAW-KUBERNETES-DEPLOYMENT.md) or [SERVERLESS](./SERVERLESS-DEPLOYMENT.md)

### For LLM Practitioners
1. Read [OVERALL-FULL-FLOW.md](./OVERALL-FULL-FLOW.md) (focus on LLM-D section)
2. Deep dive into [LLM-D-DEPLOYMENT.md](./LLM-D-DEPLOYMENT.md)
3. Also see main folder's [LLM-D-ISVC-FLOWS.md](../LLM-D-ISVC-FLOWS.md) for code-level details

### For Platform Engineers
1. [OVERALL-FULL-FLOW.md](./OVERALL-FULL-FLOW.md) for system understanding
2. All three deployment docs based on your requirements
3. Main folder's [TECHNICAL-REFERENCE.md](../TECHNICAL-REFERENCE.md) for configurations

---

## 🎨 Documentation Style

All documents in this folder follow these principles:

### ✅ What You'll Find
- **Flowcharts Only** - No sequence diagrams, all flows use flowcharts
- **Simple Language** - Technical but easy to understand
- **Complete Coverage** - Every feature explained
- **Real Examples** - Configuration YAMLs for every feature
- **Visual Diagrams** - Heavy use of Mermaid flowcharts

### ❌ What You Won't Find
- Complex jargon without explanation
- Incomplete feature lists
- Missing configuration examples
- Sequence diagrams (we use flowcharts instead)

---

## 🔗 Related Documentation

**In Main Folder (`documant flow/`)**:
- [SIMPLE-ARCHITECTURE-FLOWS.md](../SIMPLE-ARCHITECTURE-FLOWS.md) - Easiest to understand (start here!)
- [ODH-ML-SERVING-ARCHITECTURE.md](../ODH-ML-SERVING-ARCHITECTURE.md) - Complete architectural overview
- [COMPLETE-INTEGRATION-DEEP-DIVE.md](../COMPLETE-INTEGRATION-DEEP-DIVE.md) - Detailed integration flows
- [LLM-D-ISVC-FLOWS.md](../LLM-D-ISVC-FLOWS.md) - LLM-D code-level documentation
- [TECHNICAL-REFERENCE.md](../TECHNICAL-REFERENCE.md) - Configuration examples & API specs
- [QUICK-REFERENCE-GUIDE.md](../QUICK-REFERENCE-GUIDE.md) - Decision matrices & comparisons

---

## 📊 Documentation Statistics

- **Total Documents**: 4
- **Total Flowcharts**: 60+
- **Total YAML Examples**: 80+
- **Total Features Covered**: 100%
- **Lines of Documentation**: ~10,000+

---

## 💡 Pro Tips

1. **Use the flowcharts** - They show the complete flow visually
2. **Copy the YAML examples** - All configs are production-ready
3. **Follow the examples** - Each feature has step-by-step instructions
4. **Check decision trees** - They help you choose the right approach

---

## ❓ Still Need Help?

1. Check the main [README.md](../README.md) in parent folder
2. Use the "Quick Feature Finder" above
3. All documents have detailed troubleshooting sections

---

**Happy Learning! 🚀**

*Last Updated: October 27, 2025*

