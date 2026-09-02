"""Tests del core: parseo de usage, traduccion caps -> request, y log .md.

Sin red: los payloads son fijos.
"""
import json
from pathlib import Path

import pytest

from core import models
from core.client import build_body, render_message
from core.conversation import Conversation, Message, Part, TurnParams
from core.models import Cap
from core.usage import Usage

GPT = models.get("openai/gpt-5.6-luna")
HAIKU = models.get("anthropic/claude-haiku-4.5")
GEMINI = models.get("google/gemini-3.7-flash")
DEEPSEEK = models.get("deepseek/deepseek-v4-flash-0731")


# --- usage ---------------------------------------------------------------

def test_usage_parsea_el_payload_completo():
    u = Usage.from_payload({
        "prompt_tokens": 3480,
        "completion_tokens": 512,
        "prompt_tokens_details": {"cached_tokens": 3412},
        "completion_tokens_details": {"reasoning_tokens": 340},
        "cost": 0.00214,
        "cache_discount": 0.0031,
    })
    assert (u.prompt_tokens, u.completion_tokens) == (3480, 512)
    assert (u.cached_tokens, u.reasoning_tokens) == (3412, 340)
    assert u.fresh_prompt_tokens == 68
    assert u.cache_hit


def test_usage_sin_detalles_no_explota():
    u = Usage.from_payload({"prompt_tokens": 10, "completion_tokens": 5})
    assert u.cached_tokens == 0 and u.reasoning_tokens == 0
    assert not u.cache_hit
    assert Usage.from_payload(None) == Usage()


def test_cache_discount_negativo_se_preserva():
    # Escribir cache en Anthropic cuesta 1.25x el input: la primera pasada
    # sale mas cara, y eso tiene que llegar al informe con signo.
    u = Usage.from_payload({"cache_discount": -0.0004})
    assert u.cache_discount == pytest.approx(-0.0004)


def test_usages_se_suman_para_los_totales():
    a = Usage(prompt_tokens=100, completion_tokens=10, cached_tokens=80, cost=0.001)
    b = Usage(prompt_tokens=200, completion_tokens=20, cached_tokens=150, cost=0.002)
    total = sum([a, b])  # sum() arranca en 0
    assert total.prompt_tokens == 300
    assert total.cached_tokens == 230
    assert total.cost == pytest.approx(0.003)


# --- traduccion caps -> request ------------------------------------------

def test_anthropic_marca_cache_control_en_la_ultima_parte_cacheable():
    msg = Message(role="system", parts=[
        Part("contrato", cacheable=True),
        Part("ejemplos", cacheable=True),
        Part("lo que cambia"),
    ])
    blocks = render_message(msg, HAIKU)["content"]
    assert isinstance(blocks, list)
    assert "cache_control" not in blocks[0]
    assert blocks[1]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in blocks[2]


def test_los_demas_proveedores_reciben_content_string():
    msg = Message(role="system", parts=[Part("contrato", cacheable=True), Part(" y mas")])
    for model in (GPT, GEMINI, DEEPSEEK):
        assert not model.has(Cap.EXPLICIT_CACHE)
        assert render_message(msg, model)["content"] == "contrato y mas"


def test_una_parte_cacheable_vacia_no_gasta_el_breakpoint():
    msg = Message(role="system", parts=[Part("   ", cacheable=True)])
    assert "cache_control" not in render_message(msg, HAIKU)["content"][0]


def test_effort_solo_va_a_los_modelos_que_lo_soportan():
    params = TurnParams(reasoning_effort="high")
    msgs = [Message.of("user", "hola")]
    assert build_body(GPT, msgs, params)["reasoning"] == {"effort": "high"}
    # Haiku 4.5 no soporta reasoning_effort: se descarta en vez de romper.
    assert "reasoning" not in build_body(HAIKU, msgs, params)


def test_thinking_budget_va_a_haiku():
    body = build_body(HAIKU, [Message.of("user", "hola")], TurnParams(thinking_budget=4000))
    assert body["reasoning"] == {"max_tokens": 4000}


