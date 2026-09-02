"""API del chat. Las rutas son finitas: validan y delegan al core."""
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core import models, store
from core.client import OpenRouterClient, OpenRouterError
from core.conversation import TurnParams
from core.models import Cap
from core.tokens import estimate

load_dotenv()

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="TP3 · Chat multi-modelo")
STORE = store.Store()


def _client() -> OpenRouterClient:
    try:
        return OpenRouterClient()
    except OpenRouterError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


def _model_or_404(model_id: str):
    try:
        return models.get(model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


def _conversation_or_404(conversation_id: str):
    try:
        return STORE.get(conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


def _conv_state(conv) -> dict:
    return {
        "id": conv.id,
        "model_id": conv.model_id,
        "log_path": conv.log_path,
        "prompt_count": conv.prompt_count,
        "totals": conv.totals.as_dict(),
        "static_context": conv.static_context,
        "static_context_tokens": estimate(conv.static_context),
    }


# --- requests -------------------------------------------------------------

class NewConversation(BaseModel):
    model_id: str


class StaticContext(BaseModel):
    text: str = ""


class Params(BaseModel):
    reasoning_effort: str | None = None
    thinking_budget: int | None = None
    json_schema: dict | None = None


class ChatRequest(BaseModel):
    conversation_id: str
    text: str = Field(min_length=1)
    params: Params = Params()


# --- rutas ----------------------------------------------------------------

@app.get("/api/models")
def list_models():
    return {"models": [models.as_dict(m) for m in models.MODELS]}


@app.get("/api/static-context")
def get_static_context():
    text = store.read_static_context()
    return {"text": text, "tokens": estimate(text)}


@app.put("/api/static-context")
def put_static_context(body: StaticContext):
    store.write_static_context(body.text)
    return {"text": body.text, "tokens": estimate(body.text)}


@app.post("/api/conversations")
def create_conversation(body: NewConversation):
    model = _model_or_404(body.model_id)
    # El estatico se congela al abrir: durante la conversacion no cambia, para
    # que el prefijo se mantenga estable turno a turno.
    conv = STORE.new(model, store.read_static_context())
    return _conv_state(conv)


@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    conv = _conversation_or_404(conversation_id)
    return {
        **_conv_state(conv),
        "turns": [
            {
                "n": t.n,
                "prompt": t.prompt,
                "reply": t.reply,
                "usage": t.usage.as_dict(),
                "params_label": t.params.label(),
            }
            for t in conv.turns
        ],
    }


@app.post("/api/chat")
def chat(body: ChatRequest):
    conv = _conversation_or_404(body.conversation_id)
    model = _model_or_404(conv.model_id)

    # Descartamos lo que el modelo no soporta antes de armar el turno, para que
    # el log refleje lo que realmente se mando y no lo que pidio la UI.
    p = body.params
    params = TurnParams(
        reasoning_effort=p.reasoning_effort if model.has(Cap.REASONING_EFFORT) else None,
        thinking_budget=p.thinking_budget if model.has(Cap.THINKING_BUDGET) else None,
        json_schema=p.json_schema if model.has(Cap.STRUCTURED_OUTPUT) else None,
    )

    try:
        reply, usage, _ = _client().complete(model, conv.outbound_messages(body.text), params)
    except OpenRouterError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    turn = STORE.record(conv, model, body.text, reply, usage, params)
    return {
        "turn": {"n": turn.n, "reply": reply, "usage": usage.as_dict(), "params_label": params.label()},
        **_conv_state(conv),
    }


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
