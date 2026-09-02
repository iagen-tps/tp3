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

## Cómo se usa

La pantalla tiene cuatro zonas, de arriba abajo: el **selector de modelo** con las
perillas de ese modelo, el panel del **contexto estático**, el **chat**, y el
**tablero** con el acumulado de la conversación.

**1 · Elegir el modelo.** El dropdown muestra los cuatro slots con su proveedor, lo que
ejercita cada uno y su precio por millón de tokens. A la derecha aparecen solo las
perillas que ese modelo soporta: `effort` en los slots 1, 3 y 4; presupuesto de
`thinking` en los slots 2 y 3; `JSON Schema` en todos. Cambiar de modelo pide
confirmación y **abre una conversación nueva**: el log de la anterior queda cerrado con
sus totales en `logs/`.

**2 · Cargar el contexto estático.** El panel `Contexto estático` es el prefijo que el
proveedor puede cachear: el contrato, las instrucciones y los ejemplos. Se guarda en
`prompts/static_context.md` y se antepone idéntico a toda conversación nueva, que es la
condición para que haya cache hit. El aforo al costado avisa si el bloque llega al
mínimo que el proveedor exige (2048 tokens en Haiku 4.5); por debajo de eso no cachea
por más que se mande la marca. Guardar con la conversación todavía vacía la reabre, así
el bloque rige desde el primer mensaje.

**3 · Chatear.** Enter envía, Shift+Enter salta línea. Bajo cada respuesta queda la
lectura del turno: una barra a escala con la entrada que vino del cache (verde), la que
se reprocesó (gris) y la salida (violeta), y debajo los números — entrada, cacheados,
salida, razonamiento, costo y `cache_discount`. El tablero de abajo lleva el acumulado
y el **contador de prompts**, que es el número con el que se audita el ejercicio 2.

**4 · Leer el log.** El path del `.md` de la conversación en curso está a la derecha del
tablero. El archivo se crea con el primer mensaje y se reescribe entero después de cada
turno.

### Reproducir los criterios de éxito

- **Slot 1 · effort.** Misma pregunta dos veces seguidas, primero con `low` y después
  con `high`. Los dos turnos quedan en el mismo log, con sus `reasoning_tokens` y sus
  costos al lado.
- **Slot 2 · cache hit.** Pegar un bloque estático de más de 2048 tokens (el aforo se
  pone verde), guardarlo y mandar dos mensajes **seguidos**: el cache `ephemeral` vive
  unos 5 minutos. El segundo muestra `cacheados > 0` y el costo de entrada baja. Ojo con
  el `cache_discount` de la primera pasada: aparece en rojo porque **escribir** el cache
  cuesta 1.25× el input. Es esperado, y es un dato para el informe.
- **Slot 3 · salidas estructuradas.** Activar `JSON Schema` y pegar el schema en el
  campo de al lado. Si el JSON está mal formado, el borde se pone rojo.
- **Slot 4 · el escalón barato.** La misma pregunta que se le hizo al slot 2, y comparar
  el costo de los dos logs.

## Entrega

- `app/`, `core/` — la interfaz del ejercicio 1
- `logs/*.md` — los logs de las conversaciones (evidencia de los ejercicios 2 y 3)
- `vida.py` — el script del ejercicio 2
- `INFORME.md` — la cuenta final del ejercicio 3
