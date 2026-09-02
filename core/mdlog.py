"""Escritura del log .md de cada conversacion.

Es la evidencia de auditoria de los ejercicios 2 y 3: cuantos prompts hubo,
que se gasto en cada uno y si hubo cache hits. Por eso el archivo se reescribe
entero despues de cada turno y no al cerrar la conversacion: si la app se cae,
lo que ya paso ya esta en disco.
"""
import re
from pathlib import Path

from core.conversation import Conversation
from core.models import Model
from core.tokens import estimate
from core.usage import Usage

LOGS_DIR = Path("logs")


def _slug(model_id: str) -> str:
    return re.sub(r"[^a-z0-9.-]+", "-", model_id.split("/")[-1].lower())


def path_for(conv: Conversation, model: Model, logs_dir: Path = LOGS_DIR) -> Path:
    stamp = conv.started_at.strftime("%Y%m%d-%H%M%S")
    return logs_dir / f"{stamp}__slot{model.slot}__{_slug(model.id)}.md"


def _fence(text: str) -> str:
    """Valla de codigo mas larga que cualquier corrida de backticks del texto.

    El bloque estatico suele traer ejemplos con ``` adentro; con una valla de 3
    el log se rompe y deja de ser evidencia legible.
    """
    mas_largo = max((len(m) for m in re.findall(r"`+", text)), default=0)
    return "`" * max(3, mas_largo + 1)


def _money(x: float) -> str:
    return f"${x:.6f}"


def _signed_money(x: float) -> str:
    return f"{'-' if x < 0 else '+'}${abs(x):.6f}"


def _usage_table(u: Usage) -> str:
    return (
        "| entrada | cacheados | nuevos | salida | razonamiento | costo | cache_discount |\n"
        "|---:|---:|---:|---:|---:|---:|---:|\n"
        f"| {u.prompt_tokens:,} | {u.cached_tokens:,} | {u.fresh_prompt_tokens:,} "
        f"| {u.completion_tokens:,} | {u.reasoning_tokens:,} "
        f"| {_money(u.cost)} | {_signed_money(u.cache_discount)} |"
    )


def render(conv: Conversation, model: Model) -> str:
    out: list[str] = []
    out.append("---")
    out.append(f"conversacion: {conv.id}")
    out.append(f"modelo: {model.id}")
    out.append(f"proveedor: {model.provider}")
    out.append(f"slot: {model.slot}")
    out.append(f"inicio: {conv.started_at.isoformat(timespec='seconds')}")
    out.append("---\n")

    out.append(f"# Slot {model.slot} · {model.label}\n")

    if conv.static_context.strip():
        n = estimate(conv.static_context)
        marca = "cache_control explicito" if model.min_cache_tokens else "prefijo automatico"
        out.append(f"## Contexto estatico (cacheable, ~{n:,} tokens, {marca})\n")
        out.append("<details><summary>ver bloque</summary>\n")
        valla = _fence(conv.static_context)
        out.append(f"{valla}text")
        out.append(conv.static_context.rstrip())
        out.append(valla + "\n")
        out.append("</details>\n")
    else:
        out.append("## Contexto estatico\n\n_(vacio)_\n")

    for t in conv.turns:
        out.append("---\n")
        out.append(f"### {t.n} · user  ·  {t.at.isoformat(timespec='seconds')}\n")
        out.append(t.prompt.rstrip() + "\n")
        etiqueta = t.params.label()
        cabecera = f"### {t.n} · assistant"
        if etiqueta:
            cabecera += f"  ·  {etiqueta}"
        out.append(cabecera + "\n")
        out.append(t.reply.rstrip() + "\n")
        out.append(_usage_table(t.usage) + "\n")
        if t.usage.cache_hit:
            out.append(
                f"> Cache hit: {t.usage.cached_tokens:,} de {t.usage.prompt_tokens:,} "
                "tokens de entrada vinieron del cache.\n"
            )

    total = conv.totals
    out.append("---\n")
    out.append("## Totales\n")
    out.append(f"**Prompts de usuario: {conv.prompt_count}**\n")
    out.append(_usage_table(total) + "\n")
    return "\n".join(out) + "\n"


def write(conv: Conversation, model: Model, logs_dir: Path = LOGS_DIR) -> Path:
    """Reescribe el log completo. Idempotente: mismo estado, mismo archivo."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    p = path_for(conv, model, logs_dir)
    p.write_text(render(conv, model), encoding="utf-8")
    return p
