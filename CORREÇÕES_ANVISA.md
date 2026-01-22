# ANVISA Crawler - Correções Aplicadas

## 🔧 Problemas Identificados

### 1. **Timeout ao clicar em "Busca Avançada"**
**Erro nos logs:**
```
Page.click: Timeout 30000ms exceeded.
waiting for locator("input[value=\"Busca Avançada\"]")
```

**Causa:**
- O código tentava clicar imediatamente sem esperar o elemento estar visível
- AngularJS precisa de tempo para carregar e renderizar os elementos
- Não havia verificação de visibilidade do elemento

### 2. **Clique no ícone da lupa sem seletor específico**
- O seletor `i.glyphicon-search` era muito genérico
- Poderia pegar qualquer ícone de lupa na página
- Não garantia que estava clicando no ícone correto ao lado de "Princípio Ativo"

### 3. **Falta de espera adequada para AngularJS**
- AngularJS é uma aplicação single-page assíncrona
- Precisa esperar as requisições HTTP terminarem
- Precisa esperar o digest cycle do Angular completar

## ✅ Correções Implementadas

### 1. **Função `_wait_for_angular()`**
```python
async def _wait_for_angular(self):
    """Wait for AngularJS to finish loading"""
    try:
        await self.page.wait_for_function(
            """
            () => {
                return typeof angular !== 'undefined' && 
                       angular.element(document).injector() &&
                       angular.element(document).injector().get('$http').pendingRequests.length === 0;
            }
            """,
            timeout=10000
        )
    except:
        await asyncio.sleep(2)
```

**O que faz:**
- Espera até que todas as requisições HTTP do Angular terminem
- Verifica se o Angular está inicializado
- Fallback para wait simples se der erro

### 2. **Função `_click_with_retry()`**
```python
async def _click_with_retry(self, selector: str, description: str, max_retries: int = 3):
    """Click element with retry mechanism"""
    for attempt in range(max_retries):
        try:
            # Wait for element to be visible
            await self.page.wait_for_selector(selector, state='visible', timeout=15000)
            
            # Extra wait for any animations
            await asyncio.sleep(0.5)
            
            # Try to click
            await self.page.click(selector, timeout=10000)
            logger.info(f"      ✅ Successfully clicked: {description}")
            return True
            
        except Exception as e:
            logger.warning(f"      ⚠️ Attempt {attempt + 1}/{max_retries} failed...")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            else:
                raise
```

**O que faz:**
- Espera explicitamente o elemento estar **visível** antes de clicar
- Faz retry automático até 3 vezes
- Adiciona wait extra para animações
- Logs detalhados de cada tentativa

### 3. **Múltiplas estratégias para clicar "Busca Avançada"**
```python
# Strategy A: By value attribute
await self._click_with_retry(
    'input[value="Busca Avançada"]',
    "Busca Avançada (by value)",
    max_retries=2
)

# Strategy B: By ng-click attribute  
await self._click_with_retry(
    'input[ng-click="toggleBuscaAvancada()"]',
    "Busca Avançada (by ng-click)",
    max_retries=2
)

# Strategy C: By text content
await self._click_with_retry(
    'button:has-text("Busca Avançada"), input:has-text("Busca Avançada")',
    "Busca Avançada (by text)",
    max_retries=2
)
```

**O que faz:**
- Tenta 3 diferentes maneiras de encontrar o botão
- Se uma falhar, tenta a próxima
- Aumenta muito a robustez do crawler

### 4. **Clique preciso no ícone da lupa**
```python
# JavaScript injection para clicar no ícone certo
await self.page.evaluate("""
    () => {
        const labels = Array.from(document.querySelectorAll('label'));
        const principioLabel = labels.find(l => l.textContent.includes('Princípio Ativo'));
        if (principioLabel) {
            const icon = principioLabel.closest('.form-group, div').querySelector('i.glyphicon-search');
            if (icon) {
                icon.closest('button, a, i').click();
                return true;
            }
        }
        return false;
    }
""")
```

**O que faz:**
- Primeiro encontra o label "Princípio Ativo"
- Depois procura o ícone de lupa dentro daquele grupo
- Garante que está clicando no ícone correto
- Fallback para clique Playwright se JavaScript falhar

### 5. **Waits adicionais em pontos críticos**
```python
await self.page.goto(url, wait_until='networkidle', timeout=30000)
await self._wait_for_angular()
await asyncio.sleep(2)  # Extra stability
```

**O que faz:**
- Espera a rede ficar idle (todas as requisições terminarem)
- Espera o Angular terminar de processar
- Wait extra de 2 segundos para garantir estabilidade

### 6. **Screenshots para debugging**
```python
try:
    screenshot_path = f"/tmp/anvisa_error_{molecule}.png"
    await self.page.screenshot(path=screenshot_path)
    logger.info(f"      📸 Screenshot saved: {screenshot_path}")
except:
    pass
```

**O que faz:**
- Salva screenshot quando der erro
- Ajuda no debugging visual
- Não quebra se falhar

## 📋 Resumo das Melhorias

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Espera por elementos** | Clique direto | `wait_for_selector(state='visible')` |
| **AngularJS** | Não aguardava | `_wait_for_angular()` detecta quando pronto |
| **Retry** | 1 tentativa | Até 3 tentativas com estratégias diferentes |
| **Timeouts** | Padrão (30s) | Customizado por operação (10-15s) |
| **Seletores** | 1 seletor genérico | Múltiplos seletores específicos + fallback |
| **Clique na lupa** | Seletor CSS genérico | JavaScript + seletor contextual |
| **Debugging** | Apenas logs | Logs + screenshots automáticos |
| **Waits extras** | Mínimos | Estratégicos após cada ação |

## 🎯 Resultado Esperado

Com essas correções, o crawler deve:
1. ✅ Conseguir clicar em "Busca Avançada" consistentemente
2. ✅ Clicar no ícone correto da lupa
3. ✅ Preencher o campo de princípio ativo
4. ✅ Completar o fluxo de busca por molécula
5. ✅ Retornar resultados para "darolutamida" / "nubeqa"

## 🧪 Como Testar

### Teste 1: Busca básica
```bash
curl -X POST http://localhost:8080/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamide",
    "brand_name": "nubeqa"
  }'
```

### Teste 2: Apenas molécula
```bash
curl -X POST http://localhost:8080/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "acetylsalicylic acid"
  }'
```

### Teste 3: Com tradução Groq
```bash
curl -X POST http://localhost:8080/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamide",
    "brand_name": "nubeqa",
    "groq_api_key": "your_groq_key_here"
  }'
```

## 📝 Notas Importantes

1. **Versão do Playwright**: Mantida em 1.48.0 conforme solicitado
2. **Proxies**: Mantidos os mesmos proxies rotativos
3. **Stealth**: Todas as técnicas de stealth preservadas
4. **Compatibilidade**: 100% compatível com o código existente

## 🔄 Próximos Passos

1. Substituir `anvisa_crawler.py` por `anvisa_crawler_fixed.py`
2. Testar localmente
3. Deploy no Railway
4. Monitorar logs para confirmar sucesso
