#!/bin/bash

echo "=========================================="
echo "🏥 ANVISA API - SETUP SCRIPT"
echo "=========================================="
echo ""

# Check Python version
echo "1️⃣ Checking Python version..."
python --version
echo ""

# Install dependencies
echo "2️⃣ Installing Python dependencies..."
pip install -r requirements.txt
echo ""

# Install Playwright
echo "3️⃣ Installing Playwright browsers..."
playwright install chromium
echo ""

# Create .env file
echo "4️⃣ Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   ✅ Created .env file"
    echo "   ⚠️  Please edit .env and add your GROQ_API_KEY"
else
    echo "   ℹ️  .env already exists"
fi
echo ""

echo "=========================================="
echo "✅ Setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your GROQ_API_KEY"
echo "  2. Run: python anvisa_main.py"
echo "  3. Test: ./test.sh"
echo ""
