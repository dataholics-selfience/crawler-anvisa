#!/bin/bash

echo "=========================================="
echo "🏥 ANVISA API - TEST SCRIPT"
echo "=========================================="
echo ""

# Check if server is running
SERVER="http://localhost:8000"

echo "1️⃣ Testing health endpoint..."
curl -s "$SERVER/health" | jq .
echo ""

echo "2️⃣ Testing quick test endpoint (aspirin)..."
curl -s "$SERVER/test" | jq .
echo ""

echo "3️⃣ Testing main search (darolutamide)..."
curl -s -X POST "$SERVER/anvisa/search" \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamide",
    "brand_name": "nubeqa",
    "groq_api_key": "'"$GROQ_API_KEY"'",
    "use_proxy": false
  }' | jq .
echo ""

echo "4️⃣ Testing with just molecule (no brand)..."
curl -s -X POST "$SERVER/anvisa/search" \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "paracetamol",
    "use_proxy": false
  }' | jq .
echo ""

echo "=========================================="
echo "✅ Tests completed!"
echo "=========================================="
