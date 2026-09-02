"""Cliente de OpenRouter: traduce capacidades del modelo a parametros del request.

Todo lo especifico de cada proveedor esta aca. El resto del sistema habla en
terminos de `Part` y `TurnParams` y no sabe que Anthropic necesita bloques ni
que OpenAI usa `reasoning.effort`.
"""
import os

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


def build_body(model: Model, messages: list[Message], params: TurnParams) -> dict:
    """Arma el body del request descartando lo que el modelo no soporta."""
    body: dict = {
        "model": model.id,
        "messages": [render_message(m, model) for m in messages],
        # OpenRouter incluye el usage igual; pedirlo explicitamente garantiza
        # que venga el campo `cost` ya calculado en USD.
        "usage": {"include": True},
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

    def complete(
        self, model: Model, messages: list[Message], params: TurnParams
    ) -> tuple[str, Usage, dict]:
        """Devuelve (texto de la respuesta, usage, body enviado)."""
        body = build_body(model, messages, params)
        try:
            r = httpx.post(API_URL, headers=self._headers(), json=body, timeout=TIMEOUT)
        except httpx.HTTPError as e:
            raise OpenRouterError(f"No se pudo llegar a OpenRouter: {e}") from e

        try:
            data = r.json()
        except ValueError:
            raise OpenRouterError(f"Respuesta no-JSON (HTTP {r.status_code}): {r.text[:300]}") from None

        if r.status_code >= 400 or "error" in data:
            msg = (data.get("error") or {}).get("message") or r.text[:300]
            raise OpenRouterError(f"OpenRouter respondio {r.status_code}: {msg}")

        choices = data.get("choices") or []
        if not choices:
            raise OpenRouterError(f"Respuesta sin choices: {str(data)[:300]}")
        text = (choices[0].get("message") or {}).get("content") or ""
        return text, Usage.from_payload(data.get("usage")), body
