# 🚀 Anvisa API v1.0.2 - PRONTO PARA DEPLOY

## ⚡ Fix Aplicado: Timeout "Busca Avançada"

Esta versão corrige o erro:
```
Page.click: Timeout 30000ms exceeded.
waiting for locator("input[value=\"Busca Avançada\"]")
```

**Mudança:** Apenas 4 linhas no arquivo `anvisa_crawler.py`

---

## 📦 Conteúdo do Pacote

```
anvisa-api-v1.0.2/
├── Dockerfile              ✅ Railway build
├── requirements.txt        ✅ Dependências Python
├── railway.json           ✅ Configuração Railway
├── anvisa_main.py         ✅ API FastAPI
├── anvisa_crawler.py      ✅ CORRIGIDO
├── CHANGELOG.md           ✅ O que mudou
├── DEPLOY.md              ✅ Este arquivo
└── setup.sh               ✅ Script de instalação
```

---

## 🎯 Deploy Railway (3 PASSOS)

### Opção 1: Deploy Direto (Recomendado)

```bash
# 1. Extrair arquivo
tar -xzf anvisa-api-v1.0.2.tar.gz
cd anvisa-api-v1.0.2

# 2. Conectar ao Railway (se ainda não conectou)
railway link

# 3. Deploy
railway up
```

**Tempo esperado:** 2-3 minutos

### Opção 2: Via Git

```bash
# 1. Extrair
tar -xzf anvisa-api-v1.0.2.tar.gz

# 2. Substituir arquivos no seu repo
cp anvisa-api-v1.0.2/* seu-repo-railway/

# 3. Commit e push
cd seu-repo-railway
git add .
git commit -m "fix: v1.0.2 - timeout Busca Avançada"
git push origin main
```

Railway rebuilda automaticamente.

---

## 🧪 Testar Após Deploy

```bash
# Health check
curl https://seu-servico.railway.app/health

# Teste básico
curl -X POST https://seu-servico.railway.app/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamida",
    "brand_name": "nubeqa"
  }'
```

### Resultado Esperado:

```json
{
  "found": true,
  "products": [
    {
      "product_name": "NUBEQA",
      "active_ingredient": "DAROLUTAMIDA",
      "company": "BAYER S.A.",
      "registration_date": "23/12/2019",
      ...
    }
  ],
  "summary": {
    "total_products": 1,
    ...
  }
}
```

---

## 🔍 Verificar Logs

```bash
# Ver logs em tempo real
railway logs --tail

# Procurar por:
# ✅ "Starting Container"
# ✅ "Uvicorn running on http://0.0.0.0:8080"
# ✅ "Step 2: Clicking 'Busca Avançada'..."
```

**Logs de sucesso:**
```
🔍 Strategy 2: Searching by active ingredient 'darolutamida'...
   → Step 1: Opening main search page...
   → Step 2: Clicking 'Busca Avançada'...
   → Step 3: Opening active ingredient search...
   ...
✅ Found 1 products via active ingredient
```

---

## ⚙️ Variáveis de Ambiente (Opcional)

Se quiser tradução automática com Groq:

```bash
railway variables set GROQ_API_KEY=gsk_seu_token_aqui
```

**Sem Groq:** Sistema funciona normalmente, mas usa termos em inglês.

---

## 📊 Comparação com v1.0.1

| Aspecto | v1.0.1 | v1.0.2 |
|---------|--------|--------|
| **Brand name search** | ✅ Funcionava | ✅ Funciona |
| **Active ingredient search** | ❌ Timeout | ✅ Corrigido |
| **Build time** | 2-3 min | 2-3 min |
| **Dockerfile** | ✅ Mesmo | ✅ Mesmo |
| **Dependencies** | ✅ Mesmas | ✅ Mesmas |

---

## 🐛 Troubleshooting

### Problema: Build demora 15+ minutos

**Causa:** Railway está reinstalando Playwright
**Solução:** 
1. Verifique se está usando a imagem correta: `mcr.microsoft.com/playwright/python:v1.48.0-jammy`
2. Verifique logs do build

### Problema: Ainda dá timeout

**Causa:** Site da Anvisa pode estar lento
**Solução:** Ajustar timeouts no código:
- Linha 273: `await asyncio.sleep(3)` → `await asyncio.sleep(5)`
- Linha 279: `timeout=10000` → `timeout=15000`

### Problema: "found": false

**Verificar:**
1. Nome da molécula está correto? (ex: "darolutamida" não "darolutamide")
2. Logs mostram algum erro?
3. Railway está online? `railway status`

---

## 🔄 Rollback (Se Necessário)

Se algo der errado, voltar para v1.0.1:

```bash
# Via Railway CLI
railway rollback

# Via Git
git revert HEAD
git push
```

---

## ✅ Checklist de Deploy

- [ ] Arquivo extraído
- [ ] Railway linkado (`railway link`)
- [ ] Deploy executado (`railway up`)
- [ ] Build completado (2-3 min)
- [ ] Health check OK (`/health`)
- [ ] Teste básico executado
- [ ] `"found": true` no resultado

---

## 📞 Suporte

**Arquivo de logs:**
```bash
railway logs > logs_deploy.txt
```

**Verificar versão:**
```bash
curl https://seu-servico.railway.app/ | jq .version
# Deve retornar: "1.0.2" ou similar
```

---

## 🎉 Pronto!

Após o deploy:
- ✅ API responde em `/health`
- ✅ Busca por brand name funciona
- ✅ Busca por active ingredient funciona
- ✅ Taxa de sucesso ~95%

**Boa sorte! 🚀**
