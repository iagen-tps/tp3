"""Cliente de OpenRouter: traduce capacidades del modelo a parametros del request.

Todo lo especifico de cada proveedor esta aca. El resto del sistema habla en
terminos de `Part` y `TurnParams` y no sabe que Anthropic necesita bloques ni
que OpenAI usa `reasoning.effort`.

El modo por defecto es streaming (SSE): la UI recibe deltas a medida que el
modelo genera, y el `usage` llega en el ultimo chunk antes de `[DONE]`.
"""
import json
import os
from collections.abc import Iterator
from typing import Any

import httpx

from core.conversation import Message, TurnParams
from core.models import Cap, Model
from core.usage import Usage

API_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT = 180.0


class OpenRouterError(RuntimeError):
    pass


def render_message(msg: Message, model: Model) -> dict:
    """Un mensaje del dominio -> el shape que espera el proveedor.

    Con EXPLICIT_CACHE (Anthropic) el contenido va como lista de bloques y la
    marca `cache_control: {"type": "ephemeral"}` cuelga del ultimo bloque
    cacheable: significa "cachea el prompt desde el principio hasta aca".
    Sin ella, Anthropic no cachea nada por mas que el prefijo se repita.

    Con los demas (OpenAI, Gemini, DeepSeek) el cache es automatico por prefijo,
    asi que aplanamos a string y el flag `cacheable` no viaja: lo unico que
    importa ahi es que el prefijo salga byte-identico entre llamadas.
    """
    if not model.has(Cap.EXPLICIT_CACHE):
        return {"role": msg.role, "content": msg.text}

    blocks = [{"type": "text", "text": p.text} for p in msg.parts]
    # Solo el ultimo bloque cacheable lleva la marca: marcar varios gasta
    # breakpoints (Anthropic permite pocos) sin ganar nada.
    last_cacheable = max(
        (i for i, p in enumerate(msg.parts) if p.cacheable and p.text.strip()), default=None
    )
    if last_cacheable is not None:
        blocks[last_cacheable]["cache_control"] = {"type": "ephemeral"}
    return {"role": msg.role, "content": blocks}


def build_body(
    model: Model, messages: list[Message], params: TurnParams, *, stream: bool = False
) -> dict:
    """Arma el body del request descartando lo que el modelo no soporta."""
    body: dict = {
        "model": model.id,
        "messages": [render_message(m, model) for m in messages],
        # OpenRouter incluye el usage igual; pedirlo explicitamente garantiza
        # que venga el campo `cost` ya calculado en USD.
        "usage": {"include": True},
        "stream": stream,
    }

    reasoning: dict = {}
    if params.reasoning_effort and model.has(Cap.REASONING_EFFORT):
        reasoning["effort"] = params.reasoning_effort
    elif params.thinking_budget and model.has(Cap.THINKING_BUDGET):
        # Presupuesto de pensamiento: la alternativa de Claude y Gemini al effort.
        reasoning["max_tokens"] = int(params.thinking_budget)
    if reasoning:
        body["reasoning"] = reasoning

    if params.json_schema and model.has(Cap.STRUCTURED_OUTPUT):
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": params.json_schema.get("name", "respuesta"),
                "strict": True,
                "schema": params.json_schema.get("schema", params.json_schema),
            },
        }

    return body


def _delta_text(chunk: dict) -> str:
    choices = chunk.get("choices") or []
    if not choices:
        return ""
    delta = choices[0].get("delta") or {}
    return delta.get("content") or ""


class OpenRouterClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise OpenRouterError(
                "Falta OPENROUTER_API_KEY. Copiá .env.example a .env y cargá tu key."
            )

    def _headers(self) -> dict:
        h = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if url := os.environ.get("OPENROUTER_APP_URL"):
            h["HTTP-Referer"] = url
        if title := os.environ.get("OPENROUTER_APP_TITLE"):
            h["X-Title"] = title
        return h

    def stream(
        self, model: Model, messages: list[Message], params: TurnParams
    ) -> Iterator[tuple[str, Any]]:
        """Genera eventos `("delta", str)` y al final `("usage", Usage)`.

        OpenRouter manda el usage en el ultimo chunk SSE, justo antes de
        `data: [DONE]`. Los comentarios SSE (lineas que empiezan con `:`) se
        ignoran.
        """
        body = build_body(model, messages, params, stream=True)
        try:
            with httpx.stream(
                "POST", API_URL, headers=self._headers(), json=body, timeout=TIMEOUT
            ) as r:
                if r.status_code >= 400:
                    # Hay que leer el cuerpo antes de armar el error: con stream
                    # no viene parseado.
                    raw = r.read().decode("utf-8", errors="replace")
                    try:
                        data = json.loads(raw)
                        msg = (data.get("error") or {}).get("message") or raw[:300]
                    except ValueError:
                        msg = raw[:300]
                    raise OpenRouterError(f"OpenRouter respondio {r.status_code}: {msg}")

                usage: Usage | None = None
                for line in r.iter_lines():
                    if not line or line.startswith(":"):
                        continue
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except ValueError:
                        continue
                    if err := chunk.get("error"):
                        msg = err.get("message") if isinstance(err, dict) else str(err)
                        raise OpenRouterError(f"OpenRouter mid-stream: {msg}")
                    if chunk.get("usage"):
                        usage = Usage.from_payload(chunk["usage"])
                    text = _delta_text(chunk)
                    if text:
                        yield ("delta", text)

                if usage is None:
                    usage = Usage()
                yield ("usage", usage)
        except httpx.HTTPError as e:
            raise OpenRouterError(f"No se pudo llegar a OpenRouter: {e}") from e

    def complete(
        self, model: Model, messages: list[Message], params: TurnParams
    ) -> tuple[str, Usage, dict]:
        """Compat: acumula el stream y devuelve (texto, usage, body enviado)."""
        body = build_body(model, messages, params, stream=True)
        parts: list[str] = []
        usage = Usage()
        for kind, value in self.stream(model, messages, params):
            if kind == "delta":
                parts.append(value)
            elif kind == "usage":
                usage = value
        return "".join(parts), usage, body
