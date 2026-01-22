# 🏥 ANVISA API v1.0

Standalone API for Brazilian pharmaceutical regulatory intelligence.

**Uses EXACT same technique as Pharmyrus INPI crawler**:
- ✅ Playwright 1.48.0
- ✅ Stealth mode (disable automation detection)
- ✅ Proxy rotation (Bright Data + ScrapingBee)
- ✅ Groq AI for Portuguese translation
- ✅ Retry mechanisms

---

## 🚀 Quick Start

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. Set Groq API key (optional but recommended)
export GROQ_API_KEY="gsk_your_key_here"

# 4. Run server
python anvisa_main.py
```

Server will start at: http://localhost:8000

---

## 📡 API Endpoints

### 1. Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "anvisa-api"
}
```

---

### 2. Search Anvisa

```bash
POST /anvisa/search
```

Request body:
```json
{
  "molecule": "darolutamide",
  "brand_name": "nubeqa",
  "groq_api_key": "gsk_xxx",
  "use_proxy": false
}
```

Fields:
- `molecule` (required): Molecule name in English
- `brand_name` (optional): Brand/commercial name
- `groq_api_key` (optional): For Portuguese translation
- `use_proxy` (optional): Enable proxy rotation (default: false)

Response:
```json
{
  "found": true,
  "products": [
    {
      "product_name": "NUBEQA",
      "registration_number": "170560120",
      "registration_date": "23/12/2019",
      "expiry_date": "12/2029",
      "company": "BAYER S.A.",
      "cnpj": "18.459.628/0001-15",
      "active_ingredient": "DAROLUTAMIDA",
      "regulatory_category": "Novo",
      "reference_drug": "MEDICAMENTO DE REFERÊNCIA DESDE 28/07/2023",
      "therapeutic_class": "ANTIANDRÓGENOS",
      "atc_code": "G03H",
      "priority_type": "Doença Rara",
      "presentations": []
    }
  ],
  "summary": {
    "total_products": 1,
    "first_approval": "2019-12-23",
    "reference_drugs": 1,
    "generic_drugs": 0,
    "companies": ["BAYER S.A."]
  },
  "search_terms": {
    "molecule": "darolutamide",
    "molecule_pt": "darolutamida",
    "brand": "nubeqa",
    "brand_pt": "nubeqa"
  }
}
```

---

### 3. Quick Test

```bash
GET /test
```

Tests with aspirin (known drug). Returns first 2 results.

---

## 🧪 Testing

### Using test script:

```bash
# Set your Groq API key
export GROQ_API_KEY="gsk_xxx"

# Run tests
./test.sh
```

### Manual tests:

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Test 2: Quick test (aspirin)
curl http://localhost:8000/test

# Test 3: Search darolutamide
curl -X POST http://localhost:8000/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamide",
    "brand_name": "nubeqa",
    "groq_api_key": "gsk_xxx"
  }'

# Test 4: Search paracetamol (no brand)
curl -X POST http://localhost:8000/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "paracetamol"
  }'
```

---

## 🐳 Docker Deployment

### Build image:

```bash
docker build -t anvisa-api .
```

### Run container:

```bash
docker run -p 8000:8000 \
  -e GROQ_API_KEY="gsk_xxx" \
  anvisa-api
```

---

## 🚂 Railway Deployment

### Deploy to Railway:

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Set environment variable
railway variables set GROQ_API_KEY=gsk_xxx

# 5. Deploy
railway up
```

---

## 🔧 Technical Details

### Search Strategy

The crawler uses a **2-phase approach**:

1. **Phase 1: Brand Name Search** (if provided)
   - URL: `https://consultas.anvisa.gov.br/#/medicamentos/q/?nomeProduto=xxx`
   - More specific, faster results
   - Example: "nubeqa"

2. **Phase 2: Active Ingredient Search** (fallback)
   - Uses "Busca Avançada" (Advanced Search)
   - Steps:
     1. Click "Busca Avançada"
     2. Click magnifying glass (🔍) next to "Princípio Ativo"
     3. Type molecule name
     4. Click "Pesquisar"
     5. Select first result
     6. Click "Consultar"
   - More comprehensive but slower
   - Example: "darolutamida"

