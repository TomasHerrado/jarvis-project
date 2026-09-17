"""
Traduce texto en lenguaje natural a una llamada de skill concreta,
usando un modelo local corrido con Ollama. Puede recibir historial
reciente para entender referencias a comandos anteriores.
"""

import json
import re
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from automation.skills import SKILLS

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3.2"


def _formatear_historial(historial: list) -> str:
    if not historial:
        return "No hay conversación previa."

    lineas = []
    for h in historial:
        lineas.append(f'Usuario dijo: "{h["texto_usuario"]}" -> Jarvis ejecutó: {h["skill_ejecutada"] or "nada"}')
    return "\n".join(lineas)


def _construir_prompt(texto_usuario: str, historial: list = None) -> str:
    descripcion_skills = "\n".join(
        f'- "{nombre}": {info["descripcion"]} Parámetros: {info["parametros"]}'
        for nombre, info in SKILLS.items()
    )

    contexto_previo = _formatear_historial(historial)

    return f"""Sos el módulo de interpretación de un asistente de voz llamado Jarvis.
Tu única tarea es traducir lo que dice el usuario a UNA de las siguientes acciones (skills):

{descripcion_skills}

Contexto de la conversación reciente (puede ser útil si el usuario hace referencia a algo anterior, como "hacelo de nuevo" o "y ahora"):
{contexto_previo}

Reglas:
- Respondé ÚNICAMENTE con un JSON válido, sin texto antes ni después, sin markdown.
- El JSON debe tener esta forma exacta: {{"skill": "nombre_skill", "params": {{...}}}}
- Si el usuario no pide ninguna acción reconocible, respondé: {{"skill": null, "params": {{}}}}
- Interpretá la intención aunque esté mal dicho, con errores de transcripción, sin tildes, o con palabras de más.
- Para nombres de aplicaciones o archivos, extraé solo el nombre relevante, sin artículos ni palabras sueltas.
- Usá el contexto previo SOLO si el mensaje actual hace referencia clara a algo anterior (ej: "hacelo de nuevo", "y ahora qué"). Si el mensaje actual es una acción nueva y completa, ignorá el contexto.

Usuario dijo ahora: "{texto_usuario}"

JSON:"""


def _extraer_json(texto_crudo: str) -> dict:
    match = re.search(r"\{.*\}", texto_crudo, re.DOTALL)
    if not match:
        return {"skill": None, "params": {}}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"skill": None, "params": {}}


def interpretar(texto_usuario: str, historial: list = None) -> dict:
    """Devuelve {"skill": nombre_o_None, "params": {...}}"""
    payload = {
        "model": MODEL,
        "prompt": _construir_prompt(texto_usuario, historial),
        "stream": False,
        "options": {"temperature": 0.1},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[intent_parser] Error contactando a Ollama: {e}")
        return {"skill": None, "params": {}}

    texto_generado = response.json().get("response", "")
    return _extraer_json(texto_generado)


if __name__ == "__main__":
    pruebas = [
        "abrí la calculadora",
        "abrime spotify porfa",
        "¿qué procesos consumen más ram?",
        "buscá el archivo curriculum tomas herrado",
        "qué día es hoy",
    ]
    for texto in pruebas:
        resultado = interpretar(texto)
        print(f'"{texto}" -> {resultado}')