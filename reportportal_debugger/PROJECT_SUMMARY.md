# ReportPortal Debugger - Project Summary

## 📁 Project Structure

```
reportportal_debugger/
├── 🐍 Core Tools
│   ├── rp_debugger.py          # Main debugger (single launch analysis)
│   ├── batch_analyzer.py       # Batch analysis (multiple launches)
│   ├── advanced_rca.py         # Advanced RCA engine
│   └── interactive_debug.py    # Interactive setup & debugging
│
├── ⚙️ Configuration
│   ├── .env                    # Your credentials (create from template)
│   ├── config_template.env    # Template for .env
│   └── requirements.txt        # Python dependencies
│
├── 🛠️ Setup
│   └── setup.sh               # Quick setup script
│
├── 📚 Documentation
│   ├── README.md              # Main documentation
│   ├── QUICKSTART.md          # Quick start guide
│   ├── FEATURES.md            # Detailed feature documentation
│   └── PROJECT_SUMMARY.md     # This file
│
└── 🔒 Security
    └── .gitignore            # Prevents credential commits
```

---

## 🚀 Quick Start (3 Steps)

### Option A: Interactive Setup (Easiest)
```bash
cd /home/mwaykole/project/hacks/reportportal_debugger
python interactive_debug.py
```
→ It will guide you through setup and start debugging!

### Option B: Manual Setup
```bash
cd /home/mwaykole/project/hacks/reportportal_debugger

# 1. Setup
./setup.sh

# 2. Configure (edit with your credentials)
nano .env

# 3. Run
python rp_debugger.py
```

---

## 🎯 What Each Tool Does

### 1. `rp_debugger.py` - Main Debugger
**Purpose**: Analyze failed tests from a single launch

**When to use**: 
- Daily test failure review
- After each test run
- CI/CD integration

**Features**:
- Fetches latest (or specific) launch
- Analyzes all failed tests
- Provides RCA for each failure
- Suggests debugging steps
- Can auto-update defect types

**Example**:
```bash
# Analyze latest launch
python rp_debugger.py

# Analyze specific launch
RP_LAUNCH_ID=abc123 python rp_debugger.py

# Auto-update defect types
RP_AUTO_UPDATE=true python rp_debugger.py
```

**Output**:
```
🔍 DEBUGGING: test_user_login
================================================================================
📊 ROOT CAUSE ANALYSIS:
   Category: Product Bug
   Defect Type: pb001
   Confidence: HIGH

💡 DEBUG SUGGESTIONS:
   🐛 Verify the expected vs actual values
   📝 Check if business logic has changed
   ...

📈 SUMMARY
Total Failed Tests: 5
  Product Bug: 2
  Automation Bug: 2
  System Issue: 1
```

---

### 2. `batch_analyzer.py` - Batch Analysis
**Purpose**: Analyze multiple launches for trends and patterns

**When to use**:
- Weekly/monthly reviews
- Identifying flaky tests
- Tracking persistent failures
- Quality trend analysis

**Features**:
- Analyze last N launches
- Analyze by date range
- Detect flaky tests
- Track persistent failures
- Export JSON reports

**Example**:
```bash
python batch_analyzer.py

# Choose option:
# 1. Last 10 launches
# 2. Date range (2025-11-01 to 2025-11-07)
```

**Output**:
```
BATCH ANALYSIS SUMMARY
================================================================================
Total Launches Analyzed: 10
Total Failed Tests: 45

Defect Breakdown:
  Product Bug: 20 (44.4%)
  Automation Bug: 15 (33.3%)
  System Issue: 10 (22.2%)

🔄 Flaky Tests Detected: 3
  - test_checkout_process (failed 5 times)
  - test_payment_gateway (failed 4 times)

⚠️  Persistent Failures: 2
  - test_login_validation (Product Bug, 8 failures)
  - test_api_timeout (System Issue, 6 failures)

✅ Report exported to: batch_report.json
```

---

### 3. `advanced_rca.py` - RCA Engine
**Purpose**: Advanced analysis engine for programmatic use

**When to use**:
- Building custom tools
- Integration with other systems
- Advanced debugging scenarios

**Features**:
- Weighted pattern matching
- Confidence scoring
- Historical analysis
- Keyword analysis
- Contextual recommendations

**Example**:
```python
from advanced_rca import AdvancedRCAEngine

engine = AdvancedRCAEngine()
result = engine.analyze_comprehensive(
    test_name="test_login",
    error_message="Connection timeout",
    logs=log_entries,
    stack_trace=trace,
    test_history=history
)

print(f"Category: {result['category']}")
print(f"Confidence: {result['confidence']}")
print(f"Score: {result['confidence_score']}")
print(f"Recommendations: {result['recommendations']}")
```

---

### 4. `interactive_debug.py` - Interactive Mode
**Purpose**: User-friendly guided debugging

**When to use**:
- First time setup
- Users unfamiliar with command line
- Quick debugging without config files

**Features**:
- Guided credential setup
- Interactive configuration
- Automatic validation
- Seamless transition to debugging

**Example**:
```bash
python interactive_debug.py

# It will ask for:
# - ReportPortal URL
# - API Token
# - Project Name
# - Auto-update preference

# Then automatically starts debugging!
```

---

## 🧠 How RCA Analysis Works

### Pattern Matching System

The engine uses **weighted pattern matching** across three main categories:

#### 1. Product Bug Patterns (pb001)
```python
Patterns with weights:
- "assertion failed"         → 3 points
- "expected X but got Y"     → 3 points
- "incorrect value"          → 2 points
- "validation error"         → 2 points
```

#### 2. Automation Bug Patterns (ab001)
```python
Patterns with weights:
- "element not found"        → 4 points
- "timeout waiting"          → 3 points
- "stale element"            → 4 points
- "selenium"                 → 3 points
```

