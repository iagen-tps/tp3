# SPEC · Medidor (ejercicio 1 del TP3)

Interfaz de chat sobre OpenRouter que sirve cuatro modelos de cuatro proveedores,
muestra el `usage` de cada respuesta y deja un log `.md` por conversación. El log es
la evidencia de auditoría de los ejercicios 2 y 3.

## Modelos

| Slot | Modelo | Proveedor | Ejercita | Caching |
|---|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | OpenAI | `reasoning_effort` | automático por prefijo |
| 2 | `anthropic/claude-haiku-4.5` | Anthropic | caching explícito | `cache_control`, mínimo 2048 tok |
| 3 | `google/gemini-3.7-flash` | Google | salidas estructuradas | automático por prefijo |
| 4 | `deepseek/deepseek-v4-flash-0731` | DeepSeek | el escalón barato | automático por prefijo |

Verificados contra `GET /api/v1/models` el 2026-09-02. Haiku 4.5 **no** soporta
`reasoning_effort` (solo `reasoning.max_tokens`); DeepSeek v4 Flash soporta ambos.

## Requisitos y dónde se cumplen

| Requisito de la consigna | Dónde |
|---|---|
| Mostrar el usage después de cada respuesta | barra de lectura bajo cada respuesta + tablero acumulado |
| Switchear de modelo; el cambio inicia conversación nueva | `selectModel()` confirma y llama a `POST /api/conversations` |
| Log `.md` por conversación con rol, mensaje y usage | `core/mdlog.py`, reescrito tras cada turno |
| Cuatro modelos de proveedores distintos | `core/models.py` |

## Decisiones

**El contenido de un mensaje es una lista de `Part`, no un string.** Anthropic solo
acepta `cache_control` colgado de un bloque de contenido. Si el contenido fuera un
string no habría dónde marcar el fin del prefijo estático. `core/client.py` traduce:
bloques con la marca para Anthropic, string plano para los que cachean por prefijo
automático.

**El bloque estático vive fuera de la conversación**, persistido en
`prompts/static_context.md`. El ejercicio 2 exige que cada intento abra conversación
nueva y que aun así haya cache hit, y eso solo pasa si el prefijo sale byte-idéntico.
Si hubiera que volver a pegarlo en cada intento, un espacio de más mata el hit.

**El `reasoning_effort` es por turno, no por conversación.** La consigna solo obliga a
reiniciar el chat al cambiar de modelo. Con el effort por turno, comparar `low` contra
`high` sobre la misma pregunta queda dentro de un mismo log.

**Sin streaming.** La respuesta viene como un JSON completo con el `usage` adentro.
Con streaming el usage llegaría recién en el último chunk y habría que parsear SSE en
las dos puntas a cambio de nada que la consigna pida.

**`cache_discount` se guarda con signo.** Anthropic cobra la escritura de cache a 1.25×
el precio de input y la lectura a 0.1×: la primera pasada cuesta *más*. Mostrarlo en
valor absoluto escondería ese hecho, que va al informe del ejercicio 3.

**La UI no conoce ningún id de modelo.** Pide `GET /api/models` y deriva de las `caps`
qué controles mostrar. Agregar un modelo es agregar una entrada en `core/models.py`.

## Arquitectura

```
core/models.py        registry: id, proveedor, slot, caps, pricing
core/usage.py         Usage: parseo del payload + suma para los totales
core/conversation.py  Part / Message / TurnParams / Turn / Conversation
core/client.py        OpenRouter: caps -> parámetros -> HTTP -> (texto, usage)
core/mdlog.py         escritura del log .md
core/store.py         conversaciones vivas + bloque estático persistido
core/tokens.py        estimación grosera de tokens (solo para avisos de la UI)
app/main.py           FastAPI; las rutas validan y delegan
app/static/           index.html, style.css, app.js
```

## API

| Ruta | Qué hace |
|---|---|
| `GET /api/models` | registry serializado: caps, pricing, contexto, mínimo de cache |
| `GET /api/static-context` · `PUT` | lee y escribe `prompts/static_context.md` |
| `POST /api/conversations` | `{model_id}` → abre conversación y su log |
| `GET /api/conversations/{id}` | historial, totales y contador de prompts |
| `POST /api/chat` | `{conversation_id, text, params}` → respuesta, usage y totales |

`params` acepta `reasoning_effort`, `thinking_budget` y `json_schema`. El backend
descarta lo que el modelo no soporta **antes** de armar el turno, para que el log
refleje lo que se mandó y no lo que pidió la UI.

## Formato del log

`logs/<YYYYMMDD-HHMMSS>__slot<N>__<modelo>.md`, reescrito entero después de cada turno
(no al cerrar: si la app se cae, lo que ya pasó ya está en disco). Contiene front-matter
con modelo y slot, el bloque estático con su tamaño estimado, y por turno el prompt, la
respuesta, los parámetros usados y una tabla de usage. El footer trae el contador de
prompts de usuario y los totales.
