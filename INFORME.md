# Informe — TP3: el prompt mínimo

## Relevamiento de OpenRouter

Datos consultados en Discover, las fichas y el catálogo público de OpenRouter;
precios en USD.

### Qué hace un router

Un router de modelos elige a qué modelo enviar cada consulta según la tarea y el presupuesto, resolviendo la selección del backend sin que el usuario tenga que elegirlo manualmente. [Auto Router](https://openrouter.ai/openrouter/auto).

El Auto Router usa el gasto de la comunidad en tareas similares durante los últimos
siete días para decidir. La consulta se factura a la tarifa del modelo elegido;
el router no implica que la generación sea gratuita. El catálogo permite
[filtrar los routers de OpenRouter](https://openrouter.ai/models?arch=Router&model_authors=openrouter).

### Mapa de los siete proveedores

Se seleccionaron modelos de propósito general de las familias más avanzadas
vigentes, considerando sus descripciones y evaluaciones publicadas. Se excluyeron
modelos dedicados a generar imágenes o audio y variantes batch. Una versión más
nueva o más cara no garantiza mejores resultados en todas las tareas.

Los precios y las ventanas exactas de la tabla provienen de
[`GET /api/v1/models`](https://openrouter.ai/api/v1/models): `pricing.prompt` y
`pricing.completion`, multiplicados por 1.000.000, y `context_length`. Son las
tarifas base del catálogo para entrada sin cache y salida; pueden variar con el
proveedor de inferencia, la modalidad o el tamaño de la consulta.

| Proveedor / familia | Modelo e ID | Entrada USD / millón | Salida USD / millón | Contexto, tokens |
|---|---|---:|---:|---:|
| OpenAI | [GPT-6 Astra Pro](https://openrouter.ai/openai/gpt-6-astra-pro) — `openai/gpt-6-astra-pro` | 10,00 | 50,00 | 1.050.000 |
| Anthropic | [Claude Fable 5.1](https://openrouter.ai/anthropic/claude-fable-5.1) — `anthropic/claude-fable-5.1` | 10,00 | 50,00 | 1.000.000 |
| Grok | [Grok 4.6](https://openrouter.ai/x-ai/grok-4.6) — `x-ai/grok-4.6` | 2,00 | 6,00 | 500.000 |
| Gemini | [Gemini 3.8 Flash](https://openrouter.ai/google/gemini-3.8-flash) — `google/gemini-3.8-flash` | 0,75 | 3,75 | 1.048.576 |
| DeepSeek | [DeepSeek V4.1 Flash](https://openrouter.ai/deepseek/deepseek-v4.1-flash) — `deepseek/deepseek-v4.1-flash` | 0,15 | 0,60 | 1.048.576 |
| Qwen | [Qwen3.8 Max (0902)](https://openrouter.ai/qwen/qwen3.8-max-0902) — `qwen/qwen3.8-max-0902` | 2,00 | 6,00 | 1.000.000 |
| Kimi | [Kimi K3](https://openrouter.ai/moonshotai/kimi-k3) — `moonshotai/kimi-k3` | 2,10 | 10,95 | 1.048.576 |

GPT-6 Astra Pro es el mismo modelo Astra con `reasoning.mode: "pro"`; su ficha lo
presenta como una opción de mayor calidad para tareas complejas. Gemini 3.8 Flash
publica un índice de inteligencia de 41,2 frente a 30,4 de
[Gemini 3.1 Pro Preview](https://openrouter.ai/google/gemini-3.1-pro-preview).
DeepSeek V4.1 Flash publica 39,5 frente a 36,3 de
[V4 Pro 0813](https://openrouter.ai/deepseek/deepseek-v4-pro-0813).
Estas comparaciones fundamentan la selección de las dos variantes Flash.

#### Benchmarks y posición

Se registró el **Intelligence Index de Artificial Analysis** y su **percentil de
posición** publicado por OpenRouter en los datos de cada ficha. El percentil
expresa posición relativa; un valor mayor indica una posición más alta. No es un
porcentaje de respuestas correctas. Los niveles de esfuerzo se incluyen porque
afectan la evaluación.

| Modelo evaluado | Configuración publicada | Intelligence Index | Percentil de inteligencia | Posición mostrada en Discover |
|---|---|---:|---:|---|
| [GPT-6 Astra](https://openrouter.ai/openai/gpt-6-astra) | `max` | 52,8 | 98 | 2.º; muestra 53 por redondeo |
| [Claude Fable 5.1](https://openrouter.ai/anthropic/claude-fable-5.1) | Adaptive Reasoning, Max Effort, Default Fallback | 53,4 | 98 | 1.º; muestra 53 por redondeo |
| [Grok 4.6](https://openrouter.ai/x-ai/grok-4.6) | `high` | 44,4 | 91 | 4.º |
| [Gemini 3.8 Flash](https://openrouter.ai/google/gemini-3.8-flash) | `high` | 41,2 | 85 | 5.º |
| [DeepSeek V4.1 Flash](https://openrouter.ai/deepseek/deepseek-v4.1-flash) | Reasoning, Max Effort | 39,5 | 82 | No aparece en la lista de cinco modelos de frontera |
| [Qwen3.8 Max (0902)](https://openrouter.ai/qwen/qwen3.8-max-0902) | No especifica effort en el nombre de la evaluación | 45,4 | 93 | No aparece esa versión; el 3.º es **0803**, con 53 |
| [Kimi K3](https://openrouter.ai/moonshotai/kimi-k3) | `max` | 43,8 | 89 | No aparece en la lista de cinco modelos de frontera |

La ficha de Astra Pro no publica un benchmark propio. Por eso se registra la
evaluación de Astra `max` como referencia de la familia, sin atribuir ese resultado
al modo `pro`. La lista de [Discover](https://openrouter.ai/discover) es una
selección de cinco modelos, no una clasificación completa: estar ausente no permite
deducir un puesto global. Tampoco se trasladó el puntaje de Qwen 0803 a 0902.
Los rankings por volumen de tokens miden uso, y se distinguen de estos benchmarks.

### Comparación de parámetros entre proveedores

Se compararon las fichas de
[GPT-5.6 Luna](https://openrouter.ai/openai/gpt-5.6-luna),
[Claude Haiku 4.5](https://openrouter.ai/anthropic/claude-haiku-4.5) y
[Gemini 3.7 Flash](https://openrouter.ai/google/gemini-3.7-flash), y sus campos
`supported_parameters` y `reasoning` en el
[catálogo público](https://openrouter.ai/api/v1/models).

| Parámetro o capacidad | GPT-5.6 Luna | Claude Haiku 4.5 | Gemini 3.7 Flash |
|---|---|---|---|
| `reasoning` / `include_reasoning` | Sí | Sí | Sí |
| `reasoning_effort` | `none`, `low`, `medium`, `high`, `xhigh`, `max` | No figura | `low`, `medium`, `high` |
| Razonamiento obligatorio | No | No | Sí |
| `response_format` / `structured_outputs` | Sí | Sí | Sí |
| `temperature` | No figura | Sí | Sí |
| `top_p` | No figura | Sí | Sí |
| `top_k` | No figura | Sí | No figura |
| `seed` | Sí | No figura | Sí |
| `stop` | No figura | Sí | Sí |
| `max_tokens` | Sí | Sí | Sí |
| `max_completion_tokens` | Sí | Sí | No figura |
| `tools` / `tool_choice` | Sí | Sí | Sí |
| `frequency_penalty` / `presence_penalty` | No figuran | No figuran | No figuran |

OpenRouter unifica el control como `reasoning.effort` o `reasoning.max_tokens`.
Haiku permite presupuesto de pensamiento en tokens; en Gemini el presupuesto se
traduce a un nivel de thinking. `max_tokens` en la raíz del request limita la
generación y es distinto del presupuesto dentro de `reasoning`. Los tokens de
razonamiento se facturan como salida. [Documentación de razonamiento](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).

La API común no vuelve universales todos los parámetros: los controles deben
depender de las capacidades del modelo. Además, las rutas de inferencia pueden
diferir; `provider.require_parameters: true` permite exigir soporte de los
parámetros enviados. [Selección de proveedores](https://openrouter.ai/docs/guides/routing/provider-selection).

## Corridas del ejercicio 2

Se usó `deepseek/deepseek-v4-flash-0731` desde la interfaz de chat, con
`reasoning.effort: "high"` y JSON Schema desactivado. El
[contexto estático](prompts/static_context.md) contiene rol, contexto, contrato,
instrucciones, restricciones y nueve ejemplos de entrada/salida. El mensaje de
usuario identifica el input y solicita la implementación completa.

El **intento 1 es la conversación ganadora**: produjo
[vida.py](vida.py) con **un único prompt de usuario** y pasó los nueve tests de
la cátedra. El script se extrajo del bloque Python de la respuesta, sin cambiar
ningún carácter de código. El intento 2 repitió el mismo mensaje en una
conversación nueva para comprobar caching; también pasó los nueve tests. No hubo
intentos quemados ni prompts de corrección.

| Corrida y log | Prompts de usuario | Tests | Entrada | Salida | Razonamiento | Cacheados | Costo USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| [1 — ganadora](chats/20260918-013031__slot4__deepseek-v4-flash-0731/log.md) | 1 | 9/9 | 1.337 | 4.222 | 2.843 | 0 | 0,00094362 |
| [2 — comprobación de cache](chats/20260918-013137__slot4__deepseek-v4-flash-0731/log.md) | 1 | 9/9 | 1.337 | 2.198 | 1.530 | 1.024 | 0,0004768504 |
| **Total** | **2** | | **2.674** | **6.420** | **4.373** | **1.024** | **0,0014204704** |

Los costos conservan la precisión de los `meta.json` correspondientes; los logs
Markdown los muestran redondeados a seis decimales. Los tokens de razonamiento
son parte de la salida, no se suman otra vez al total de salida.

Se verificó que el contexto estático es idéntico en ambas conversaciones y en
`prompts/static_context.md`. El `cached_tokens: 1024` del segundo intento confirma
el cache hit, aunque `cache_discount` quedó en cero. La diferencia entre los
costos totales de las dos corridas incluye también una salida de distinta
longitud, por lo que no representa por sí sola el ahorro por caching.

Para ejecutar los tests se copiaron, sin modificaciones, el script de cada
respuesta y `tests/test_vida.py` a un directorio temporal, uno al lado del otro,
y se ejecutó `python3 test_vida.py`. Ambas corridas terminaron con `Ran 9 tests`
y `OK`. El `vida.py` de la raíz coincide exactamente con el bloque Python del
log ganador; no fue reemplazado por la respuesta del segundo intento.
