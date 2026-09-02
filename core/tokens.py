"""Estimacion grosera de tokens, solo para avisar en la UI.

No es un tokenizer: sirve para saber si el bloque estatico esta cerca del
minimo que Anthropic exige para cachear (~2048 en Haiku 4.5), que es la causa
mas comun de "puse cache_control y no hubo hit". Los numeros reales de la
factura son siempre los del usage que devuelve la API.
"""
CHARS_POR_TOKEN = 4


def estimate(text: str) -> int:
    return len(text) // CHARS_POR_TOKEN
