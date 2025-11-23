# 🚀 Quick Start Guide

Get started debugging with ReportPortal in 3 easy steps!

## Step 1: Setup

```bash
cd reportportal_debugger
./setup.sh
```

## Step 2: Configure

Edit the `.env` file with your ReportPortal credentials:

```bash
nano .env  # or use your preferred editor
```

You need:
1. **RP_BASE_URL** - Your ReportPortal URL (e.g., `https://rp.yourcompany.com`)
2. **RP_API_TOKEN** - Your API token from ReportPortal
3. **RP_PROJECT_NAME** - Your project name (e.g., `my_project`)

### How to get your API Token:

1. Login to ReportPortal
2. Click your profile icon (top right)
3. Go to **Profile** → **API Keys**
4. Copy or generate your token

Example `.env`:
```env
RP_BASE_URL=https://reportportal.mycompany.com
RP_API_TOKEN=a1b2c3d4-e5f6-7890-abcd-ef1234567890
RP_PROJECT_NAME=qa_automation
RP_AUTO_UPDATE=false
```

## Step 3: Run the Debugger

```bash
python rp_debugger.py
```

That's it! The tool will:
- ✅ Connect to ReportPortal
- ✅ Fetch the latest test launch
- ✅ Analyze all failed tests
- ✅ Provide RCA (Root Cause Analysis)
- ✅ Give debugging suggestions

---

## Advanced Usage

### Debug a specific launch

```bash
RP_LAUNCH_ID=your-launch-id python rp_debugger.py
```

### Auto-update defect types

```bash
RP_AUTO_UPDATE=true python rp_debugger.py
```

### Run as cron job

Add to your crontab for automatic daily debugging:

```cron
0 9 * * * cd /path/to/reportportal_debugger && python rp_debugger.py
```

---

## What the output tells you

```
📊 ROOT CAUSE ANALYSIS:
   Category: Product Bug          ← Type of issue
   Defect Type: pb001             ← ReportPortal defect code
   Confidence: HIGH               ← How confident the analysis is
   Reason: Matched 3 patterns     ← Why this classification

🎯 Matched Patterns:              ← Specific patterns found
   - assertion.*failed
   - expected.*but.*got

💥 Error Message:                 ← The actual error
   AssertionError: Expected 401 but got 200

📋 Key Log Entries:               ← Important logs
   - API returned wrong status code
   - Security validation failed

💡 DEBUG SUGGESTIONS:             ← What to do next
   🐛 Verify expected vs actual values
   📝 Check if business logic changed
   🔍 Review recent code changes
```

---

## Troubleshooting

### ❌ Connection Failed
- Check your `RP_BASE_URL` (no trailing slash!)
- Verify your API token is valid
- Ensure you can access ReportPortal from your network

### ❌ No Failed Tests Found
- Check if the launch has failed tests
- Verify your project name is correct
- Make sure you have read permissions

### ❌ Import Error
```bash
pip install -r requirements.txt
```

---

## Need Help?

Check the full [README.md](README.md) for detailed documentation.


