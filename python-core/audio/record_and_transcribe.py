import wave
import numpy as np
import sounddevice as sd
import webrtcvad
import keyboard
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30  # webrtcvad solo acepta 10, 20 o 30 ms
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
SILENCE_LIMIT_MS = 1000  # ms de silencio antes de cortar la grabación
SILENCE_FRAMES = SILENCE_LIMIT_MS // FRAME_DURATION_MS

vad = webrtcvad.Vad(2)  # agresividad 0-3 (0 = permisivo, 3 = estricto)


def grabar_audio():
    print("Presioná ESPACIO para empezar a grabar...")
    keyboard.wait("space")
    print("Grabando... hablá ahora")

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

    print("Grabación terminada.")
    return np.concatenate(buffer, axis=0)


def guardar_wav(audio, path="temp.wav"):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # int16 = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return path


def transcribir(path):
    # "small" es un buen punto medio: razonable en CPU y bastante preciso en español.
    # Si te resulta lento, probá "base"; si te sobra potencia, "medium".
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(path, language="es")
    return " ".join(segment.text for segment in segments).strip()


if __name__ == "__main__":
    audio = grabar_audio()
    path = guardar_wav(audio)
    print("Transcribiendo...")
    texto = transcribir(path)
    print(f'Jarvis escuchó: "{texto}"')