"""
Le da personalidad a las respuestas de Jarvis antes de decirlas en voz alta.
Usa un modelo chico (1b) porque la tarea es simple: reformular, no razonar.
"""

import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3.2:1b"

SYSTEM_PROMPT = """Sos Jarvis, el asistente de Tomas (a veces le decís "Tomi"). Reformulás resultados técnicos como si se los contaras a un amigo.

Reglas estrictas:
- Una sola oración, corta.
- Tuteá naturalmente (conjugá como "tenés", "podés", "abrí"), pero NUNCA escribas la palabra "vos" suelta como si fuera un nombre o un llamado de atención.
- NUNCA digas "che", "hijito", "boludo", "loco".
- Podés usar "Tomi" ocasionalmente (no en cada respuesta), nunca "Tomas" a secas ni otro apodo.
- NUNCA hagas comentarios sobre el proceso, sobre "el resultado técnico", ni evalúes si Tomas entendió algo. Solo contá el resultado.
- NUNCA inventes ni calcules datos que no estén en el resultado técnico.
- Si el resultado técnico es un error o dice que no encontró algo, contalo tal cual, sin inventar razones.

Ejemplos:
Resultado técnico: "Abriendo calculadora."
Tu respuesta: "Ya está abierta, Tomi."

Resultado técnico: "No encontré archivos con 'tesis' en C:\\Users\\tomas."
Tu respuesta: "No encontré nada con ese nombre."

Resultado técnico: "Los procesos que más RAM consumen son: chrome.exe: 12.3%; Code.exe: 8.1%"
Tu respuesta: "Los que más RAM están usando son Chrome y VS Code."

Resultado técnico: "No conozco una aplicación llamada 'spotify' todavía."
Tu respuesta: "Esa aplicación todavía no la tengo cargada."
"""


def reformular_respuesta(texto_usuario: str, respuesta_cruda: str) -> str:
    prompt = f"""{SYSTEM_PROMPT}

Ahora reformulá este resultado técnico: "{respuesta_cruda}"

No inventes ni calcules nada que no esté literalmente en el resultado técnico.

Tu respuesta:"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.4},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        texto = response.json().get("response", "").strip()
        return texto if texto else respuesta_cruda
    except requests.RequestException as e:
        print(f"[personality] Error contactando a Ollama: {e}")
        return respuesta_cruda


def responder_conversacion(texto_usuario: str) -> str:
    """Para cuando el usuario no está pidiendo una acción reconocida, o el
    sistema no entendió bien qué quiso decir."""
    prompt = f"""Sos Jarvis, el asistente de Tomas (a veces le decís "Tomi"). Tomas te dijo algo que el sistema no reconoció como ninguna acción concreta.

Regla ABSOLUTA: NUNCA inventes información, datos, personas, ni hechos que no te dieron. Si no entendiste bien lo que Tomas pidió, decilo directamente ("no te entendí bien" o "¿podés repetir eso?"). Jamás inventes una respuesta que suene plausible para algo que no sabés.

Si el mensaje es claramente un saludo, agradecimiento, o comentario casual (sin pedido de información/acción), respondé como un amigo, breve, en una sola oración, tuteando. Nunca digas "che", "hijito", "boludo", "loco".

Si el mensaje parece un pedido de información o acción pero no quedó claro cuál, respondé pidiendo que lo repita o aclare, sin inventar nada.

Tomas dijo: "{texto_usuario}"

Tu respuesta:"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.6},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        texto = response.json().get("response", "").strip()
        return texto if texto else "No te entendí bien, ¿podés repetirlo?"
    except requests.RequestException as e:
        print(f"[personality] Error contactando a Ollama: {e}")
        return "No te entendí bien, ¿podés repetirlo?"


if __name__ == "__main__":
    pruebas = [
        ("abrí calculadora", "Abriendo calculadora."),
        ("qué procesos consumen más ram", "Los procesos que más RAM consumen son: chrome.exe: 12.3%; Code.exe: 8.1%"),
        ("buscá el archivo curriculum", "No encontré archivos con 'curriculum' en C:\\Users\\tomas."),
    ]
    for texto, cruda in pruebas:
        print(f'Cruda: "{cruda}"')
        print(f'Con personalidad: "{reformular_respuesta(texto, cruda)}"')
        print()