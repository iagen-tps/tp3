"""Estado de la sesion: conversaciones vivas y el bloque estatico persistido.

El bloque estatico vive en disco y *fuera* de las conversaciones a proposito.
El ejercicio 2 exige que cada intento abra conversacion nueva y que igual haya
cache hit, y eso solo pasa si el prefijo sale byte-identico entre intentos: si
hubiera que volver a pegarlo cada vez, un espacio de mas mata el hit.
"""
from pathlib import Path

from core import mdlog
from core.conversation import Conversation, TurnParams
from core.models import Model
from core.usage import Usage

STATIC_CONTEXT_PATH = Path("prompts/static_context.md")


def read_static_context(path: Path = STATIC_CONTEXT_PATH) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_static_context(text: str, path: Path = STATIC_CONTEXT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Store:
    def __init__(self, logs_dir: Path = mdlog.LOGS_DIR):
        self.logs_dir = logs_dir
        self._conversations: dict[str, Conversation] = {}

    def new(self, model: Model, static_context: str) -> Conversation:
        conv = Conversation(model_id=model.id, static_context=static_context)
        self._conversations[conv.id] = conv
        # Escribimos el log ya vacio: el archivo existe desde el minuto cero y
        # la UI puede mostrar su path antes del primer mensaje.
        conv.log_path = str(mdlog.write(conv, model, self.logs_dir))
        return conv

    def get(self, conversation_id: str) -> Conversation:
        try:
            return self._conversations[conversation_id]
        except KeyError:
            raise ValueError(f"Conversacion desconocida: {conversation_id!r}") from None

    def record(
        self, conv: Conversation, model: Model, prompt: str, reply: str,
        usage: Usage, params: TurnParams,
    ):
        turn = conv.record(prompt, reply, usage, params)
        conv.log_path = str(mdlog.write(conv, model, self.logs_dir))
        return turn
