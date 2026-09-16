"""Estado de la sesion: conversaciones vivas y el bloque estatico persistido.

Las conversaciones se guardan en `chats/<stamp>__slotN__modelo/` con
`meta.json` (estado reconstruible) y `log.md` (evidencia de auditoria).

El bloque estatico vive en disco y *fuera* de las conversaciones a proposito.
El ejercicio 2 exige que cada intento abra conversacion nueva y que igual haya
cache hit, y eso solo pasa si el prefijo sale byte-identico entre intentos: si
hubiera que volver a pegarlo cada vez, un espacio de mas mata el hit.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

from core import mdlog
from core.conversation import Conversation, Message, Turn, TurnParams
from core.models import Model
from core.usage import Usage

STATIC_CONTEXT_PATH = Path("prompts/static_context.md")
CHATS_DIR = mdlog.CHATS_DIR


def read_static_context(path: Path = STATIC_CONTEXT_PATH) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_static_context(text: str, path: Path = STATIC_CONTEXT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _params_dict(p: TurnParams) -> dict:
    return {
        "reasoning_effort": p.reasoning_effort,
        "thinking_budget": p.thinking_budget,
        "json_schema": p.json_schema,
    }


def _params_from_dict(d: dict | None) -> TurnParams:
    d = d or {}
    return TurnParams(
        reasoning_effort=d.get("reasoning_effort"),
        thinking_budget=d.get("thinking_budget"),
        json_schema=d.get("json_schema"),
    )


def meta_dict(conv: Conversation) -> dict:
    return {
        "id": conv.id,
        "model_id": conv.model_id,
        "started_at": conv.started_at.isoformat(timespec="seconds"),
        "static_context": conv.static_context,
        "prompt_count": conv.prompt_count,
        "totals": conv.totals.as_dict(),
        "title": title_of(conv),
        "turns": [
            {
                "n": t.n,
                "prompt": t.prompt,
                "reply": t.reply,
                "usage": t.usage.as_dict(),
                "params": _params_dict(t.params),
                "params_label": t.params.label(),
                "at": t.at.isoformat(timespec="seconds"),
            }
            for t in conv.turns
        ],
    }


def title_of(conv: Conversation) -> str:
    if conv.turns:
        first = conv.turns[0].prompt.strip().splitlines()[0]
        return (first[:72] + "…") if len(first) > 72 else first
    return "Chat nuevo"


def conversation_from_meta(data: dict, chat_dir: Path) -> Conversation:
    started = datetime.fromisoformat(data["started_at"])
    conv = Conversation(
        model_id=data["model_id"],
        static_context=data.get("static_context") or "",
        id=data["id"],
        started_at=started,
        chat_dir=str(chat_dir),
        log_path=str(chat_dir / "log.md"),
    )
    for t in data.get("turns") or []:
        params = _params_from_dict(t.get("params"))
        usage = Usage.from_dict(t.get("usage"))
        at = datetime.fromisoformat(t["at"]) if t.get("at") else datetime.now()
        turn = Turn(
            n=int(t["n"]),
            prompt=t["prompt"],
            reply=t["reply"],
            usage=usage,
            params=params,
            at=at,
        )
        conv.turns.append(turn)
        conv.history.append(Message.of("user", turn.prompt))
        conv.history.append(Message.of("assistant", turn.reply))
    return conv


def write_meta(conv: Conversation, chat_dir: Path) -> Path:
    chat_dir.mkdir(parents=True, exist_ok=True)
    path = chat_dir / "meta.json"
    path.write_text(json.dumps(meta_dict(conv), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class Store:
    def __init__(self, chats_dir: Path = CHATS_DIR):
        self.chats_dir = chats_dir
        self.chats_dir.mkdir(parents=True, exist_ok=True)
        self._conversations: dict[str, Conversation] = {}
        self._reload_from_disk()

    def _reload_from_disk(self) -> None:
        if not self.chats_dir.exists():
            return
        for child in self.chats_dir.iterdir():
            meta = child / "meta.json"
            if not (child.is_dir() and meta.exists()):
                continue
            try:
                data = json.loads(meta.read_text(encoding="utf-8"))
                conv = conversation_from_meta(data, child)
            except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError):
                continue
            self._conversations[conv.id] = conv

    def new(self, model: Model, static_context: str) -> Conversation:
        conv = Conversation(model_id=model.id, static_context=static_context)
        self._conversations[conv.id] = conv
        chat_dir = mdlog.dir_for(conv, model, self.chats_dir)
        conv.chat_dir = str(chat_dir)
        conv.log_path = str(chat_dir / "log.md")
        # meta desde el arranque para que el chat aparezca en el sidebar;
        # el log.md se escribe recien con el primer turno (evidencia no vacia).
        write_meta(conv, chat_dir)
        return conv

    def get(self, conversation_id: str) -> Conversation:
        try:
            return self._conversations[conversation_id]
        except KeyError:
            raise ValueError(f"Conversacion desconocida: {conversation_id!r}") from None

    def delete(self, conversation_id: str) -> None:
        conv = self.get(conversation_id)
        del self._conversations[conversation_id]
        if conv.chat_dir:
            path = Path(conv.chat_dir).resolve()
            root = self.chats_dir.resolve()
            if path.exists() and path.is_dir() and (path == root or root in path.parents):
                shutil.rmtree(path)

    def list_summaries(self) -> list[dict]:
        items = []
        for conv in self._conversations.values():
            items.append({
                "id": conv.id,
                "model_id": conv.model_id,
                "started_at": conv.started_at.isoformat(timespec="seconds"),
                "prompt_count": conv.prompt_count,
                "title": title_of(conv),
                "totals": conv.totals.as_dict(),
                "chat_dir": conv.chat_dir,
                "log_path": conv.log_path,
            })
        items.sort(key=lambda x: x["started_at"], reverse=True)
        return items

    def record(
        self, conv: Conversation, model: Model, prompt: str, reply: str,
        usage: Usage, params: TurnParams,
    ):
        turn = conv.record(prompt, reply, usage, params)
        chat_dir = Path(conv.chat_dir) if conv.chat_dir else mdlog.dir_for(conv, model, self.chats_dir)
        conv.chat_dir = str(chat_dir)
        conv.log_path = str(mdlog.write(conv, model, self.chats_dir))
        write_meta(conv, chat_dir)
        return turn
