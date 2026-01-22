# 🚀 Guia de Deploy - Anvisa Crawler Corrigido

## 📦 Arquivos Modificados

### Arquivo Principal Corrigido
- `anvisa_crawler_fixed.py` → Deve substituir `anvisa_crawler.py`

### Mantidos Sem Alterações
- `anvisa_main.py` (API FastAPI)
- `anvisa_crawler_v2.py` (V2 com documentos completos)
- `requirements.txt`
- `Dockerfile`
- Todos os outros arquivos

## 🔧 Opção 1: Deploy no Railway (Recomendado)

### Passo 1: Backup do código atual
```bash
# No Railway, fazer backup através do Git ou baixar os arquivos
railway logs > backup_logs.txt
```

### Passo 2: Substituir o arquivo
1. Acesse o Railway Dashboard
2. Vá para seu projeto `crawler-anvisa-production`
3. Abra o editor de código ou conecte via GitHub
4. **RENOMEIE** `anvisa_crawler.py` para `anvisa_crawler_OLD.py` (backup)
5. **RENOMEIE** `anvisa_crawler_fixed.py` para `anvisa_crawler.py`
6. Commit e push

### Passo 3: Verificar deployment
```bash
# Aguardar o Railway rebuildar automaticamente
# Verificar logs em tempo real:
railway logs --tail
```

### Passo 4: Testar
```bash
# Teste básico
curl -X POST https://crawler-anvisa-production-ab03.up.railway.app/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamida",
    "brand_name": "nubeqa"
  }'
```

## 🔧 Opção 2: Deploy Manual (Git)

### Se você tem o projeto no Git:

```bash
# 1. Clone ou pull latest
git clone <seu-repo>
cd anvisa-api-v2.0-railway

# 2. Fazer backup
cp anvisa_crawler.py anvisa_crawler_OLD.py

# 3. Substituir com a versão corrigida
cp anvisa_crawler_fixed.py anvisa_crawler.py

# 4. Commit e push
git add anvisa_crawler.py
git commit -m "fix: Melhorar waits para AngularJS e múltiplas estratégias de clique"
git push origin main

# Railway vai rebuildar automaticamente
```

## 🔧 Opção 3: Teste Local Primeiro

### Antes de fazer deploy, testar localmente:

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Instalar Playwright browsers
playwright install chromium

# 3. Configurar variáveis de ambiente
export PORT=8080
export GROQ_API_KEY="your_key_here"  # opcional

# 4. Rodar localmente
python anvisa_main.py

# 5. Em outro terminal, testar
curl -X POST http://localhost:8080/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamida",
    "brand_name": "nubeqa"
  }'
```

## 📝 Checklist de Deploy

- [ ] Backup do `anvisa_crawler.py` original feito
- [ ] `anvisa_crawler_fixed.py` renomeado para `anvisa_crawler.py`
- [ ] Código commitado no Git (se aplicável)
- [ ] Railway rebuild iniciado
- [ ] Logs verificados (sem erros de timeout)
- [ ] Teste básico executado com sucesso
- [ ] API retornando `"found": true` para darolutamida

## 🐛 Troubleshooting

### Se ainda houver timeout:

1. **Verificar logs do Railway:**
```bash
railway logs --tail
```

2. **Procurar por:**
- `✅ Successfully clicked: Busca Avançada` - Deve aparecer
- `❌ Attempt 3/3 failed` - Não deve aparecer
- `📸 Screenshot saved` - Se aparecer, há um problema visual

3. **Se o timeout persistir:**
- Aumentar o timeout na linha 15: `timeout=15000` → `timeout=20000`
- Aumentar waits após cliques: `await asyncio.sleep(2)` → `await asyncio.sleep(3)`

### Se encontrar erro de import:

```python
# Certifique-se que o arquivo se chama exatamente:
anvisa_crawler.py

# E que a importação no anvisa_main.py está:
from anvisa_crawler import anvisa_crawler as crawler_v1
```

### Se o Railway não rebuildar:

1. Force rebuild:
```bash
railway up --force
```

2. Ou pelo Dashboard: Settings → Redeploy

## ✅ Verificação de Sucesso

Você sabe que funcionou quando:

1. **Nos logs do Railway:**
```
✅ Successfully clicked: Busca Avançada
✅ Clicked search icon via JavaScript
```

2. **Na resposta da API:**
```json
{
  "found": true,
  "products": [
    {
      "product_name": "NUBEQA",
      "active_ingredient": "DAROLUTAMIDA",
      ...
    }
  ],
  "summary": {
    "total_products": 1,
    ...
  }
}
```

## 🔄 Rollback (Se necessário)

Se algo der errado, rollback é simples:

```bash
# Restaurar backup
cp anvisa_crawler_OLD.py anvisa_crawler.py

# Commit
git add anvisa_crawler.py
git commit -m "rollback: Restaurar versão anterior"
git push origin main
```

## 📞 Suporte

Se ainda houver problemas:

1. Capturar logs completos:
```bash
railway logs > debug_logs.txt
```

2. Verificar se Playwright está instalado:
```bash
playwright --version
```

3. Testar manualmente no Railway Shell:
```bash
railway shell
python test_crawler_fixed.py
```

## 🎉 Próximos Passos Após Deploy

1. Monitorar primeiras requisições
2. Verificar taxa de sucesso
3. Ajustar timeouts se necessário
4. Considerar implementar cache de resultados
5. Adicionar mais logs de debug se necessário
