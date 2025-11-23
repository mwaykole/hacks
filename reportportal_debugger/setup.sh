#!/bin/bash

echo "=================================="
echo "ReportPortal Debugger Setup"
echo "=================================="
echo ""

if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp config_template.env .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  Please edit .env and add your ReportPortal credentials:"
    echo "   - RP_BASE_URL"
    echo "   - RP_API_TOKEN"
    echo "   - RP_PROJECT_NAME"
    echo ""
else
    echo "✅ .env file already exists"
fi

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
    echo ""
    echo "=================================="
    echo "Setup Complete!"
    echo "=================================="
    echo ""
    echo "Next steps:"
    echo "1. Edit .env with your ReportPortal credentials"
    echo "2. Run: python rp_debugger.py"
    echo ""
else
    echo "❌ Failed to install dependencies"
    exit 1
fi


