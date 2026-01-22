#!/bin/bash

# ANVISA API V2 - Local Setup Script
# Installs dependencies and Playwright browsers

set -e

echo "=========================================="
echo "ANVISA API V2 - Local Setup"
echo "=========================================="
echo ""

# Check Python version
echo "1️⃣ Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
if (( $(echo "$PYTHON_VERSION >= 3.10" | bc -l) )); then
    echo "✅ Python $PYTHON_VERSION detected"
else
    echo "❌ Python 3.10+ required (found $PYTHON_VERSION)"
    exit 1
fi
echo ""

# Create virtual environment
echo "2️⃣ Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "3️⃣ Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "4️⃣ Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Install Playwright browsers
echo "5️⃣ Installing Playwright browsers..."
playwright install chromium
echo "✅ Playwright browsers installed"
echo ""

# Create .env if it doesn't exist
echo "6️⃣ Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file (edit it to add your GROQ_API_KEY)"
else
    echo "ℹ️  .env file already exists"
fi
echo ""

echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "🚀 To start the API:"
echo "   source venv/bin/activate"
echo "   uvicorn anvisa_main:app --reload --port 8080"
echo ""
echo "🧪 To run tests:"
echo "   ./test.sh http://localhost:8080"
echo ""
echo "📝 Don't forget to:"
echo "   - Edit .env and add your GROQ_API_KEY (optional)"
echo "   - Check README.md for more information"
echo ""
