import wave
import numpy as np
import sounddevice as sd
import soundfile as sf
import webrtcvad
import keyboard
from faster_whisper import WhisperModel
from piper import PiperVoice
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from automation.skills import ejecutar_skill
from ai.intent_parser import interpretar
from ai.personality import reformular_respuesta, responder_conversacion
from memory.database import inicializar_db, guardar_interaccion, obtener_historial_reciente

SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
SILENCE_LIMIT_MS = 1000
SILENCE_FRAMES = SILENCE_LIMIT_MS // FRAME_DURATION_MS

TTS_MODEL_PATH = "../models/piper-voices/es_AR-daniela-high.onnx"

vad = webrtcvad.Vad(2)

print("Cargando modelos (esto pasa una sola vez al arrancar)...")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
tts_voice = PiperVoice.load(TTS_MODEL_PATH)
inicializar_db()

print("Precalentando modelos de Ollama (puede tardar un rato la primera vez)...")
interpretar("hola")  # fuerza a Ollama a cargar el modelo grande en memoria
reformular_respuesta("hola", "prueba")  # ídem con el modelo chico
print("Listo. Jarvis está en línea.\n")


def grabar_audio():
    print("Presioná ESPACIO para hablar...")
    keyboard.wait("space")
    print("Escuchando...")

    buffer = []
    silence_counter = 0
    speaking_started = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        while True:
            frame, _ = stream.read(FRAME_SIZE)
            is_speech = vad.is_speech(frame.tobytes(), SAMPLE_RATE)
            buffer.append(frame)

            if is_speech:
                speaking_started = True
                silence_counter = 0
            elif speaking_started:
                silence_counter += 1

            if speaking_started and silence_counter > SILENCE_FRAMES:
                break

    return np.concatenate(buffer, axis=0)


def guardar_wav(audio, path="temp.wav"):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return path


def transcribir(path):
    segments, _ = whisper_model.transcribe(path, language="es")
    return " ".join(segment.text for segment in segments).strip()


def hablar(texto):
    audio_path = "respuesta.wav"
    with wave.open(audio_path, "wb") as wav_file:
        tts_voice.synthesize_wav(texto, wav_file)

    data, samplerate = sf.read(audio_path)
    sd.play(data, samplerate)
    sd.wait()


def limpiar_params(params: dict) -> dict:
    limpio = {}
    for clave, valor in params.items():
        if valor == "" or valor is None:
            continue
        if isinstance(valor, str) and valor.strip().isdigit():
            valor = int(valor)
        limpio[clave] = valor
    return limpio


def procesar_comando(texto):
    historial = obtener_historial_reciente(3)
    resultado = interpretar(texto, historial)
    nombre_skill = resultado.get("skill")
    params = resultado.get("params", {})

    if not nombre_skill:
        respuesta = responder_conversacion(texto)
        guardar_interaccion(texto, None, {}, respuesta)
        return respuesta

    params_limpios = limpiar_params(params)
    respuesta_cruda = ejecutar_skill(nombre_skill, **params_limpios)
    guardar_interaccion(texto, nombre_skill, params_limpios, respuesta_cruda)
    return reformular_respuesta(texto, respuesta_cruda)

if __name__ == "__main__":
    while True:
        audio = grabar_audio()
        path = guardar_wav(audio)

        print("Transcribiendo...")
        texto_usuario = transcribir(path)
        print(f'Vos dijiste: "{texto_usuario}"')

        texto_lower = texto_usuario.lower()
        if any(palabra in texto_lower for palabra in ("salir", "salí", "chau", "chao", "terminar", "adiós", "adios")):
            hablar("Nos vemos.")
            break

        respuesta = procesar_comando(texto_usuario)
        print(f"Jarvis responde: {respuesta}")
        hablar(respuesta)
        print()