#### 3. System Issue Patterns (si001)
```python
Patterns with weights:
- "connection refused"       → 4 points
- "503/502/504"             → 4 points
- "network error"           → 3 points
- "database error"          → 3 points
```

### Confidence Scoring

```
High Confidence:   Score ≥ 8  (3+ strong patterns)
Medium Confidence: Score 4-7  (2-3 patterns)
Low Confidence:    Score < 4  (0-1 patterns)
```

### Analysis Process

```
1. Combine all text sources
   ├── Test name
   ├── Error message
   ├── Stack trace
   └── Log entries (up to 10)

2. Score against all patterns
   └── Calculate total points per category

3. Analyze additional factors
   ├── Keyword frequency
   ├── Historical patterns (if available)
   └── Log severity levels

4. Determine defect type
   └── Highest scoring category wins

5. Generate recommendations
   └── Context-specific debugging steps
```

---

## 📊 Integration Examples

### CI/CD Integration (GitHub Actions)

```yaml
name: Analyze Test Failures

on:
  workflow_run:
    workflows: ["Run Tests"]
    types: [completed]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          cd reportportal_debugger
          pip install -r requirements.txt
      
      - name: Run RCA Analysis
        env:
          RP_BASE_URL: ${{ secrets.RP_BASE_URL }}
          RP_API_TOKEN: ${{ secrets.RP_API_TOKEN }}
          RP_PROJECT_NAME: ${{ secrets.RP_PROJECT_NAME }}
          RP_AUTO_UPDATE: true
        run: |
          cd reportportal_debugger
          python rp_debugger.py
      
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: rca-report
          path: reportportal_debugger/*.json
```

### Cron Job (Daily Analysis)

```bash
# Add to crontab (crontab -e)
0 9 * * * cd /home/mwaykole/project/hacks/reportportal_debugger && python rp_debugger.py >> /var/log/rp_debug.log 2>&1
```

### Python Script Integration

```python
import os
from rp_debugger import RPConfig, RPDebugger

# Configure
config = RPConfig(
    base_url=os.getenv("RP_BASE_URL"),
    api_token=os.getenv("RP_API_TOKEN"),
    project_name=os.getenv("RP_PROJECT_NAME")
)

# Create debugger
debugger = RPDebugger(config)

# Analyze
results = debugger.debug_launch(auto_update=True)

# Process results
for result in results:
    print(f"Test: {result['test_name']}")
    print(f"Category: {result['analysis']['category']}")
    print(f"Confidence: {result['analysis']['confidence']}")
```

---

## 🔐 Security Best Practices

### ✅ DO
- Use API tokens (not passwords)
- Store credentials in `.env` file
- Keep `.env` in `.gitignore`
- Rotate tokens periodically
- Use environment variables in CI/CD
- Restrict token permissions in ReportPortal

### ❌ DON'T
- Commit `.env` to git
- Share tokens in plain text
- Use admin tokens for automation
- Hardcode credentials in scripts
- Use same token across environments

### Getting API Token Safely

1. Login to ReportPortal
2. Click profile icon (top right)
3. Navigate to: **Profile → API Keys**
4. Click **Generate** or copy existing token
5. Save to `.env` file (never commit!)

---

## 📈 Metrics & Reports

### Per-Launch Metrics
- Total failed tests
- Defect type distribution
- Confidence level breakdown
- Most common patterns

### Batch Analysis Metrics
- Failure trends over time
- Flaky test identification
- Persistent failure tracking
- Quality trend analysis
- Top failing tests

### JSON Report Structure
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
    "flaky_tests": [
      {
        "test_name": "test_checkout",
        "failure_count": 5,
        "defect_types": ["ab001", "pb001", "si001"]
      }
    ],
    "persistent_failures": [
      {
        "test_name": "test_login",
        "failure_count": 8,
        "category": "Product Bug"
      }
    ]
  },
  "detailed_results": [...]
}
```

---

## 🆘 Common Issues & Solutions

### Issue: Connection Failed
**Solution**:
```bash
# Test connection manually
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-rp-url.com/api/v1/user

# Check if you get 200 OK
```

### Issue: No Failed Tests Found
**Possible causes**:
- Launch has no failures (good news!)
- Wrong project name (case-sensitive!)
- No read permissions
- Wrong launch ID

### Issue: Import Error
**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

### Issue: Update Failed
**Possible causes**:
- No write permissions in ReportPortal
- Defect types don't exist in your project
- Invalid defect type codes

**Solution**: Check ReportPortal admin settings for defect types

---

## 📚 Additional Resources

- [ReportPortal GitHub](https://github.com/reportportal)
- [ReportPortal API Docs](https://developers.reportportal.io/api-docs/)
- [ReportPortal Documentation](https://github.com/reportportal/docs)
- [ReportPortal Community](https://slack.epmrpp.reportportal.io/)

---

## 🎯 Next Steps

1. **Setup**: Run `./setup.sh` or `python interactive_debug.py`
2. **Configure**: Add your credentials to `.env`
3. **Test**: Run `python rp_debugger.py` on latest launch
4. **Explore**: Try batch analysis with `python batch_analyzer.py`
5. **Integrate**: Add to your CI/CD pipeline
6. **Customize**: Modify patterns in `advanced_rca.py` for your needs

---

## 📝 Notes

- All tools are in: `/home/mwaykole/project/hacks/reportportal_debugger/`
- Based on official ReportPortal API v1
- Compatible with Python 3.7+
- No external dependencies beyond Python packages
- Fully open source and customizable

---

**Created**: November 2025  
**Version**: 1.0.0  
**License**: Use freely for debugging your ReportPortal tests!


