# CLAUDE.md

Interfaz de chat multi-modelo sobre OpenRouter para el TP3 de IAGen. La consigna está
en `mission.md`; las decisiones de diseño y los contratos, en `SPEC.md`. Leé `SPEC.md`
antes de tocar `core/`.

## Comandos

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # cargar OPENROUTER_API_KEY
.venv/bin/uvicorn app.main:app --reload
.venv/bin/python -m pytest    # tests del core, sin red
```

Los tests de la cátedra son aparte y se corren con `vida.py` al lado:
`python3 tests/test_vida.py`. `pytest.ini` los excluye de la corrida normal.

## Reglas del repo

- **La key sale de `.env`.** Nunca en la UI, nunca en un archivo versionado, nunca en
  un log. `.env` está gitignoreado.
- **`core/` no importa nada de `app/`.** El dominio se testea sin levantar el servidor.
- **Todo lo específico de un proveedor vive en `core/client.py`.** Si aparece un
  `if model.id == ...` fuera de `core/models.py`, es una capacidad que falta declarar
  en el registry.
- **Los logs de `logs/` son parte de la entrega.** No los borres ni los edites a mano:
  son la evidencia de auditoría. Si un log está mal, la corrida se rehace.
- **El bloque estático de `prompts/` no se toca entre intentos del ejercicio 2.**
  Cambiarlo rompe el prefijo y con él el cache hit que hay que demostrar.

## Al trabajar en el ejercicio 2

Lo que se itera entre intentos es el **prompt**, no el código que devolvió el modelo.
Parchear `vida.py` a mano quema la corrida. Si un intento falla: conversación nueva,
prompt reescrito, y el bloque estático igual que estaba.
