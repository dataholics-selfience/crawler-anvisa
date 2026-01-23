# 🚀 ANVISA API V2 - Quick Start Guide

## Deploy in 3 Minutes

### 1️⃣ Deploy to Railway

```bash
# Option A: One-click deploy
# Go to: https://railway.app
# Click: New Project → Deploy from GitHub repo → Select this repo
# Railway will auto-detect Dockerfile and deploy

# Option B: Railway CLI
railway login
railway init
railway up
```

**That's it!** Railway will:
- Build the Docker image
- Deploy the API
- Assign a public URL
- Start health monitoring

---

### 2️⃣ Test Your Deployment

```bash
# Replace YOUR_RAILWAY_URL with your actual URL
export API_URL="https://your-app.railway.app"

# Health check
curl $API_URL/health

# Test V2 (enhanced)
curl -X POST $API_URL/anvisa/search/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamide",
    "brand_name": "nubeqa"
  }'
```

---

### 3️⃣ View Results

You should see:
```json
{
  "found": true,
  "products": [{
    "product_name": "NUBEQA",
    "presentations": [{
      "description": "300 MG COM REV...",
      "registration": "170560120001",
      ...
    }],
    "links": {
      "bulario": "https://...",
      "parecer_publico": "https://...",
      "rotulagem": [...]
    }
  }],
  "summary": {
    "total_products": 1,
    "total_presentations": 1,
    "documents_available": {
      "bulario": 1,
      "parecer_publico": 1,
      "rotulagem": 1
    }
  }
}
```

---

## 🎯 Choose Your Endpoint

### Use V2 (Recommended) ✨
```bash
POST /anvisa/search/v2
```
**Why**: Full data extraction (presentations + links)

### Use V1 (Legacy)
```bash
POST /anvisa/search
```
**Why**: Backward compatibility, faster (but incomplete data)

---

## 📊 Compare Results

```bash
# See V1 vs V2 differences
curl $API_URL/compare/darolutamide?brand_name=nubeqa
```

---

## 🔧 Optional: Add Groq Translation

1. Get API key: https://console.groq.com
2. In Railway dashboard:
   - Go to your project
   - Click "Variables"
   - Add: `GROQ_API_KEY=gsk_xxx`
3. Redeploy

Now your API will translate molecules to Portuguese automatically!

---

## 📱 Use the API

### Python Example
```python
import httpx

async def search_anvisa(molecule: str, brand: str = None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-app.railway.app/anvisa/search/v2",
            json={
                "molecule": molecule,
                "brand_name": brand
            },
            timeout=120.0
        )
        return response.json()

# Usage
result = await search_anvisa("darolutamide", "nubeqa")
print(f"Found {len(result['products'])} products")
print(f"Total presentations: {result['summary']['total_presentations']}")
```

### JavaScript Example
```javascript
async function searchAnvisa(molecule, brand) {
  const response = await fetch(
    'https://your-app.railway.app/anvisa/search/v2',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        molecule: molecule, 
        brand_name: brand 
      })
    }
  );
  return await response.json();
}

// Usage
const result = await searchAnvisa('darolutamide', 'nubeqa');
console.log(`Found ${result.products.length} products`);
console.log(`Documents available:`, result.summary.documents_available);
```

---

## 🐛 Troubleshooting

### Problem: Deployment failed
**Solution**: Check Railway logs for errors
```bash
railway logs
```

### Problem: API returns 500 error
**Solution**: Check if Playwright browsers are installed (they should be in Docker image)

### Problem: Empty results
**Solution**: 
- Verify the molecule/brand name is correct
- Try both endpoints (V1 and V2)
- Check Railway logs for detailed errors

---

## 📈 Next Steps

1. ✅ **Deployed** - Your API is running
2. 📊 **Test** - Try different molecules
3. 🔧 **Configure** - Add Groq key for translation
4. 📚 **Integrate** - Use in your application
5. 🎯 **Monitor** - Check Railway metrics

---

## 🆘 Need Help?

- **Logs**: `railway logs`
- **Status**: Railway dashboard → Deployments
- **Health**: `curl YOUR_URL/health`
- **Documentation**: See README.md

---

**That's it! You're ready to go.** 🎉

Total time: ~3 minutes
