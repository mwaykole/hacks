# ReportPortal Debugger - Usage Examples

Real-world examples of how to use the ReportPortal Debugger tools.

---

## Example 1: First Time Setup

**Scenario**: You just cloned the project and want to start debugging.

```bash
cd /home/mwaykole/project/hacks/reportportal_debugger

# Interactive setup (easiest)
python interactive_debug.py
```

**What happens**:
1. Asks for ReportPortal URL: `https://rp.mycompany.com`
2. Asks for API Token: `abc123-def456-...`
3. Asks for Project Name: `qa_automation`
4. Creates `.env` file
5. Automatically starts debugging your latest launch!

---

## Example 2: Daily Morning Routine

**Scenario**: Every morning, check yesterday's test failures.

```bash
cd /home/mwaykole/project/hacks/reportportal_debugger

# Analyze latest launch
python rp_debugger.py
```

**Output**:
```
✅ Connected to ReportPortal successfully!
✅ Found Launch: Nightly Regression (#142)
⚠️  Found 8 failed test(s)

[1/8] 🔍 DEBUGGING: test_user_authentication
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
   - incorrect.*value

💥 Error Message:
   AssertionError: Expected status code 401 but got 200

💡 DEBUG SUGGESTIONS:
   🔍 Review the assertion/validation logic
   📊 Compare expected vs actual values
   🔄 Check for recent changes in business logic
   🧪 Reproduce the issue manually
   📝 Verify test data correctness
```

**Action**: Review the product bug, fix it, create JIRA ticket.

---

## Example 3: Auto-Update Defect Types

**Scenario**: You want the tool to automatically update defect types in ReportPortal.

```bash
cd /home/mwaykole/project/hacks/reportportal_debugger

# Enable auto-update
RP_AUTO_UPDATE=true python rp_debugger.py
```

**What happens**:
1. Analyzes each failed test
2. Determines defect type (pb001, ab001, si001, ti001)
3. Updates ReportPortal via API
4. Adds comment: "Auto-RCA: Product Bug (Confidence: high)"

**Result**: All your failed tests are now categorized automatically!

---

## Example 4: Analyze Specific Launch

**Scenario**: You want to debug a specific test launch, not just the latest.

```bash
cd /home/mwaykole/project/hacks/reportportal_debugger

# Method 1: Environment variable
RP_LAUNCH_ID=5f4dcc3b5aa765d61d8327de python rp_debugger.py

# Method 2: Edit .env file
nano .env
# Add: RP_LAUNCH_ID=5f4dcc3b5aa765d61d8327de
python rp_debugger.py
```

---

## Example 5: Weekly Batch Analysis

**Scenario**: Every Monday, analyze last week's test results to identify trends.

```bash
cd /home/mwaykole/project/hacks/reportportal_debugger

python batch_analyzer.py
```

**Interactive prompts**:
```
🔧 ReportPortal Batch Analyzer

Options:
  1. Analyze last N launches
  2. Analyze date range

Enter choice (1 or 2): 2
Start date (YYYY-MM-DD): 2025-11-01
End date (YYYY-MM-DD): 2025-11-07
```

**Output**:
```
BATCH ANALYSIS SUMMARY
================================================================================
Total Launches Analyzed: 12
Total Failed Tests: 67

Defect Breakdown:
  Product Bug: 30 (44.8%)
  Automation Bug: 22 (32.8%)
  System Issue: 15 (22.4%)

🔄 Flaky Tests Detected: 5
  - test_payment_gateway (failed 6 times)
  - test_checkout_process (failed 5 times)
  - test_user_profile (failed 4 times)

⚠️  Persistent Failures: 3
  - test_api_authentication (Product Bug, 10 failures)
  - test_database_connection (System Issue, 8 failures)
  - test_ui_rendering (Automation Bug, 7 failures)

✅ Report exported to: batch_report.json
```

**Action**: 
- Fix the persistent failures first (highest priority)
- Investigate flaky tests for intermittent issues
- Share `batch_report.json` with team

---

## Example 6: CI/CD Integration

**Scenario**: Automatically analyze test failures after every test run in CI.

### GitHub Actions

```yaml
# .github/workflows/test-and-analyze.yml
name: Test and Analyze

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run Tests
        run: |
          # Your test execution here
          pytest --reportportal
      
      - name: Analyze Failures
        env:
          RP_BASE_URL: ${{ secrets.RP_BASE_URL }}
          RP_API_TOKEN: ${{ secrets.RP_API_TOKEN }}
          RP_PROJECT_NAME: ${{ secrets.RP_PROJECT_NAME }}
          RP_AUTO_UPDATE: true
        run: |
          cd reportportal_debugger
          pip install -r requirements.txt
          python rp_debugger.py
      
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: rca-report
          path: reportportal_debugger/*.json
```

### GitLab CI

```yaml
# .gitlab-ci.yml
analyze_failures:
  stage: analyze
  script:
    - cd reportportal_debugger
    - pip install -r requirements.txt
    - python rp_debugger.py
  variables:
    RP_AUTO_UPDATE: "true"
  artifacts:
    paths:
      - reportportal_debugger/*.json
```

---

## Example 7: Scheduled Daily Analysis

**Scenario**: Run analysis every day at 9 AM automatically.

```bash
# Add to crontab
crontab -e

# Add this line:
0 9 * * * cd /home/mwaykole/project/hacks/reportportal_debugger && /usr/bin/python3 rp_debugger.py >> /var/log/rp_debug.log 2>&1
```

**What happens**:
- Runs every day at 9:00 AM
- Analyzes latest launch
- Logs output to `/var/log/rp_debug.log`
- Can be reviewed later

