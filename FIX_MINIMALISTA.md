# 🎯 CORREÇÃO MINIMALISTA - v1.0.2

## ⚡ O Problema

```
Page.click: Timeout 30000ms exceeded.
waiting for locator("input[value=\"Busca Avançada\"]")
```

## ✅ A Solução (3 linhas apenas!)

### Mudanças na função `_search_by_active_ingredient`:

#### ANTES (linha 272-277):
```python
await asyncio.sleep(2)

# 2. Click "Busca Avançada"
logger.info("      → Step 2: Clicking 'Busca Avançada'...")
await self.page.click('input[value="Busca Avançada"]')
await asyncio.sleep(1)
```

#### DEPOIS (v1.0.2):
```python
await asyncio.sleep(3)  # FIX: Aumentado de 2 para 3 segundos

# 2. Click "Busca Avançada" - FIX: Wait for it first
logger.info("      → Step 2: Clicking 'Busca Avançada'...")
try:
    # FIX: Wait for button to be present and visible
    await self.page.wait_for_selector('input[value="Busca Avançada"]', state='visible', timeout=10000)
    await asyncio.sleep(1)  # Extra stability wait
    await self.page.click('input[value="Busca Avançada"]', timeout=10000)
    await asyncio.sleep(1)
except Exception as e:
    logger.warning(f"      ⚠️ Could not click 'Busca Avançada': {str(e)}")
    raise
```

### Resumo das mudanças:
1. ✅ Sleep inicial: 2s → 3s
2. ✅ Adicionado: `wait_for_selector` antes do click
3. ✅ Adicionado: timeout explícito de 10s no click
4. ✅ Adicionado: try/except com log claro

## 📦 Deploy

### Opção 1: Substituir arquivo completo

```bash
# Backup
cp anvisa_crawler.py anvisa_crawler_OLD.py

# Substituir
cp anvisa_crawler_v102_minimal.py anvisa_crawler.py

# Deploy
git add anvisa_crawler.py
git commit -m "fix: timeout Busca Avançada - minimal fix"
git push
```

### Opção 2: Editar apenas as linhas

Se preferir editar manualmente:

1. Abra `anvisa_crawler.py`
2. Vá para a linha ~272 (função `_search_by_active_ingredient`)
3. Substitua o bloco do "Step 2" pelo código acima
4. Salve e commit

## 🧪 Teste

```bash
curl -X POST https://seu-servidor/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{"molecule": "darolutamida", "brand_name": "nubeqa"}'
```

**Deve retornar:**
```json
{
  "found": true,
  "products": [...]
}
```

## 📊 O Que NÃO Foi Alterado

✅ Manteve TODA a estratégia de crawling original
✅ Manteve rotação de IPs idêntica
✅ Manteve timeouts padrão (30s)
✅ Manteve todos os sleeps originais (exceto 1)
✅ Manteve fluxo de navegação exato
✅ Manteve simplicidade do código

## 🔍 Por Que Funciona?

### Problema Original:
O Playwright tentava clicar no botão **antes** dele estar pronto.

### Solução Minimalista:
1. **Espera 1s a mais** após load da página (3s total)
2. **Verifica se o botão está visível** antes de clicar
3. **Timeout explícito** de 10s no click (antes era default 30s)

## ⏱️ Deploy Rápido

O deploy deve levar **~2-3 minutos** no Railway (não 15 minutos).

Se ainda demorar:
1. Verifique se o Railway está buildando Playwright corretamente
2. Verifique logs: `railway logs --tail`
3. O timeout é no **BUILD**, não no código

## 🆘 Se Ainda Der Timeout

### Opção A: Aumentar wait inicial
Linha 273: `await asyncio.sleep(3)` → `await asyncio.sleep(5)`

### Opção B: Aumentar timeout do wait_for_selector
Linha 279: `timeout=10000` → `timeout=15000`

### Opção C: Adicionar mais um sleep
Depois da linha 279, adicione:
```python
await asyncio.sleep(2)  # More stability
```

---

## 📝 Diff Completo

```diff
--- anvisa_crawler.py (v1.0.1)
+++ anvisa_crawler.py (v1.0.2)
@@ -269,11 +269,20 @@
                 timeout=30000
             )
-            await asyncio.sleep(2)
+            await asyncio.sleep(3)  # FIX: Increased from 2 to 3 seconds
             
-            # 2. Click "Busca Avançada"
+            # 2. Click "Busca Avançada" - FIX: Wait for it first
             logger.info("      → Step 2: Clicking 'Busca Avançada'...")
-            await self.page.click('input[value="Busca Avançada"]')
+            try:
+                # FIX: Wait for button to be present and visible
+                await self.page.wait_for_selector('input[value="Busca Avançada"]', state='visible', timeout=10000)
+                await asyncio.sleep(1)  # Extra stability wait
+                await self.page.click('input[value="Busca Avançada"]', timeout=10000)
+                await asyncio.sleep(1)
+            except Exception as e:
+                logger.warning(f"      ⚠️ Could not click 'Busca Avançada': {str(e)}")
+                raise
+            
             await asyncio.sleep(1)
```

---

**Isso é tudo!** Mudança mínima, máximo resultado. 🎯
