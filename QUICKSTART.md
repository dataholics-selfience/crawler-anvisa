# 🚀 QUICK START - Anvisa API

## 5 minutos para começar

### 1. Setup (1 comando)

```bash
./setup.sh
```

Isso vai:
- ✅ Instalar dependências Python
- ✅ Instalar Playwright Chromium
- ✅ Criar arquivo .env

---

### 2. Configurar Groq API Key

```bash
# Editar .env
nano .env

# Ou export direto
export GROQ_API_KEY="gsk_your_key_here"
```

**Opcional mas recomendado** - melhora tradução PT

---

### 3. Iniciar servidor

```bash
python anvisa_main.py
```

Vai abrir em: http://localhost:8000

---

### 4. Testar

```bash
# Em outro terminal
./test.sh
```

Ou manualmente:

```bash
# Health check
curl http://localhost:8000/health

# Quick test (aspirin)
curl http://localhost:8000/test

# Search darolutamide
curl -X POST http://localhost:8000/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{"molecule": "darolutamide", "brand_name": "nubeqa"}'
```

---

## ✅ Pronto!

Agora você pode:

1. ✅ Testar com diferentes moléculas
2. ✅ Ver logs detalhados no terminal
3. ✅ Integrar no Pharmyrus quando estiver 100%

---

## 📝 Exemplos de Teste

### Teste 1: Darolutamide (Nubeqa)

```bash
curl -X POST http://localhost:8000/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "darolutamide",
    "brand_name": "nubeqa"
  }'
```

### Teste 2: Paracetamol

```bash
curl -X POST http://localhost:8000/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "paracetamol"
  }'
```

### Teste 3: Aspirin

```bash
curl -X POST http://localhost:8000/anvisa/search \
  -H "Content-Type: application/json" \
  -d '{
    "molecule": "acetylsalicylic acid",
    "brand_name": "aspirin"
  }'
```

---

## 🐛 Problemas?

### Erro: playwright not found

```bash
playwright install chromium
```

### Erro: Port 8000 in use

```bash
# Matar processo
lsof -ti:8000 | xargs kill -9

# Ou usar outra porta
PORT=8001 python anvisa_main.py
```

---

**Dúvidas?** Veja README.md completo
