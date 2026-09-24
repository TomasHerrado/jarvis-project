"""
Le da a Jarvis la capacidad de "leer" y entender texto de la pantalla usando OCR.
"""

import pytesseract
import pyautogui
import requests

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3.2"


def leer_texto_pantalla() -> str:
    """Toma una captura de pantalla completa y devuelve el texto crudo que encuentra."""
    captura = pyautogui.screenshot()
    return pytesseract.image_to_string(captura, lang="spa").strip()


def responder_sobre_pantalla(pregunta: str) -> str:
    """Lee la pantalla y le pide a Ollama que responda la pregunta del usuario
    usando solo lo relevante de ese texto (que suele venir con mucho ruido de OCR)."""
    texto_pantalla = leer_texto_pantalla()

    if not texto_pantalla:
        return "No logré leer texto en la pantalla ahora mismo."

    prompt = f"""Te paso el texto que se detectó en la pantalla de una computadora, capturado con OCR (puede tener errores de lectura, nombres de menús sueltos, texto cortado).

TEXTO DE PANTALLA:
{texto_pantalla[:1500]}

PREGUNTA DEL USUARIO: {pregunta}

Respondé la pregunta usando SOLO la información del TEXTO DE PANTALLA de arriba. No comentes sobre el OCR, sobre ruido, ni sobre estas instrucciones — andá directo al contenido. Si el texto de pantalla no tiene la información pedida, decilo. Respuesta breve:"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)
        response.raise_for_status()
        return response.json().get("response", "").strip() or "No pude interpretar la pantalla."
    except requests.RequestException as e:
        print(f"[vision] Error contactando a Ollama: {e}")
        return "Tuve un problema tratando de interpretar la pantalla."


if __name__ == "__main__":
    print("Leyendo y analizando la pantalla actual...")
    respuesta = responder_sobre_pantalla("¿qué hay en esta pantalla?")
    print(respuesta)