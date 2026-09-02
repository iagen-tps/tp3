"""Registry de los modelos servidos por la interfaz.

Una sola fuente de verdad: la UI arma el dropdown y decide que controles
mostrar a partir de esto, y el cliente traduce las capacidades a parametros
del request. Agregar un modelo es agregar una entrada aca.

Los precios y los `supported_parameters` estan verificados contra
`GET https://openrouter.ai/api/v1/models` el 2026-09-02.
"""
from dataclasses import dataclass, field
from enum import StrEnum


class Cap(StrEnum):
    """Capacidades declaradas por modelo."""

    REASONING_EFFORT = "reasoning_effort"      # reasoning: {"effort": low|medium|high}
    THINKING_BUDGET = "thinking_budget"        # reasoning: {"max_tokens": N}
    STRUCTURED_OUTPUT = "structured_output"    # response_format con JSON Schema
    EXPLICIT_CACHE = "explicit_cache"          # hay que marcar con cache_control
    AUTO_CACHE = "auto_cache"                  # el proveedor cachea por prefijo, solo


@dataclass(frozen=True)
class Pricing:
    """USD por token. OpenRouter los publica asi, no por millon."""

    prompt: float
    completion: float
    cache_read: float | None = None
    cache_write: float | None = None

    def per_million(self, attr: str) -> float | None:
        v = getattr(self, attr)
        return None if v is None else v * 1_000_000


@dataclass(frozen=True)
class Model:
    id: str
    provider: str
    slot: int
    label: str
    ejercita: str
    context_length: int
    pricing: Pricing
    caps: frozenset[Cap]
    # Minimo de tokens que el proveedor exige para siquiera cachear un bloque.
    # Debajo de esto, marcar cache_control no produce ningun hit.
    min_cache_tokens: int | None = None
    efforts: tuple[str, ...] = field(default=("low", "medium", "high"))

    def has(self, cap: Cap) -> bool:
        return cap in self.caps


MODELS: tuple[Model, ...] = (
    Model(
        id="openai/gpt-5.6-luna",
        provider="OpenAI",
        slot=1,
        label="GPT-5.6 Luna",
        ejercita="Effort configurable",
        context_length=1_050_000,
        pricing=Pricing(prompt=2e-7, completion=1.2e-6, cache_read=2e-8, cache_write=2.5e-7),
        caps=frozenset({Cap.REASONING_EFFORT, Cap.STRUCTURED_OUTPUT, Cap.AUTO_CACHE}),
    ),
    Model(
        id="anthropic/claude-haiku-4.5",
        provider="Anthropic",
        slot=2,
        label="Claude Haiku 4.5",
        ejercita="Caching explicito (cache_control)",
        context_length=200_000,
        pricing=Pricing(prompt=1e-6, completion=5e-6, cache_read=1e-7, cache_write=1.25e-6),
        # Haiku 4.5 no soporta reasoning_effort, solo presupuesto de thinking.
        caps=frozenset({Cap.THINKING_BUDGET, Cap.STRUCTURED_OUTPUT, Cap.EXPLICIT_CACHE}),
        min_cache_tokens=2048,
    ),
    Model(
        id="google/gemini-3.7-flash",
        provider="Google",
        slot=3,
        label="Gemini 3.7 Flash",
        ejercita="Salidas estructuradas (JSON Schema)",
        context_length=1_048_576,
        pricing=Pricing(prompt=7.5e-7, completion=3.75e-6, cache_read=7.5e-8, cache_write=4.16666e-8),
        caps=frozenset(
            {Cap.REASONING_EFFORT, Cap.THINKING_BUDGET, Cap.STRUCTURED_OUTPUT, Cap.AUTO_CACHE}
        ),
    ),
    Model(
        id="deepseek/deepseek-v4-flash-0731",
        provider="DeepSeek",
        slot=4,
        label="DeepSeek V4 Flash",
        ejercita="El escalon barato",
        context_length=1_310_720,
        # Sin cache_write: DeepSeek no cobra por escribir el cache.
        pricing=Pricing(prompt=6.5e-8, completion=1.8e-7, cache_read=1.6e-8),
        caps=frozenset({Cap.REASONING_EFFORT, Cap.STRUCTURED_OUTPUT, Cap.AUTO_CACHE}),
    ),
)

BY_ID = {m.id: m for m in MODELS}


def get(model_id: str) -> Model:
    try:
        return BY_ID[model_id]
    except KeyError:
        raise ValueError(f"Modelo desconocido: {model_id!r}") from None


def as_dict(m: Model) -> dict:
    """Serializacion para `GET /api/models`, que es lo que consume la UI."""
    return {
        "id": m.id,
        "provider": m.provider,
        "slot": m.slot,
        "label": m.label,
        "ejercita": m.ejercita,
        "context_length": m.context_length,
        "caps": sorted(m.caps),
        "efforts": list(m.efforts),
        "min_cache_tokens": m.min_cache_tokens,
        "pricing_per_million": {
            "prompt": m.pricing.per_million("prompt"),
            "completion": m.pricing.per_million("completion"),
            "cache_read": m.pricing.per_million("cache_read"),
            "cache_write": m.pricing.per_million("cache_write"),
        },
    }
