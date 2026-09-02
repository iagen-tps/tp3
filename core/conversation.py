"""El dominio de la conversacion.

La decision estructural esta en `Part`: el contenido de un mensaje es una
lista de bloques, no un string. Anthropic solo acepta `cache_control` colgado
de un bloque, asi que si el contenido fuera un string no habria donde marcar
donde termina el prefijo cacheable. El resto de los proveedores cachea por
prefijo automatico y no necesita la marca, pero el flag igual documenta la
frontera, que es exactamente lo que hay que mantener estable entre intentos.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from core.usage import Usage

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class Part:
    text: str
    # True en la ultima parte del prefijo estatico: "cachea todo hasta aca".
    cacheable: bool = False


@dataclass
class Message:
    role: Role
    parts: list[Part]

    @classmethod
    def of(cls, role: Role, text: str, cacheable: bool = False) -> "Message":
        return cls(role=role, parts=[Part(text=text, cacheable=cacheable)])

    @property
    def text(self) -> str:
        return "".join(p.text for p in self.parts)


@dataclass(frozen=True)
class TurnParams:
    """Las perillas del request. Son por turno, no por conversacion.

    El effort por turno es lo que permite comparar low vs high sobre la misma
    pregunta dentro de un solo log, que es el criterio de exito del slot 1.
    """

    reasoning_effort: str | None = None
    thinking_budget: int | None = None
    json_schema: dict | None = None

    def label(self) -> str:
        bits = []
        if self.reasoning_effort:
            bits.append(f"effort={self.reasoning_effort}")
        if self.thinking_budget:
            bits.append(f"thinking_budget={self.thinking_budget}")
        if self.json_schema:
            bits.append("json_schema")
        return " · ".join(bits)


@dataclass
class Turn:
    n: int
    prompt: str
    reply: str
    usage: Usage
    params: TurnParams
    at: datetime = field(default_factory=datetime.now)


@dataclass
class Conversation:
    model_id: str
    # Se congela al crear la conversacion. Cada intento del ejercicio 2 abre una
    # conversacion nueva, y el prefijo tiene que salir byte-identico o no hay hit.
    static_context: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: datetime = field(default_factory=datetime.now)
    history: list[Message] = field(default_factory=list)
    turns: list[Turn] = field(default_factory=list)
    log_path: str | None = None

    @property
    def prompt_count(self) -> int:
        """Prompts de usuario. El ejercicio 2 se audita con este numero."""
        return len(self.turns)

    @property
    def totals(self) -> Usage:
        return sum((t.usage for t in self.turns), Usage())

    def outbound_messages(self, user_text: str) -> list[Message]:
        """Los mensajes que van al request, en el orden que el cache necesita.

        Estatico primero (marcado como cacheable), historial despues, y lo que
        cambia siempre al final. Cualquier variacion adelante rompe el prefijo.
        """
        msgs: list[Message] = []
        if self.static_context.strip():
            msgs.append(Message.of("system", self.static_context, cacheable=True))
        msgs.extend(self.history)
        msgs.append(Message.of("user", user_text))
        return msgs

    def record(self, prompt: str, reply: str, usage: Usage, params: TurnParams) -> Turn:
        self.history.append(Message.of("user", prompt))
        self.history.append(Message.of("assistant", reply))
        turn = Turn(n=len(self.turns) + 1, prompt=prompt, reply=reply, usage=usage, params=params)
        self.turns.append(turn)
        return turn
