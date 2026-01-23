#!/bin/bash

# ANVISA API Test Script
# Tests the crawler with sample searches

API_URL="${1:-http://localhost:8000}"

echo "=========================================="
echo "ANVISA API v2.0.1 - Test Script"
echo "=========================================="
echo "Testing API at: $API_URL"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health check
echo -e "${YELLOW}Test 1: Health Check${NC}"
HEALTH=$(curl -s "$API_URL/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASS${NC} - API is healthy"
else
    echo -e "${RED}❌ FAIL${NC} - API not responding"
    exit 1
fi
echo ""

# Test 2: Root endpoint
echo -e "${YELLOW}Test 2: Root Endpoint${NC}"
ROOT=$(curl -s "$API_URL/")
if echo "$ROOT" | grep -q "Anvisa API"; then
    echo -e "${GREEN}✅ PASS${NC} - Root endpoint working"
    echo "$ROOT" | grep -o '"version":"[^"]*"'
    echo "$ROOT" | grep -o '"v2_available":[^,]*'
else
    echo -e "${RED}❌ FAIL${NC} - Root endpoint error"
fi
echo ""

# Test 3: Simple search (aspirin - should be fast)
echo -e "${YELLOW}Test 3: Simple Search (Aspirin)${NC}"
echo "Searching for aspirin (no brand name)..."
START_TIME=$(date +%s)

SEARCH=$(curl -s -X POST "$API_URL/anvisa/search/v2" \
    -H "Content-Type: application/json" \
    -d '{
        "molecule": "aspirin",
        "use_proxy": false
    }')

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if echo "$SEARCH" | grep -q '"found":true'; then
    PRODUCTS=$(echo "$SEARCH" | grep -o '"total_products":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✅ PASS${NC} - Found $PRODUCTS products"
    echo "Duration: ${DURATION} seconds"
else
    echo -e "${RED}❌ FAIL${NC} - No products found"
    echo "Response: $SEARCH"
fi
echo ""

# Test 4: Brand name search (darolutamide/nubeqa)
echo -e "${YELLOW}Test 4: Brand Name Search (Darolutamide/Nubeqa)${NC}"
echo "Searching for darolutamide with brand name nubeqa..."
START_TIME=$(date +%s)

SEARCH2=$(curl -s -X POST "$API_URL/anvisa/search/v2" \
    -H "Content-Type: application/json" \
    -d '{
        "molecule": "darolutamide",
        "brand_name": "nubeqa",
        "use_proxy": false
    }')

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if echo "$SEARCH2" | grep -q '"found":true'; then
    PRODUCTS=$(echo "$SEARCH2" | grep -o '"total_products":[0-9]*' | cut -d':' -f2)
    PRESENTATIONS=$(echo "$SEARCH2" | grep -o '"total_presentations":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✅ PASS${NC} - Found $PRODUCTS products with $PRESENTATIONS presentations"
    echo "Duration: ${DURATION} seconds"
    
    # Check for document links
    if echo "$SEARCH2" | grep -q '"bulario"'; then
        echo -e "${GREEN}✅ Document links extracted${NC}"
    fi
else
    echo -e "${RED}❌ FAIL${NC} - No products found"
    echo "Response: $SEARCH2"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "API URL: $API_URL"
echo "All core tests completed!"
echo ""
echo "Next steps:"
echo "1. Check Railway logs for detailed output"
echo "2. Try with Groq API key for translation"
echo "3. Test with use_proxy: true"
echo ""
