# ReportPortal Debugger

🤖 **AI-Powered RCA (Root Cause Analysis) tool for ReportPortal**

Based on the official [ReportPortal GitHub](https://github.com/reportportal) API structure and best practices.

## Features

### Core Features
- 🔍 **Automatically fetches failed tests** from ReportPortal via official API
- 🧠 **Advanced AI-powered RCA analysis** with confidence scoring
- 🎯 **Intelligent categorization** of failures:
  - **Product Bug** (pb001) - Real application bugs
  - **Automation Bug** (ab001) - Test automation issues
  - **System Issue** (si001) - Infrastructure/environment problems
  - **To Investigate** (ti001) - Unknown issues requiring manual review
- 💡 **Actionable debugging suggestions** for each failure
- ✅ **Auto-update defect types** in ReportPortal
- 📊 **Comprehensive statistics** and reports

### Advanced Features
- 📈 **Batch Analysis** - Analyze multiple launches at once
- 🔄 **Flaky Test Detection** - Identify intermittently failing tests
- ⚠️ **Persistent Failure Tracking** - Find tests that consistently fail
- 📅 **Historical Analysis** - Analyze launches by date range
- 📝 **JSON Report Export** - Export detailed analysis reports
- 🎨 **Rich Terminal UI** - Beautiful output with progress indicators

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure ReportPortal Connection

Create a `.env` file in this directory:

```bash
cp .env.example .env
```

Edit `.env` with your ReportPortal details:

```env
RP_BASE_URL=https://your-reportportal-url.com
RP_API_TOKEN=your_api_token_here
RP_PROJECT_NAME=your_project_name
RP_AUTO_UPDATE=false
```

### 3. Get Your API Token

1. Log into ReportPortal
2. Click on your profile (top right)
3. Go to **Profile** → **API Keys**
4. Generate/copy your API token

## Usage

### 1. Basic Debugging (Single Launch)

Debug the latest launch:

```bash
python rp_debugger.py
```

Debug specific launch:

```bash
RP_LAUNCH_ID=your-launch-id python rp_debugger.py
```

Enable auto-update of defect types:

```bash
RP_AUTO_UPDATE=true python rp_debugger.py
```

### 2. Interactive Mode

Guided setup and debugging:

```bash
python interactive_debug.py
```

### 3. Batch Analysis

Analyze multiple launches:

```bash
python batch_analyzer.py
```

Choose from:
- Analyze last N launches (e.g., last 10 launches)
- Analyze by date range (e.g., last week's launches)

Generates comprehensive reports with:
- Flaky test detection
- Persistent failure tracking
- Defect breakdown statistics
- Trend analysis

### 4. Advanced RCA Engine

For programmatic use:

```python
from advanced_rca import AdvancedRCAEngine

engine = AdvancedRCAEngine()
result = engine.analyze_comprehensive(
    test_name="test_login_invalid_credentials",
    error_message="AssertionError: Expected 401 but got 200",
    logs=log_entries,
    stack_trace=stack_trace
)

print(result["category"])  # Product Bug
print(result["recommendations"])  # List of debug steps
```

## Example Output

```
🔧 ReportPortal Debugger - Automated RCA Tool
================================================================================

ℹ️  Testing connection to ReportPortal...
✅ Connected to ReportPortal successfully!
ℹ️  Fetching latest test launch...
✅ Found Launch: Regression Suite (#42)
ℹ️  Fetching failed tests...
⚠️  Found 5 failed test(s)

================================================================================
[1/5] 🔍 DEBUGGING: test_user_login_with_invalid_credentials
================================================================================
Test ID: 5f4dcc3b5aa765d61d8327de
Fetched 12 log entries

📊 ROOT CAUSE ANALYSIS:
   Category: Product Bug
   Defect Type: pb001
   Confidence: HIGH
   Reason: Matched 3 patterns

🎯 Matched Patterns:
   - assertion.*failed
   - expected.*but.*got
   - incorrect.*value

💥 Error Message:
   AssertionError: Expected status code 401 but got 200

📋 Key Log Entries:
   - Login API returned 200 instead of expected 401
   - Invalid credentials were accepted
   - Security validation might be broken

💡 DEBUG SUGGESTIONS:
   🐛 Verify the expected vs actual values in the assertion
   📝 Check if business logic has changed recently
   🔍 Review recent code changes in the tested feature
   🧪 Try reproducing the issue manually
   📊 Check if the data/test environment is correct

================================================================================

📈 SUMMARY
================================================================================

Total Failed Tests: 5
  Automation Bug: 2
  Product Bug: 2
  System Issue: 1
```

## Defect Type Codes

| Code   | Category         | Description                          |
|--------|------------------|--------------------------------------|
| pb001  | Product Bug      | Real bugs in the application         |
| ab001  | Automation Bug   | Issues with test automation          |
| si001  | System Issue     | Infrastructure/environment problems  |
| ti001  | To Investigate   | Unknown issues needing manual review |
| nd001  | No Defect        | False positive or expected behavior  |

## Customization

You can customize the RCA patterns by editing the `DEFECT_PATTERNS` dictionary in `rp_debugger.py`.

## Security

- Never commit your `.env` file to version control
- Keep your API token secure
- Use API tokens instead of passwords
- Tokens can be revoked if compromised

## Tools Included

| Tool | Purpose | Usage |
|------|---------|-------|
| `rp_debugger.py` | Main debugger for single launch | `python rp_debugger.py` |
| `interactive_debug.py` | Interactive setup & debug | `python interactive_debug.py` |
| `batch_analyzer.py` | Batch analysis of multiple launches | `python batch_analyzer.py` |
| `advanced_rca.py` | Advanced RCA engine library | Import in your scripts |
| `setup.sh` | Quick setup script | `./setup.sh` |

## API Reference

Based on [ReportPortal API v1](https://developers.reportportal.io/api-docs/)

Key endpoints used:
- `GET /api/v1/{project}/launch` - Fetch launches
- `GET /api/v1/{project}/item` - Fetch test items
- `GET /api/v1/{project}/log` - Fetch logs
- `PUT /api/v1/{project}/item/{id}/update` - Update defect types

## Troubleshooting

### Connection Failed
- Verify `RP_BASE_URL` is correct (no trailing slash)
- Check your API token is valid (Profile → API Keys)
- Ensure you have network access to ReportPortal
- Test connection: `curl -H "Authorization: Bearer YOUR_TOKEN" YOUR_RP_URL/api/v1/user`

### No Failed Tests Found
- Verify the launch exists and has failed tests
- Check your project name is correct (case-sensitive)
- Ensure you have read permissions in ReportPortal

### Update Failed
- Verify you have write permissions in ReportPortal
- Check the defect type codes match your project configuration
- Ensure defect types (pb001, ab001, si001, ti001) exist in your project

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

