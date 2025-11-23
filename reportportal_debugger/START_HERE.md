# 🚀 START HERE - ReportPortal Debugger

## 👋 Welcome!

This tool will **automatically debug your ReportPortal test failures** using AI-powered Root Cause Analysis (RCA).

Based on the official [ReportPortal GitHub API](https://github.com/reportportal).

---

## ⚡ Quick Start (Choose One)

### Option 1: Interactive Setup (Recommended)
```bash
cd /home/mwaykole/project/hacks/reportportal_debugger
python interactive_debug.py
```
→ It will guide you through everything!

### Option 2: Manual Setup
```bash
cd /home/mwaykole/project/hacks/reportportal_debugger
./setup.sh
nano .env    # Add your credentials
python rp_debugger.py
```

---

## 📋 What You Need

Before starting, have these ready:

1. **ReportPortal URL**
   - Example: `https://rp.mycompany.com`
   - Don't include trailing slash

2. **API Token**
   - Get it from: ReportPortal → Profile → API Keys
   - Looks like: `abc123-def456-789...`

3. **Project Name**
   - Example: `qa_automation`, `my_project`
   - Case-sensitive!

---

## 🎯 What This Tool Does

### Main Features
✅ **Fetches** failed tests from ReportPortal automatically  
✅ **Analyzes** each failure using AI patterns  
✅ **Categorizes** failures:
   - 🐛 Product Bug (real bugs in your app)
   - 🤖 Automation Bug (test script issues)
   - 🖥️ System Issue (infrastructure problems)
   - 🔍 To Investigate (unknown issues)

✅ **Provides** debugging suggestions for each failure  
✅ **Updates** defect types in ReportPortal (optional)  
✅ **Generates** reports and statistics

### Advanced Features
📈 **Batch Analysis** - Analyze multiple test runs  
🔄 **Flaky Test Detection** - Find intermittent failures  
⚠️ **Persistent Failure Tracking** - Find recurring issues  
📅 **Historical Analysis** - Track trends over time

---

## 📁 Files in This Directory

### 🐍 Tools You'll Use
- `rp_debugger.py` - Main debugger (daily use)
- `batch_analyzer.py` - Analyze multiple launches
- `interactive_debug.py` - Easy setup & debugging

### 📚 Documentation
- `README.md` - Full documentation
- `QUICKSTART.md` - Quick setup guide
- `FEATURES.md` - Detailed feature list
- `USAGE_EXAMPLES.md` - Real-world examples
- `PROJECT_SUMMARY.md` - Complete overview
- **`START_HERE.md`** - This file

### ⚙️ Configuration
- `config_template.env` - Template for credentials
- `.env` - Your credentials (you'll create this)
- `requirements.txt` - Python packages
- `setup.sh` - Quick setup script

---

## 🎬 Example Session

```bash
$ python interactive_debug.py

🔧 ReportPortal Configuration Setup
================================================================================

Let's set up your ReportPortal connection.

Enter your ReportPortal URL: https://rp.mycompany.com
Enter your API Token: abc123-def456...
Enter your Project Name: qa_automation
Auto-update defect types? (y/n) [n]: y

✅ Configuration saved to .env
✅ Setup complete! Starting debugger...

🔧 ReportPortal Debugger - Automated RCA Tool
================================================================================

ℹ️  Testing connection to ReportPortal...
✅ Connected to ReportPortal successfully!
ℹ️  Fetching latest test launch...
✅ Found Launch: Nightly Regression (#142)
⚠️  Found 5 failed test(s)

================================================================================
[1/5] 🔍 DEBUGGING: test_user_login_with_invalid_credentials
================================================================================
Test ID: 5f4dcc3b5aa765d61d8327de

📊 ROOT CAUSE ANALYSIS:
   Category: Product Bug
   Defect Type: pb001
   Confidence: HIGH
   Reason: Matched 4 patterns

🎯 Matched Patterns:
   - assertion.*failed
   - expected.*but.*got

💥 Error Message:
   AssertionError: Expected status code 401 but got 200

💡 DEBUG SUGGESTIONS:
   🐛 Verify the expected vs actual values in the assertion
   📝 Check if business logic has changed recently
   🔍 Review recent code changes in the tested feature
   🧪 Try reproducing the issue manually
   📝 Verify test data correctness

🔄 Updating defect type in ReportPortal...
✅ Defect type updated successfully!

[... 4 more tests analyzed ...]

================================================================================
📈 SUMMARY
================================================================================

Total Failed Tests: 5
  Product Bug: 2
  Automation Bug: 2
  System Issue: 1

================================================================================
```

---

## 📖 Next Steps

1. **First Run**
   ```bash
   python interactive_debug.py
   ```

2. **Read Documentation**
   - Quick guide: `QUICKSTART.md`
   - Examples: `USAGE_EXAMPLES.md`
   - Full docs: `README.md`

3. **Daily Usage**
   ```bash
   python rp_debugger.py
   ```

4. **Weekly Analysis**
   ```bash
   python batch_analyzer.py
   ```

5. **Customize**
   - Edit patterns in `advanced_rca.py`
   - Adjust confidence thresholds
   - Add your own analysis logic

---

## 💡 Common Use Cases

### Daily Test Review
```bash
python rp_debugger.py
```
Review yesterday's failures, get RCA, update defect types.

### Weekly Team Meeting
```bash
python batch_analyzer.py
# Analyze last 7 days
```
Generate report showing trends, flaky tests, persistent failures.

### CI/CD Integration
Add to your pipeline to automatically categorize failures.

### Release Analysis
Compare test results before and after release.

---

## 🆘 Need Help?

### Quick Troubleshooting

**Connection Failed?**
```bash
# Test your token manually
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-rp-url.com/api/v1/user
```

**Import Error?**
```bash
pip install -r requirements.txt --upgrade
```

**No Failed Tests?**
- Check if launch actually has failures
- Verify project name is correct (case-sensitive)

### Get More Help
- Read: `README.md` → Troubleshooting section
- Examples: `USAGE_EXAMPLES.md`
- Features: `FEATURES.md`

---

## 🔐 Security Reminder

- ✅ Keep `.env` file secure (never commit to git!)
- ✅ Use API tokens (not passwords)
- ✅ Rotate tokens periodically
- ✅ `.gitignore` already includes `.env`

---

## 📊 Sample Output

### Main Debugger Output
```
📊 ROOT CAUSE ANALYSIS:
   Category: Product Bug          ← What type of issue
   Defect Type: pb001             ← ReportPortal code
   Confidence: HIGH               ← How sure we are

💡 DEBUG SUGGESTIONS:            ← What to do next
   🐛 Verify expected vs actual values
   📝 Check if business logic changed
   🔍 Review recent code changes
```

### Batch Analysis Output
```
BATCH ANALYSIS SUMMARY
Total Launches: 10
Total Failed Tests: 45

Defect Breakdown:
  Product Bug: 20 (44.4%)        ← Most failures are real bugs
  Automation Bug: 15 (33.3%)
  System Issue: 10 (22.2%)

🔄 Flaky Tests: 3                 ← Need attention
⚠️  Persistent Failures: 2        ← Urgent fixes needed
```

---

## 🎉 You're Ready!

Run this now:
```bash
python interactive_debug.py
```

It will:
1. ✅ Ask for your credentials
2. ✅ Save them securely
3. ✅ Connect to ReportPortal
4. ✅ Analyze your latest test failures
5. ✅ Show you what's wrong and how to fix it

**That's it!** 🚀

---

## 📚 Documentation Index

| Document | Purpose |
|----------|---------|
| **START_HERE.md** (this file) | Quick overview & getting started |
| QUICKSTART.md | Step-by-step setup guide |
| README.md | Complete documentation |
| FEATURES.md | Detailed feature descriptions |
| USAGE_EXAMPLES.md | Real-world examples |
| PROJECT_SUMMARY.md | Technical overview |

---

**Ready to debug?** Run `python interactive_debug.py` now! 🎯


