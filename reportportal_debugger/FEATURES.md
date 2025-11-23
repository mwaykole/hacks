# ReportPortal Debugger - Feature Documentation

## Overview

This tool suite provides comprehensive debugging and analysis capabilities for ReportPortal test results, leveraging the official ReportPortal API and AI-powered pattern recognition.

---

## 🎯 Core Features

### 1. Automated Test Failure Fetching

- **API Integration**: Uses official ReportPortal REST API v1
- **Launch Detection**: Automatically finds the latest launch or processes specific launch ID
- **Batch Processing**: Handles multiple failed tests efficiently
- **Real-time Monitoring**: Can be integrated into CI/CD pipelines

**How it works:**
```python
# Fetches all failed tests from a launch
GET /api/v1/{project}/item?filter.eq.launchId={id}&filter.in.status=FAILED
```

### 2. AI-Powered Root Cause Analysis

#### Pattern Recognition System

The RCA engine uses weighted pattern matching across multiple categories:

**Product Bugs (pb001)**
- Assertion failures
- Validation errors
- Incorrect business logic results
- API response mismatches

**Automation Bugs (ab001)**
- Element not found errors
- Timeout issues
- Stale element references
- Locator failures

**System Issues (si001)**
- Network connectivity problems
- Database errors
- Service unavailability (503, 502, 504)
- Infrastructure failures

**To Investigate (ti001)**
- Unknown error patterns
- Low confidence classifications
- Complex multi-cause failures

#### Confidence Scoring

The engine provides confidence levels based on pattern matches:
- **High**: 3+ strong pattern matches (score ≥ 8)
- **Medium**: 2-3 pattern matches (score 4-7)
- **Low**: 0-1 pattern matches (score < 4)

### 3. Advanced Analysis Engine

Located in `advanced_rca.py`, provides:

**Comprehensive Analysis**
```python
analysis = engine.analyze_comprehensive(
    test_name="test_login",
    error_message="Connection timeout",
    logs=log_entries,
    stack_trace=trace,
    test_history=history_data  # Optional
)
```

**Output includes:**
- Defect type classification
- Confidence score
- Primary failure indicators
- Detailed log analysis
- Contextual recommendations

**Historical Pattern Learning**
- Tracks previous failures of the same test
- Boosts confidence for recurring patterns
- Identifies flaky vs persistent issues

### 4. Batch Analysis

Located in `batch_analyzer.py`, enables:

**Multiple Launch Analysis**
```bash
python batch_analyzer.py
# Options:
# 1. Analyze last N launches
# 2. Analyze by date range
```

**Features:**
- Process 5-50 launches in one run
- Aggregate statistics across launches
- Identify trends over time
- Export comprehensive JSON reports

**Output:**
- Total failures across all launches
- Defect category breakdown
- Flaky test identification
- Persistent failure tracking

### 5. Flaky Test Detection

**Definition**: Tests that fail intermittently with different root causes

**Detection Method:**
- Analyzes same test across multiple launches
- Identifies tests with varying defect types
- Flags tests failing in ≥2 launches with different classifications

**Use Case:**
```
Test: test_checkout_process
Launch 1: ab001 (Automation Bug)
Launch 2: pb001 (Product Bug)
Launch 3: si001 (System Issue)
→ FLAGGED as Flaky Test
```

### 6. Persistent Failure Tracking

**Definition**: Tests that consistently fail with same root cause

**Detection Method:**
- Tracks tests failing in ≥3 consecutive launches
- Same defect category across failures
- Sorted by failure frequency

**Use Case:**
```
Test: test_payment_validation
Launch 1: pb001 (Product Bug)
Launch 2: pb001 (Product Bug)
Launch 3: pb001 (Product Bug)
→ FLAGGED as Persistent Failure (requires immediate attention)
```

### 7. Auto-Update Defect Types