---

## Example 8: Custom Python Script

**Scenario**: You want to integrate RCA into your own Python tool.

```python
#!/usr/bin/env python3
"""Custom ReportPortal Analysis Script"""

import os
import sys
sys.path.append('/home/mwaykole/project/hacks/reportportal_debugger')

from rp_debugger import ReportPortalClient, RPConfig
from advanced_rca import AdvancedRCAEngine

# Configure
config = RPConfig(
    base_url="https://rp.mycompany.com",
    api_token="your-api-token",
    project_name="qa_automation"
)

# Create client and engine
client = ReportPortalClient(config)
engine = AdvancedRCAEngine()

# Get latest launch
launch = client.get_latest_launch()
launch_id = launch["id"]

# Get failed tests
failed_tests = client.get_failed_tests(launch_id)

# Analyze each
for test in failed_tests:
    test_id = test["id"]
    test_name = test["name"]
    logs = client.get_test_logs(test_id)
    
    # Get error
    error = test.get("issue", {}).get("comment", "")
    
    # Analyze
    analysis = engine.analyze_comprehensive(
        test_name=test_name,
        error_message=error,
        logs=logs
    )
    
    # Process result
    if analysis["confidence"] == "high":
        print(f"✅ {test_name}: {analysis['category']}")
        
        # Auto-update in ReportPortal
        client.update_defect_type(
            test_id,
            analysis["defect_type"],
            f"Auto-RCA: {analysis['category']}"
        )
    else:
        print(f"⚠️  {test_name}: Manual review needed")

print("\n✅ Analysis complete!")
```

---

## Example 9: Finding Flaky Tests

**Scenario**: You suspect some tests are flaky and want to confirm.

```bash
cd /home/mwaykole/project/hacks/reportportal_debugger

python batch_analyzer.py
# Choose: 1. Analyze last N launches
# Enter: 20
```

**Look for**:
```
🔄 Flaky Tests Detected: 8
  - test_async_operations (failed 12 times with different causes)
    Defect types: ['ab001', 'pb001', 'si001', 'ab001', 'si001', ...]
```

**Action**: These tests fail with different root causes - likely flaky!
- Add better waits
- Fix race conditions
- Stabilize test environment

---

## Example 10: Monthly Quality Report

**Scenario**: Generate a comprehensive quality report for management.

```bash
cd /home/mwaykole/project/hacks/reportportal_debugger

python batch_analyzer.py
# Choose: 1. Analyze last N launches
# Enter: 50

# Export generates: batch_report.json
```

**Process the report**:
```python
import json

with open('batch_report.json') as f:
    data = json.load(f)

summary = data['analysis']['summary']

print(f"Quality Metrics - {data['generated_at']}")
print(f"="*50)
print(f"Total Test Runs: {summary['total_launches']}")
print(f"Total Failures: {summary['total_failed_tests']}")
print(f"\nDefect Distribution:")
for category, count in summary['defect_breakdown'].items():
    pct = count / summary['total_failed_tests'] * 100
    print(f"  {category}: {count} ({pct:.1f}%)")

print(f"\nFlaky Tests: {len(summary['flaky_tests'])}")
print(f"Persistent Issues: {len(summary['persistent_failures'])}")
```

---

## Example 11: Debugging After Release

**Scenario**: You released yesterday and want to check today's test results.

```bash
cd /home/mwaykole/project/hacks/reportportal_debugger

# Analyze today's launches
python batch_analyzer.py
# Choose: 2. Analyze date range
# Start: 2025-11-07
# End: 2025-11-07
```

**Compare with pre-release**:
```bash
# Analyze previous day
python batch_analyzer.py
# Choose: 2. Analyze date range
# Start: 2025-11-06
# End: 2025-11-06
```

**Action**: Compare the two reports to see if release introduced new failures.

---

## Example 12: Team Collaboration

**Scenario**: Share analysis results with your team.

```bash
cd /home/mwaykole/project/hacks/reportportal_debugger

# Run batch analysis
python batch_analyzer.py

# Export creates: batch_report.json

# Share with team via Slack/Email/Teams
# Or commit to git (report only, not .env!)
git add batch_report.json
git commit -m "Weekly test analysis - Nov 7, 2025"
git push
```

**Team reviews**:
- Product Bugs → Dev team
- Automation Bugs → QA team
- System Issues → DevOps team
- Flaky Tests → Joint investigation

---

## Tips & Best Practices

### ✅ DO
- Run analysis daily for quick feedback
- Use auto-update for time savings
- Review batch reports weekly
- Track flaky tests and fix them
- Share reports with team
- Keep credentials in `.env` only

### ❌ DON'T
- Ignore persistent failures
- Commit `.env` to git
- Share API tokens
- Run batch analysis too frequently (API limits)
- Skip manual review of low-confidence results

---

## Keyboard Shortcuts

```bash
# Quick daily analysis
alias rpd='cd /home/mwaykole/project/hacks/reportportal_debugger && python rp_debugger.py'

# Quick batch analysis
alias rpb='cd /home/mwaykole/project/hacks/reportportal_debugger && python batch_analyzer.py'

# Interactive mode
alias rpi='cd /home/mwaykole/project/hacks/reportportal_debugger && python interactive_debug.py'

# Add to ~/.bashrc or ~/.zshrc
```

**Usage**:
```bash
rpd          # Run daily analysis
rpb          # Run batch analysis
rpi          # Interactive mode
```

---

## Questions?

- Check [README.md](README.md) for detailed docs
- See [FEATURES.md](FEATURES.md) for feature details
- Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for overview
- Review [QUICKSTART.md](QUICKSTART.md) for setup help