### Stealth Techniques

Same as INPI crawler:

```python
browser = await p.chromium.launch(
    headless=True,
    args=[
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-setuid-sandbox'
    ]
)

context = await browser.new_context(
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    viewport={'width': 1920, 'height': 1080},
    locale='pt-BR'
)
```

### Proxy Rotation

Same proxy pool as Google Patents crawler:

```python
PROXIES = [
    "http://brd-customer-hl_8ea11d75-zone-residential_proxy1:w7qs41l7ijfc@brd.superproxy.io:33335",
    "http://brd-customer-hl_8ea11d75-zone-datacenter_proxy1:93u1xg5fef4p@brd.superproxy.io:33335",
    "http://5SHQXNTHNKDHUHFD:wifi;us;;;@proxy.scrapingbee.com:8886",
    "http://XNK2KLGACMN0FKRY:wifi;us;;;@proxy.scrapingbee.com:8886",
]
```

---

## 📊 Data Fields Extracted

From each product:

- `product_name` - Commercial name
- `complement` - Brand complement
- `process_number` - Regulatory process number
- `registration_number` - Anvisa registration number
- `registration_date` - Approval date
- `expiry_date` - Registration expiry
- `company` - Holder company
- `cnpj` - Company tax ID
- `afe` - AFE code
- `active_ingredient` - Active ingredient (princípio ativo)
- `regulatory_category` - Category (Novo, Genérico, etc.)
- `reference_drug` - Reference drug status
- `therapeutic_class` - Therapeutic class
- `atc_code` - ATC classification
- `priority_type` - Priority type (Doença Rara, etc.)
- `presentations` - List of presentations/dosages

---

## 🔄 Integration with Pharmyrus

When ready to integrate:

```python
# In main.py (after INPI enrichment)

from anvisa_crawler import anvisa_crawler

# LAYER 5: Regulatory Intelligence
anvisa_results = await anvisa_crawler.search_anvisa(
    molecule=molecule,
    brand=brand,
    groq_api_key=GROQ_API_KEY,
    use_proxy=False
)

# Add to response
response_data['regulatory_intelligence'] = {
    'anvisa': anvisa_results
}
```

---

## ⚡ Performance

- **Brand name search**: ~5-10 seconds
- **Active ingredient search**: ~10-15 seconds
- **Per product details**: ~2 seconds each
- **Total (5 products)**: ~20-30 seconds

---

## 🐛 Troubleshooting

### Error: Playwright not installed

```bash
playwright install chromium
```

### Error: Port already in use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
PORT=8001 python anvisa_main.py
```

### Error: Timeout / Page not loading

- Check internet connection
- Try with `use_proxy: true`
- Increase timeout in crawler (line with `timeout=30000`)

---

## 📝 Logs

Logs show detailed execution:

```
==========================================
🏥 ANVISA SEARCH: darolutamide (nubeqa)
==========================================
   ✅ Translations:
      Molecule: darolutamide → darolutamida
      Brand: nubeqa → nubeqa
   🔍 Strategy 1: Searching by brand name 'nubeqa'...
      → URL: https://consultas.anvisa.gov.br/#/medicamentos/q/?nomeProduto=nubeqa
      → Pagination set to 50
      → Found 1 result rows
      → [1/1] Clicking: NUBEQA...
         ✅ Parsed: NUBEQA
      ✅ Found 1 products via brand name
✅ Search completed: 1 products found
```

---

## 🎯 Next Steps

1. ✅ Test with multiple drugs
2. ✅ Validate data accuracy
3. ✅ Test with proxies
4. ⏳ Integrate into Pharmyrus main API
5. ⏳ Add to patent cliff analysis
6. ⏳ Add to timeline visualization

---

## 📞 Support

Issues? Contact the team or check logs for detailed error messages.

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-22  
**Status**: ✅ Ready for testing