**How it works:**
1. Analyzes failed test
2. Determines defect type with confidence
3. Updates ReportPortal via API:
   ```python
   PUT /api/v1/{project}/item/{id}/update
   {
     "issues": [
       {
         "issueType": "pb001",
         "comment": "Auto-RCA: Product Bug (Confidence: high)"
       }
     ]
   }
   ```

**Safety:**
- Only updates when confidence is medium/high
- Adds comment with RCA reasoning
- Can be disabled (RP_AUTO_UPDATE=false)

### 8. Actionable Recommendations

Each analysis provides context-specific debugging steps:

**Example for Product Bug:**
```
🔍 Review the assertion/validation logic
📊 Compare expected vs actual values
🔄 Check for recent changes in business logic
🧪 Reproduce the issue manually
📝 Verify test data correctness
```

**Example for Automation Bug:**
```
🎯 Update element locators to be more stable
⏱️ Add appropriate wait conditions
🔧 Check if UI structure has changed
💻 Review browser/driver versions
```

### 9. Rich Terminal UI

When `rich` library is installed:
- **Colored output** for better readability
- **Progress indicators** during analysis
- **Formatted tables** for summaries
- **Interactive prompts** in interactive mode

### 10. Export & Reporting

**JSON Reports**
```json
{
  "generated_at": "2025-11-07T10:30:00",
  "summary": {
    "total_launches": 10,
    "total_failed_tests": 45,
    "defect_breakdown": {
      "Product Bug": 20,
      "Automation Bug": 15,
      "System Issue": 10
    },
    "flaky_tests": [...],
    "persistent_failures": [...]
  },
  "detailed_results": [...]
}
```

---

## 🔧 Usage Scenarios

### Scenario 1: Daily Test Failure Review
```bash
# Every morning, analyze latest test run
python rp_debugger.py

# Review failures, update defect types
# Generate report for team standup
```

### Scenario 2: Weekly Batch Analysis
```bash
# Every Monday, analyze last week
python batch_analyzer.py
# Select option 2 (date range)
# Enter: 2025-11-01 to 2025-11-07

# Identify trends, flaky tests, persistent issues
# Share batch_report.json with team
```

### Scenario 3: CI/CD Integration
```bash
# In CI pipeline after test execution
export RP_AUTO_UPDATE=true
python rp_debugger.py

# Automatically categorize all failures
# Generate report artifact
```

### Scenario 4: Historical Analysis
```bash
# Analyze last month's launches
python batch_analyzer.py
# Select option 1
# Enter: 30

# Identify most problematic tests
# Track quality trends
```

---

## 📊 Metrics & Statistics

The tool provides several key metrics:

### Per-Launch Metrics
- Total tests failed
- Defect type distribution
- Confidence level breakdown
- Most common error patterns

### Batch Metrics
- Failure trends over time
- Flaky test count
- Persistent failure count
- Category percentages
- Top failing tests

---

## 🔐 Security Features

- ✅ API token authentication (no passwords)
- ✅ Environment variable configuration
- ✅ .gitignore for credentials
- ✅ HTTPS-only API calls
- ✅ Token revocable from ReportPortal UI

---

## 🚀 Performance

- **Single launch**: ~2-5 seconds
- **10 launches**: ~30-60 seconds
- **API rate limits**: Respects ReportPortal limits
- **Concurrent requests**: Uses session pooling

---

## 🔌 Integration

### With CI/CD
```yaml
# GitHub Actions example
- name: Analyze Test Failures
  run: |
    cd reportportal_debugger
    python rp_debugger.py
    cat rca_report.json
```

### With Slack/Teams
Combine with notification tools to send analysis results.

### With JIRA
Export defect types that can be synced with JIRA via ReportPortal plugins.

---

## 📚 References

- [ReportPortal Official GitHub](https://github.com/reportportal)
- [ReportPortal API Documentation](https://developers.reportportal.io/api-docs/)
- [ReportPortal Documentation](https://github.com/reportportal/docs)

---

## 🆘 Support

For issues or questions:
1. Check `README.md` for common issues
2. Review `QUICKSTART.md` for setup help
3. Verify API token has correct permissions
4. Check ReportPortal service status


