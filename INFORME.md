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

## Ejercicio 3 — La cuenta final

### Tokens de pensamiento y facturación

La tabla de corridas anterior incluye los dos intentos del ejercicio 2 y sus
totales. DeepSeek reportó los tokens de pensamiento en
`completion_tokens_details.reasoning_tokens`: 2.843 en el primero y 1.530 en el
segundo. En ambas corridas se obtuvo un conteo explícito de razonamiento.

| Corrida | Salida total | Razonamiento, incluido en la salida | Salida visible: total menos razonamiento |
|---|---:|---:|---:|
| 1 | 4.222 | 2.843 | 1.379 |
| 2 | 2.198 | 1.530 | 668 |
| **Total** | **6.420** | **4.373** | **2.047** |

El razonamiento representa **68,12 % de los tokens de salida**. OpenRouter
factura esos tokens como salida: forman parte del cargo de generación aunque
la interfaz solo muestre el código final. No se agregan 4.373 tokens a los 6.420,
porque eso los contaría dos veces. Tampoco `reasoning.exclude` elimina ese cargo;
solo controla su devolución en la respuesta.
[Documentación de razonamiento](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).

### Tokens cacheados y ahorro

El primer intento reportó cero tokens cacheados; el segundo, 1.024 de sus 1.337
tokens de entrada. Entre ambos hubo **1.650 tokens de entrada nuevos** y **1.024
leídos del cache**, dentro de los 2.674 tokens de entrada totales.

El catálogo público de
[DeepSeek V4 Flash 0731](https://openrouter.ai/deepseek/deepseek-v4-flash-0731),
consultado mediante [`GET /api/v1/models`](https://openrouter.ai/api/v1/models),
devuelve USD **0,06 por millón de tokens de entrada** y USD **0,012 por millón
de tokens leídos del cache**. Con esas tarifas, el ahorro estimado es:

```text
ahorro = tokens_cacheados × (tarifa_entrada − tarifa_cache) / 1.000.000
       = 1.024 × (0,06 − 0,012) / 1.000.000
       = USD 0,000049152
```

| Corrida | Entrada sin descuento por cache, USD | Entrada con cache, USD | Ahorro estimado, USD |
|---|---:|---:|---:|
| 1 | 0,00008022 | 0,00008022 | 0 |
| 2 | 0,00008022 | 0,000031068 | 0,000049152 |
| **Total** | **0,00016044** | **0,000111288** | **0,000049152** |

En la segunda corrida, este cálculo reduce el costo de entrada en **61,27 %**.
Es una estimación con las tarifas del catálogo, no un desglose confirmado de la
factura: los logs no conservaron el proveedor de inferencia ni el ID de generación
necesario para recuperar el detalle de cada solicitud. La tarifa efectiva de esa
ruta puede ser distinta. El `cache_discount` persistido vale cero y el cliente
también usa cero cuando el campo no llega; por eso ese valor no permite concluir
que el ahorro real haya sido cero. El cache hit sí está confirmado por el usage.

Los precios de referencia de la interfaz (USD 0,065 de entrada, 0,180 de salida y
0,016 de lectura de cache por millón) corresponden a su registry y difieren del
catálogo consultado. Los cargos de la tabla de corridas son los `cost` devueltos
por OpenRouter, no cálculos hechos con esos precios de la interfaz.

### Gasto y contraste por API con OpenRouter

El gasto de los **dos intentos del ejercicio 2** es **USD 0,0014204704**. El grupo
recibió únicamente una API key, sin acceso a la cuenta ni al dashboard de
actividad. **Por esa restricción, el contraste se realizó por API en lugar de
consultar el dashboard**, mediante
[`GET /api/v1/key`](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key),
autenticado con la key local, sin incorporarla al informe ni a los logs.

La respuesta informó `usage_daily: 0.02468082` e `is_management_key: false`.
Para comparar el mismo alcance, se sumaron las pruebas del ejercicio 1 del mismo
día UTC, incluidas las dos consultas de Gemini, a las dos corridas del ejercicio 2.

| Concepto | USD |
|---|---:|
| Pruebas del ejercicio 1 del mismo día UTC | 0,02326035 |
| Dos intentos del ejercicio 2 | 0,0014204704 |
| **Suma de los logs de ese día** | **0,0246808204** |
| **Gasto diario informado por la API de OpenRouter** | **0,02468082** |
| Diferencia: logs menos API | 0,0000000004 |

La suma de los logs, redondeada a ocho decimales, coincide con el gasto diario
devuelto por OpenRouter. La diferencia indicada es de redondeo y no se agrega a
los cargos del ejercicio 2. Las pruebas del ejercicio 1 se incluyen aquí
únicamente para reconciliar el acumulado diario de la key.

**Alcance del contraste:** la coincidencia verifica el gasto diario agregado
informado por OpenRouter frente a la suma de los logs de ese día. **No pudimos
consultar el dashboard porque no tenemos acceso a la cuenta: solo recibimos la
API key.** Tampoco pudimos verificar el detalle individual de cada solicitud. El endpoint de
[actividad](https://openrouter.ai/docs/api/api-reference/analytics/get-user-activity)
exige una key de administración, capacidad que la key entregada no tiene.

### Conclusión

Mantendríamos `deepseek/deepseek-v4-flash-0731`: resolvió los nueve tests con un solo prompt de usuario.\
Probaríamos `effort: medium` para reducir el pensamiento, que representa el 68,12 % de la salida; lo adoptaríamos solo si conserva los nueve tests en un prompt.\
Conservaríamos el contrato y los ejemplos como prefijo idéntico entre intentos, porque la segunda corrida confirmó 1.024 tokens cacheados.