def test_json_schema_arma_response_format():
    schema = {"name": "vida", "schema": {"type": "object", "properties": {"a": {"type": "string"}}}}
    body = build_body(GEMINI, [Message.of("user", "hola")], TurnParams(json_schema=schema))
    rf = body["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["name"] == "vida"
    assert rf["json_schema"]["schema"]["type"] == "object"


def test_el_body_siempre_pide_el_usage():
    body = build_body(DEEPSEEK, [Message.of("user", "hola")], TurnParams())
    assert body["usage"] == {"include": True}
    assert json.dumps(body)  # serializable


# --- conversacion ---------------------------------------------------------

def test_el_estatico_va_primero_y_marcado():
    c = Conversation(model_id=HAIKU.id, static_context="EL CONTRATO")
    msgs = c.outbound_messages("hola")
    assert msgs[0].role == "system" and msgs[0].parts[0].cacheable
    assert msgs[-1].role == "user" and msgs[-1].text == "hola"


def test_sin_estatico_no_se_manda_system_vacio():
    c = Conversation(model_id=HAIKU.id, static_context="   ")
    assert [m.role for m in c.outbound_messages("hola")] == ["user"]


def test_el_prefijo_sale_identico_en_conversaciones_distintas():
    # Es lo que hace posible el cache hit del ejercicio 2: cada intento abre
    # conversacion nueva, pero el prefijo tiene que salir byte-identico.
    estatico = "EL CONTRATO\ncon sus ejemplos"
    a = Conversation(model_id=DEEPSEEK.id, static_context=estatico)
    b = Conversation(model_id=DEEPSEEK.id, static_context=estatico)
    ba = build_body(DEEPSEEK, a.outbound_messages("intento 1"), TurnParams())
    bb = build_body(DEEPSEEK, b.outbound_messages("intento 2"), TurnParams())
    assert ba["messages"][0] == bb["messages"][0]


def test_record_acumula_historial_totales_y_contador_de_prompts():
    c = Conversation(model_id=GPT.id)
    c.record("p1", "r1", Usage(prompt_tokens=10, completion_tokens=5, cost=0.001), TurnParams())
    c.record("p2", "r2", Usage(prompt_tokens=20, completion_tokens=8, cost=0.002), TurnParams())
    assert c.prompt_count == 2
    assert [m.role for m in c.history] == ["user", "assistant", "user", "assistant"]
    assert c.totals.prompt_tokens == 30
    assert c.totals.cost == pytest.approx(0.003)
    # El turno siguiente arrastra el historial completo.
    assert len(c.outbound_messages("p3")) == 5


# --- log .md --------------------------------------------------------------

def _conv_con_dos_turnos():
    c = Conversation(model_id=HAIKU.id, static_context="EL CONTRATO")
    c.record("p1", "r1", Usage(3480, 512, 3412, 340, 0.00214, -0.0004), TurnParams(thinking_budget=4000))
    c.record("p2", "r2", Usage(3600, 200, 3412, 10, 0.0011, 0.0031), TurnParams())
    return c


def test_el_log_registra_prompts_usage_y_totales(tmp_path):
    from core import mdlog

    c = _conv_con_dos_turnos()
    p = mdlog.write(c, HAIKU, logs_dir=tmp_path)
    md = p.read_text(encoding="utf-8")

    assert "slot: 2" in md and HAIKU.id in md
    assert "**Prompts de usuario: 2**" in md
    assert "thinking_budget=4000" in md          # los params quedan por turno
    assert "Cache hit" in md
    assert "-$0.000400" in md                    # el discount negativo, con signo
    assert "7,080" in md and "$0.003240" in md   # totales


def test_el_log_es_idempotente_y_reescribe_completo(tmp_path):
    from core import mdlog

    c = _conv_con_dos_turnos()
    primero = mdlog.write(c, HAIKU, logs_dir=tmp_path).read_text()
    segundo = mdlog.write(c, HAIKU, logs_dir=tmp_path).read_text()
    assert primero == segundo
    assert len(list(tmp_path.iterdir())) == 1


def test_el_nombre_del_log_identifica_slot_y_modelo(tmp_path):
    from core import mdlog

    p = mdlog.path_for(Conversation(model_id=DEEPSEEK.id), DEEPSEEK, logs_dir=tmp_path)
    assert p.name.endswith("__slot4__deepseek-v4-flash-0731.md")


def test_el_bloque_estatico_con_backticks_no_rompe_el_log(tmp_path):
    from core import mdlog

    c = Conversation(model_id=HAIKU.id, static_context="ejemplo:\n```python\nx = 1\n```")
    md = mdlog.write(c, HAIKU, logs_dir=tmp_path).read_text()
    assert "````text" in md      # la valla se alarga para envolver el ejemplo


def test_abrir_una_conversacion_no_escribe_log_hasta_el_primer_turno(tmp_path):
    from core.store import Store

    s = Store(logs_dir=tmp_path)
    conv = s.new(HAIKU, "EL CONTRATO")
    assert conv.log_path                       # el path ya se conoce
    assert not list(tmp_path.glob("*.md"))     # pero el archivo todavia no existe

    s.record(conv, HAIKU, "p1", "r1", Usage(10, 5, cost=0.001), TurnParams())
    assert [p.name for p in tmp_path.glob("*.md")] == [Path(conv.log_path).name]
