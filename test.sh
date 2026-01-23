#!/bin/bash

# ANVISA API V2 - Test Script
# Tests both V1 and V2 endpoints

set -e

echo "=========================================="
echo "ANVISA API V2 - Test Suite"
echo "=========================================="
echo ""

# Get API URL from argument or use default
API_URL="${1:-http://localhost:8080}"

echo "🎯 Testing API at: $API_URL"
echo ""

# Test 1: Health Check
echo "1️⃣ Testing health endpoint..."
HEALTH=$(curl -s "$API_URL/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi
echo ""

# Test 2: Root endpoint
echo "2️⃣ Testing root endpoint..."
ROOT=$(curl -s "$API_URL/")
if echo "$ROOT" | grep -q "Anvisa API"; then
    echo "✅ Root endpoint passed"
else
    echo "❌ Root endpoint failed"
    exit 1
fi
echo ""

# Test 3: V1 search
echo "3️⃣ Testing V1 search endpoint..."
V1_RESULT=$(curl -s -X POST "$API_URL/anvisa/search" \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamide",
    "brand_name": "nubeqa"
  }')

if echo "$V1_RESULT" | grep -q "found"; then
    echo "✅ V1 search passed"
    
    # Check if presentations are empty (expected in V1)
    if echo "$V1_RESULT" | grep -q '"presentations":\[\]'; then
        echo "   ℹ️  V1 presentations are empty (expected)"
    fi
else
    echo "❌ V1 search failed"
    echo "Response: $V1_RESULT"
    exit 1
fi
echo ""

# Test 4: V2 search
echo "4️⃣ Testing V2 search endpoint..."
V2_RESULT=$(curl -s -X POST "$API_URL/anvisa/search/v2" \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamide",
    "brand_name": "nubeqa"
  }')

if echo "$V2_RESULT" | grep -q "found"; then
    echo "✅ V2 search passed"
    
    # Check if presentations are filled (expected in V2)
    if echo "$V2_RESULT" | grep -q '"presentations":\[{'; then
        echo "   ✨ V2 presentations are filled (expected)"
    else
        echo "   ⚠️  V2 presentations might be empty (unexpected)"
    fi
    
    # Check if links are present (expected in V2)
    if echo "$V2_RESULT" | grep -q '"links":{'; then
        echo "   ✨ V2 links are present (expected)"
    else
        echo "   ⚠️  V2 links might be missing (unexpected)"
    fi
else
    echo "❌ V2 search failed"
    echo "Response: $V2_RESULT"
    exit 1
fi
echo ""

# Test 5: Compare endpoint
echo "5️⃣ Testing compare endpoint..."
COMPARE=$(curl -s "$API_URL/compare/darolutamide?brand_name=nubeqa")
if echo "$COMPARE" | grep -q "query"; then
    echo "✅ Compare endpoint passed"
else
    echo "❌ Compare endpoint failed"
    exit 1
fi
echo ""

# Test 6: V1 test endpoint
echo "6️⃣ Testing V1 quick test..."
TEST_V1=$(curl -s "$API_URL/test")
if echo "$TEST_V1" | grep -q "test"; then
    echo "✅ V1 test endpoint passed"
else
    echo "❌ V1 test endpoint failed"
    exit 1
fi
echo ""

# Test 7: V2 test endpoint
echo "7️⃣ Testing V2 quick test..."
TEST_V2=$(curl -s "$API_URL/test/v2")
if echo "$TEST_V2" | grep -q "test"; then
    echo "✅ V2 test endpoint passed"
else
    echo "❌ V2 test endpoint failed"
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ All tests passed!"
echo "=========================================="
echo ""
echo "📊 Summary:"
echo "   - Health check: ✅"
echo "   - Root endpoint: ✅"
echo "   - V1 search: ✅"
echo "   - V2 search: ✅"
echo "   - Compare: ✅"
echo "   - Test endpoints: ✅"
echo ""
echo "🎉 Your ANVISA API V2 is working correctly!"
