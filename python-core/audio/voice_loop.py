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
    """Ollama a veces manda números como texto o strings vacíos en vez de
    omitir el parámetro. Esto lo normaliza antes de llamar a la skill."""
    limpio = {}
    for clave, valor in params.items():
        if valor == "" or valor is None:
            continue  # dejamos que la skill use su valor por defecto
        if isinstance(valor, str) and valor.strip().isdigit():
            valor = int(valor)
        limpio[clave] = valor
    return limpio


def procesar_comando(texto):
    resultado = interpretar(texto)
    nombre_skill = resultado.get("skill")
    params = resultado.get("params", {})

    if not nombre_skill:
        return f"No estoy seguro de qué acción hacer con eso. Dijiste: {texto}"

    params_limpios = limpiar_params(params)
    return ejecutar_skill(nombre_skill, **params_limpios)


if __name__ == "__main__":
    while True:
        audio = grabar_audio()
        path = guardar_wav(audio)

        print("Transcribiendo...")
        texto_usuario = transcribir(path)
        print(f'Vos dijiste: "{texto_usuario}"')

        if texto_usuario.lower().strip(".,! ") in ("salir", "chau", "terminar"):
            hablar("Chau Tomas, nos vemos.")
            break

        respuesta = procesar_comando(texto_usuario)
        print(f"Jarvis responde: {respuesta}")
        hablar(respuesta)
        print()