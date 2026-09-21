"""
Traduce texto en lenguaje natural a un PLAN de uno o más pasos (skills),
usando un modelo local corrido con Ollama.
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

    return f"""Sos el módulo de planificación de un asistente de voz llamado Jarvis.
Tu tarea es traducir lo que dice el usuario a uno o más PASOS, cada uno una de estas acciones (skills):

{descripcion_skills}

Contexto de la conversación reciente:
{contexto_previo}

Reglas:
- Respondé ÚNICAMENTE con un JSON válido, sin texto antes ni después, sin markdown.
- El JSON debe tener esta forma exacta: {{"pasos": [{{"skill": "nombre_skill", "params": {{...}}}}, ...]}}
- Si el usuario pide UNA sola acción, "pasos" tiene un solo elemento.
- Si el usuario encadena dos acciones con "y" (ej: "buscá X y abrilo"), generá dos pasos.
- Para el segundo paso de un encadenado, si un parámetro debe usar el resultado del paso anterior (ej: el archivo que se acaba de buscar), poné el valor "$anterior" en ese parámetro, en vez de inventar un valor.
- Si el usuario no pide ninguna acción reconocible (charla casual, saludo, agradecimiento), respondé: {{"pasos": []}}
- Interpretá la intención aunque esté mal dicho, con errores de transcripción, sin tildes, o con palabras de más.
- Para nombres de aplicaciones o archivos, extraé solo el nombre relevante, sin artículos ni palabras sueltas.
- Si una skill necesita un parámetro de tipo "ruta" (archivo completo) pero el usuario solo mencionó el NOMBRE del archivo sin ruta completa, generá primero un paso "buscar_archivos" con ese nombre, y el paso siguiente usando "$anterior" para la ruta — incluso si el usuario no dijo explícitamente "y" o "buscá". Ejemplo: "eliminá el archivo front" implica buscar_archivos + eliminar_archivo encadenados.

Ejemplo de nombre de archivo sin ruta completa (sin decir explícitamente "y"):
Usuario dijo: "eliminá el archivo front"
Respuesta: {{"pasos": [{{"skill": "buscar_archivos", "params": {{"nombre": "front"}}}}, {{"skill": "eliminar_archivo", "params": {{"ruta": "$anterior"}}}}]}}

Ejemplo de comando encadenado:
Usuario dijo: "buscá el archivo curriculum y abrilo"
Respuesta: {{"pasos": [{{"skill": "buscar_archivos", "params": {{"nombre": "curriculum"}}}}, {{"skill": "abrir_archivo", "params": {{"ruta": "$anterior"}}}}]}}

Usuario dijo ahora: "{texto_usuario}"

JSON:"""


def _extraer_json(texto_crudo: str) -> dict:
    match = re.search(r"\{.*\}", texto_crudo, re.DOTALL)
    if not match:
        return {"pasos": []}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"pasos": []}


def planificar(texto_usuario: str, historial: list = None) -> dict:
    """Devuelve {"pasos": [{"skill": ..., "params": {...}}, ...]}"""
    payload = {
        "model": MODEL,
        "prompt": _construir_prompt(texto_usuario, historial),
        "stream": False,
        "options": {"temperature": 0.1},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[intent_parser] Error contactando a Ollama: {e}")
        return {"pasos": []}

    texto_generado = response.json().get("response", "")
    resultado = _extraer_json(texto_generado)
    if "pasos" not in resultado:
        resultado = {"pasos": []}
    return resultado


if __name__ == "__main__":
    pruebas = [
        "abrí la calculadora",
        "buscá el archivo curriculum y abrilo",
        "qué procesos consumen más ram",
        "qué día es hoy",
    ]
    for texto in pruebas:
        resultado = planificar(texto)
        print(f'"{texto}" -> {resultado}')