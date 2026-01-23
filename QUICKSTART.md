# Quick Start Guide

Get the ANVISA Crawler API running in 5 minutes!

## 🚀 Option 1: Railway (Recommended)

**Fastest deployment - No local setup needed**

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - ANVISA API v2.0.1"
   git remote add origin YOUR_GITHUB_REPO
   git push -u origin main
   ```

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub"
   - Select your repository
   - Add environment variable: `GROQ_API_KEY=gsk_xxx` (optional)
   - Railway auto-detects Dockerfile and deploys!

3. **Test it**
   ```bash
   curl https://YOUR-APP.railway.app/health
   ```

---

## 💻 Option 2: Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. (Optional) Configure Groq API
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 4. Run the server
uvicorn anvisa_main:app --reload --port 8000
```

### Test it

```bash
# Health check
curl http://localhost:8000/health

# Test search (without translation)
curl -X POST http://localhost:8000/anvisa/search/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "aspirin",
    "brand_name": "aspirina",
    "use_proxy": false
  }'
```

---

## 🐳 Option 3: Docker

### Build and Run

```bash
# 1. Build the image
docker build -t anvisa-api .

# 2. Run the container
docker run -p 8080:8080 \
  -e GROQ_API_KEY=gsk_your_key_here \
  anvisa-api

# 3. Test it
curl http://localhost:8080/health
```

---

## 📝 Your First Search

### Example 1: Brand Name Search (Fast)

```bash
curl -X POST http://localhost:8000/anvisa/search/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamide",
    "brand_name": "nubeqa",
    "use_proxy": false
  }'
```

**What happens:**
1. Translates "darolutamide" → "darolutamida" (if Groq API configured)
2. Searches by brand name "nubeqa" first (fast)
3. Returns complete product info + presentations + document links
4. Takes ~10 seconds

### Example 2: Molecule Search (Comprehensive)

```bash
curl -X POST http://localhost:8000/anvisa/search/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "aspirin",
    "use_proxy": false
  }'
```

**What happens:**
1. No brand name provided, goes straight to advanced search
2. Uses "Busca Avançada" flow with active ingredient
3. Returns ALL products containing aspirin
4. Takes ~15-20 seconds (more comprehensive)

### Example 3: With Translation

```bash
curl -X POST http://localhost:8000/anvisa/search/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "ibuprofen",
    "brand_name": "advil",
    "groq_api_key": "gsk_your_key_here",
    "use_proxy": false
  }'
```

**What happens:**
1. Translates: "ibuprofen" → "ibuprofeno", "advil" → "advil"
2. Searches with Portuguese terms
3. More accurate results!

---

## 🔍 Understanding the Response

```json
{
  "found": true,
  "products": [
    {
      "product_name": "NUBEQA",
      "active_ingredient": "DAROLUTAMIDA",
      "company": "BAYER S.A.",
      "registration_date": "23/12/2019",
      "presentations": [
        {
          "description": "300 MG COM REV CT FR PLAS PEAD OPC X 120",
          "pharmaceutical_form": "Comprimido Revestido",
          "validity": "36 meses"
        }
      ],
      "links": {
        "bulario": "http://...",
        "parecer_publico": "http://...",
        "rotulagem": [...]
      }
    }
  ],
  "summary": {
    "total_products": 1,
    "total_presentations": 1,
    "reference_drugs": 1,
    "companies": ["BAYER S.A."]
  }
}
```

**Key fields:**
- `products`: Array of found products
- `summary`: Statistics and aggregated info
- `search_terms`: Shows what terms were actually used

---

## 🛠️ Troubleshooting

### "No module named 'playwright'"
```bash
pip install playwright
playwright install chromium
```

### "Connection refused" or timeout errors
- Check if Railway deployment is still starting (takes ~2 minutes first time)
- Local: Make sure port 8000/8080 is not in use
- Try with `use_proxy: false` first

### "No products found"
- Check if molecule/brand name is spelled correctly
- Try searching with Portuguese terms directly
- Look at Railway logs for detailed error messages

### Translation not working
- Verify `GROQ_API_KEY` is set correctly
- API key must start with `gsk_`
- Check [console.groq.com](https://console.groq.com) for usage limits

---

## 📚 Next Steps

1. **Read the full README.md** for complete documentation
2. **Check CHANGELOG.md** to understand v2.0.1 fix
3. **Review Railway logs** to see crawler in action
4. **Test with your molecules** and see the results!

---

## 🎯 Key Features to Try

1. **Compare V1 vs V2**
   - V1: `/anvisa/search`
   - V2: `/anvisa/search/v2` (recommended)

2. **Enable proxy rotation**
   - Set `"use_proxy": true` in request
   - Helps avoid rate limiting

3. **Batch searches**
   - Search multiple molecules
   - Compare results
   - Build datasets

---

## 💡 Tips

- **Use V2 endpoint** (`/anvisa/search/v2`) for best results
- **Provide both molecule AND brand** when possible
- **Monitor Railway logs** to understand what's happening
- **Start with simple searches** (like aspirin) to verify setup
- **Use Portuguese terms** directly if no Groq key

---

**Happy crawling! 🏥📊**
