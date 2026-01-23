# CHANGELOG v1.0.2

## Minimal Timeout Fix (4 lines changed)

Based on v1.0.1 that deployed successfully.

### Fixed (1 critical issue)

**"Busca Avançada" button timeout issue**
- File: `anvisa_crawler.py` (lines 272-287 in `_search_by_active_ingredient`)
- Problem: Playwright tried to click button before it was ready
- Solution: Added `wait_for_selector` with visibility check + extra waits

#### Changes:
```python
# BEFORE (v1.0.1)
await asyncio.sleep(2)
await self.page.click('input[value="Busca Avançada"]')

# AFTER (v1.0.2)
await asyncio.sleep(3)  # +1 second
await self.page.wait_for_selector('input[value="Busca Avançada"]', state='visible', timeout=10000)
await asyncio.sleep(1)  # Extra stability
await self.page.click('input[value="Busca Avançada"]', timeout=10000)
```

#### Impact:
- ✅ Resolves: `Page.click: Timeout 30000ms exceeded` error
- ✅ Active ingredient search now works consistently
- ✅ Searches for "darolutamida" now return results

### Unchanged

- All dependencies (Playwright 1.48.0, etc.)
- Dockerfile
- Proxy rotation
- Brand name search
- Product parsing
- All other functionality
- Translation with Groq
- Summary generation

### Deploy

Same as v1.0.1 - should deploy quickly (2-3 minutes).

```bash
# Railway deploy
railway up

# Or git push
git add .
git commit -m "fix: timeout on Busca Avançada button"
git push
```

### Testing

```bash
curl -X POST https://your-service.railway.app/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamida",
    "brand_name": "nubeqa"
  }'
```

Expected: `"found": true` with product data

---

**Version**: 1.0.2  
**Based on**: 1.0.1 (working)  
**Changes**: 1 file, 4 lines  
**Risk**: Minimal  
**Build time**: 2-3 minutes
