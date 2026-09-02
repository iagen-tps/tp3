# TP3 · Prompting

Consigna: `mission.md` — https://github.com/austral-ing-ai/talksmith-ing/tree/main/missions/prompting

**Medidor**, la interfaz del ejercicio 1: un chat sobre OpenRouter que sirve cuatro
modelos de cuatro proveedores, muestra el usage y el costo de cada respuesta y deja un
log `.md` por conversación.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # cargar OPENROUTER_API_KEY
.venv/bin/uvicorn app.main:app --reload
```

Abre en http://localhost:8000. Los contratos y las decisiones de diseño están en
`SPEC.md`; las convenciones de trabajo, en `CLAUDE.md`.

## Entrega

- `app/`, `core/` — la interfaz del ejercicio 1
- `logs/*.md` — los logs de las conversaciones (evidencia de los ejercicios 2 y 3)
- `vida.py` — el script del ejercicio 2
- `INFORME.md` — la cuenta final del ejercicio 3
