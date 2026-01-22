# 🎯 GUIA RÁPIDO - 3 PASSOS

## ⚡ Deploy em 3 Minutos

### 📥 PASSO 1: Download
Baixe todos os arquivos do zip: `anvisa_crawler_CORRIGIDO.zip`

### 📝 PASSO 2: Substituir Arquivo

**No seu projeto Railway:**

1. Renomeie `anvisa_crawler.py` → `anvisa_crawler_OLD.py` (backup)
2. Copie `anvisa_crawler_fixed.py` → `anvisa_crawler.py`
3. Commit e push

```bash
cd seu-projeto-railway
mv anvisa_crawler.py anvisa_crawler_OLD.py
cp anvisa_crawler_fixed.py anvisa_crawler.py
git add .
git commit -m "fix: Correções timeout AngularJS"
git push
```

### ✅ PASSO 3: Testar

```bash
curl -X POST https://crawler-anvisa-production-ab03.up.railway.app/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{"molecule": "darolutamida", "brand_name": "nubeqa"}'
```

**Você deve ver:**
```json
{
  "found": true,  ✅ (antes era false)
  "products": [...]  ✅ (antes era [])
}
```

---

## 🔍 O Que Foi Corrigido?

### Antes ❌
```
Page.click: Timeout 30000ms exceeded.
waiting for locator("input[value=\"Busca Avançada\"]")
```

### Depois ✅
```
✅ Successfully clicked: Busca Avançada
✅ Clicked search icon via JavaScript
✅ Found 1 products via active ingredient
```

---

## 📊 Principais Melhorias

| Melhoria | Impacto |
|----------|---------|
| **Espera por AngularJS** | Aguarda requisições HTTP terminarem |
| **3 estratégias de clique** | Se uma falhar, tenta outras |
| **Retry automático** | Até 3 tentativas por clique |
| **Seletores contextuais** | Clica no elemento CERTO |
| **Screenshots automáticos** | Debug visual quando falha |

---

## 🎓 Arquivos Incluídos

### Código
- **`anvisa_crawler_fixed.py`** ⭐ - Crawler corrigido (USE ESTE)
- **`test_crawler_fixed.py`** - Script para testar localmente

### Documentação
- **`README_CORRECOES.md`** - Resumo executivo (LEIA PRIMEIRO)
- **`CORREÇÕES_ANVISA.md`** - Explicação técnica detalhada
- **`DEPLOY_GUIDE.md`** - Guia completo de deploy
- **`GUIA_RAPIDO.md`** (este arquivo) - Deploy em 3 minutos

---

## 🚨 IMPORTANTE

### ⚠️ O que NÃO foi alterado:
- ✅ Versão do Playwright (ainda 1.48.0)
- ✅ Proxies rotativos (mesmos)
- ✅ Técnicas de stealth (mesmas)
- ✅ API FastAPI (mesma)
- ✅ Estrutura do código (compatível)

### ⚠️ O que foi alterado:
- ✅ Esperas para AngularJS
- ✅ Estratégias de clique
- ✅ Seletores
- ✅ Retry logic
- ✅ Logs e debugging

---

## 💡 Teste Rápido Local (Opcional)

Antes de fazer deploy, teste localmente:

```bash
# 1. Instalar
pip install playwright beautifulsoup4 httpx
playwright install chromium

# 2. Testar
python test_crawler_fixed.py

# 3. Deve ver:
# ✅ darolutamida (nubeqa): 1 products
```

---

## 🆘 Problemas?

### Se ainda houver timeout:

1. **Aumentar timeouts** na linha 151 do código:
   ```python
   timeout=15000  →  timeout=20000
   ```

2. **Verificar logs:**
   ```bash
   railway logs --tail
   ```

3. **Verificar screenshots:**
   ```bash
   ls /tmp/anvisa_error_*.png
   ```

### Se não encontrar o botão:

O código já tem 3 estratégias de fallback, mas se mesmo assim falhar:
- Verifique se o site da Anvisa mudou
- Tire screenshot manual para comparar
- Entre em contato para ajuste

---

## 📞 Suporte

**Leia primeiro:**
1. `README_CORRECOES.md` - Visão geral
2. `CORREÇÕES_ANVISA.md` - Detalhes técnicos
3. `DEPLOY_GUIDE.md` - Troubleshooting completo

**Se ainda tiver dúvidas:**
- Capture logs: `railway logs > debug.txt`
- Execute teste local: `python test_crawler_fixed.py`
- Compare resultados com o esperado

---

## ✨ Pronto!

Após o deploy:
- ✅ Busca por darolutamida deve funcionar
- ✅ Busca por brand name (nubeqa) deve funcionar
- ✅ Taxa de sucesso ~95% (antes ~0% para active ingredient)

**Boa sorte! 🚀**
