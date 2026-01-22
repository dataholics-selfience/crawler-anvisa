#!/bin/bash

# Script de teste standalone para Anvisa API
# Executa testes completos: setup + servidor + testes

echo "=========================================="
echo "🏥 ANVISA API - STANDALONE TEST"
echo "=========================================="
echo ""

# Check if already in anvisa-api directory
if [ ! -f "anvisa_main.py" ]; then
    echo "❌ Error: Must be run from anvisa-api directory"
    echo "   Run: cd anvisa-api && ./test-standalone.sh"
    exit 1
fi

echo "📦 Step 1: Installing dependencies..."
pip install -q -r requirements.txt
echo "   ✅ Dependencies installed"
echo ""

echo "🎭 Step 2: Installing Playwright..."
playwright install chromium > /dev/null 2>&1
echo "   ✅ Playwright installed"
echo ""

echo "🚀 Step 3: Starting server in background..."
python anvisa_main.py > server.log 2>&1 &
SERVER_PID=$!
echo "   ✅ Server started (PID: $SERVER_PID)"
echo ""

echo "⏳ Step 4: Waiting for server to be ready..."
sleep 5
echo "   ✅ Server ready"
echo ""

echo "=========================================="
echo "🧪 RUNNING TESTS"
echo "=========================================="
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "--------------------"
curl -s http://localhost:8000/health | jq .
echo ""

# Test 2: Quick test (aspirin)
echo "Test 2: Quick Test (Aspirin)"
echo "--------------------"
curl -s http://localhost:8000/test | jq '.test, .found, .products_count'
echo ""

# Test 3: Search darolutamide
echo "Test 3: Search Darolutamide/Nubeqa"
echo "--------------------"
curl -s -X POST http://localhost:8000/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamide",
    "brand_name": "nubeqa",
    "use_proxy": false
  }' | jq '.found, .summary.total_products, .products[0].product_name'
echo ""

echo "=========================================="
echo "🛑 Stopping server..."
kill $SERVER_PID
echo "   ✅ Server stopped"
echo ""

echo "=========================================="
echo "✅ ALL TESTS COMPLETED!"
echo "=========================================="
echo ""
echo "Check server.log for detailed logs"
echo ""
