# Evidencia del ejercicio 1

Pruebas realizadas el 18 de septiembre de 2026 desde la interfaz en Chrome, en http://localhost:8000. Las consultas se enviaron desde el chat y los logs fueron escritos automáticamente por la aplicación. Este registro cubre las cuatro pruebas solicitadas del ejercicio 1.

## Usage por respuesta

Valores extraídos de los meta.json de las conversaciones. Costos en USD con precisión suficiente para reproducir los totales.

| Prueba | Entrada | Salida | Razonamiento | Cacheados | Costo USD |
|---|---:|---:|---:|---:|---:|
| OpenAI low | 50 | 848 | 335 | 0 | 0.00102760 |
| OpenAI high | 611 | 835 | 315 | 0 | 0.00112420 |
| Claude: primera consulta | 4918 | 208 | 0 | 0 | 0.00717975 |
| Claude: segunda consulta | 5155 | 208 | 0 | 4887 | 0.00179670 |
| DeepSeek | 4346 | 887 | 707 | 0 | 0.00065635 |
| Gemini: consulta inicial sin esquema efectivo | 22 | 2829 | 1038 | 0 | 0.01062525 |
| Gemini: JSON Schema efectivo | 109 | 205 | 190 | 0 | 0.00085050 |

Los tokens de razonamiento se presentan como una métrica separada; no se sumaron de nuevo a los tokens de salida para calcular el costo.

## Resultados

### OpenAI: comparación de effort

La misma pregunta se envió dos veces en una conversación: primero low, después high. Ambas respuestas dieron 19 maneras, resultado verificado por enumeración de las ternas enteras entre 2 y 6 que suman 12. El segundo turno produjo 315 tokens de razonamiento frente a 335 del primero; el costo pasó de USD 0.00102760 a USD 0.00112420. High no generó más razonamiento en esta prueba.

El segundo turno incluye el primer prompt y la primera respuesta en su historial: recibió 611 tokens de entrada frente a 50. Por eso la diferencia de costo no puede atribuirse exclusivamente al effort. No se configuró JSON Schema ni contexto estático.

### Claude: cache hit

Se guardaron los 15.242 caracteres del encabezado solicitado más mission.md y SPEC.md completos. Se verificó que el texto coincidiera exactamente con los archivos. La interfaz estimó 3.810 tokens. Thinking quedó vacío y JSON Schema desactivado. Se enviaron dos consultas idénticas consecutivas, sin cambiar el contexto.

La segunda respuesta reportó 4.887 tokens cacheados de 5.155 tokens de entrada: cache hit demostrado. Ambas respuestas produjeron 208 tokens de salida. El costo total por respuesta bajó de USD 0.00717975 a USD 0.00179670, una reducción del 74.98%. El segundo turno también incorpora historial; se registra el resultado de estas llamadas concretas.

cache_discount figura como 0 en los registros, incluso con el cache hit. Ese campo no se usó para afirmar un ahorro nulo: la reducción anterior se calculó directamente a partir de los costos reportados. No se verificó si el campo faltaba en la respuesta original de la API, porque no se conserva el payload crudo.

### DeepSeek: comparación de costo

Se abrió una conversación nueva de DeepSeek con exactamente el mismo contexto estático y la misma pregunta del primer turno de Claude. El selector de effort quedó en off: el cliente omitió una configuración explícita de reasoning, aunque el proveedor reportó 707 tokens de razonamiento.

DeepSeek costó USD 0.00065635, frente a USD 0.00717975 del primer turno de Claude: 10.94 veces menos. Produjo 887 tokens de salida frente a 208 de Claude; los tokens de entrada fueron 4.346 frente a 4.918. Se compara el costo de estas respuestas, con distintos tokenizadores, salida y comportamiento de cache; el factor no representa una relación universal de precios.

### Gemini: JSON Schema

La primera consulta dejó el esquema visible en la interfaz, pero el log registró json_schema=null y la respuesta fue texto con código. Se conserva esa conversación como incidencia de la prueba; no cuenta como demostración de salidas estructuradas.

Se aplicó el esquema mediante escritura con el teclado nativo y salida del campo. Se comprobó que el esquema persistiera al volver a renderizar los controles antes de enviar la consulta en una conversación nueva. El log final contiene el esquema exacto solicitado en params.json_schema.

La respuesta final se parseó con json.loads y se verificaron las tres claves, sus valores, la ausencia de claves adicionales y que tests sea un entero:

```json
{"nombre":"vida.py","lenguaje":"Python","tests":9}
```

## Logs conservados

- [OpenAI: low y high](../chats/20260918-000744__slot1__gpt-5.6-luna/log.md) — conversación 3cf1efb4c096, 2 prompt(s).
- [Claude: primera y segunda consulta](../chats/20260918-001142__slot2__claude-haiku-4.5/log.md) — conversación 5893290a58ae, 2 prompt(s).
- [DeepSeek: comparación](../chats/20260918-001229__slot4__deepseek-v4-flash-0731/log.md) — conversación d39916e9dfbe, 1 prompt(s).
- [Gemini: consulta inicial sin esquema efectivo](../chats/20260918-001255__slot3__gemini-3.7-flash/log.md) — conversación a142f9e28b5b, 1 prompt(s).
- [Gemini: JSON Schema validado](../chats/20260918-001409__slot3__gemini-3.7-flash/log.md) — conversación 181fac6da7fd, 1 prompt(s).

Cada carpeta también contiene su meta.json con los parámetros y el usage. No se modificaron ni borraron logs o respuestas. Las conversaciones vacías creadas al configurar el chat se conservaron; no generaron llamadas al modelo.

## Total de estas pruebas

Se realizaron 7 consultas en 5 conversaciones con respuestas, incluyendo la consulta inicial de Gemini. Costo total registrado: **USD 0.02326035**.

No incluye conversaciones anteriores a estas pruebas y no se contrastó todavía con el dashboard de OpenRouter. No constituye el informe del ejercicio 3.

Al terminar, el contexto estático global quedó vacío para las conversaciones nuevas. El contexto de Claude y DeepSeek sigue conservado dentro de sus logs y metadata. Chrome quedó abierto en el resultado válido de Gemini.
