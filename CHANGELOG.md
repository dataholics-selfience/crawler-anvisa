# CHANGELOG v1.0.1

## Minimal Patch Release (2 changes, ~20 lines)

Based on v1.0 that deployed successfully.

### Fixed (2 critical bugs)

1. **GROQ_API_KEY now reads from environment variable**
   - File: `anvisa_main.py` (line 107)
   - Change: Added fallback to `os.getenv("GROQ_API_KEY")`
   - Impact: Translation now works when key is set in Railway variables

2. **Parser no longer captures table headers**
   - File: `anvisa_crawler.py` (line 390-397)
   - Change: Added filter to ignore values that look like labels
   - Impact: Products now show real data instead of "Complemento da Marca", etc.

### Unchanged

- All dependencies (Playwright 1.48.0, etc.)
- Dockerfile
- Core crawler logic
- All other functionality

### Deploy

Same as v1.0 - should deploy quickly (< 5 minutes).

```bash
# Railway deploy
railway up

# Set Groq key
railway variables set GROQ_API_KEY=gsk_xxx
```

---

**Version**: 1.0.1  
**Based on**: 1.0 (working)  
**Changes**: 2 files, ~20 lines  
**Risk**: Minimal
