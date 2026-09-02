"""El usage que devuelve OpenRouter en cada respuesta, parseado y sumable.

OpenRouter lo incluye en el cuerpo de la respuesta sin que haya que pedirlo.
Lo modelamos como un value object sumable porque el ejercicio 3 pide totales
por conversacion y por intento, no solo el numero suelto de cada turno.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    # Del prefijo de entrada, cuantos vinieron del cache en vez de reprocesarse.
    cached_tokens: int = 0
    # Tokens de pensamiento. Algunos modelos razonan sin reportarlos: ver informe.
    reasoning_tokens: int = 0
    cost: float = 0.0
    # Lo que el cache ahorro (positivo) o costo de mas (negativo): escribir cache
    # en Anthropic se cobra a 1.25x el input, asi que la primera pasada da negativo.
    cache_discount: float = 0.0

    @classmethod
    def from_payload(cls, usage: dict | None) -> "Usage":
        u = usage or {}
        prompt_details = u.get("prompt_tokens_details") or {}
        completion_details = u.get("completion_tokens_details") or {}
        return cls(
            prompt_tokens=int(u.get("prompt_tokens") or 0),
            completion_tokens=int(u.get("completion_tokens") or 0),
            cached_tokens=int(prompt_details.get("cached_tokens") or 0),
            reasoning_tokens=int(completion_details.get("reasoning_tokens") or 0),
            cost=float(u.get("cost") or 0.0),
            cache_discount=float(u.get("cache_discount") or 0.0),
        )

    @property
    def fresh_prompt_tokens(self) -> int:
        """Tokens de entrada que efectivamente se reprocesaron (no vinieron del cache)."""
        return max(self.prompt_tokens - self.cached_tokens, 0)

    @property
    def cache_hit(self) -> bool:
        return self.cached_tokens > 0

    def __add__(self, other: "Usage") -> "Usage":
        if not isinstance(other, Usage):
            return NotImplemented
        return Usage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            cost=self.cost + other.cost,
            cache_discount=self.cache_discount + other.cache_discount,
        )

    def __radd__(self, other) -> "Usage":
        # sum() arranca en 0: lo tratamos como el usage vacio.
        if other == 0:
            return self
        return self.__add__(other)

    def as_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cached_tokens": self.cached_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "fresh_prompt_tokens": self.fresh_prompt_tokens,
            "cost": self.cost,
            "cache_discount": self.cache_discount,
            "cache_hit": self.cache_hit,
        }


EMPTY = Usage()
