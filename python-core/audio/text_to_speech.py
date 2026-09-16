import wave
import sounddevice as sd
import soundfile as sf
from piper import PiperVoice

MODEL_PATH = "../models/piper-voices/es_AR-daniela-high.onnx"


def hablar(texto, model_path=MODEL_PATH):
    print("Cargando voz...")
    voice = PiperVoice.load(model_path)
    audio_path = "respuesta.wav"

    print("Sintetizando...")
    with wave.open(audio_path, "wb") as wav_file:
        voice.synthesize_wav(texto, wav_file)

    data, samplerate = sf.read(audio_path)
    print(f"Audio generado: {len(data)} samples, {samplerate} Hz, duración ≈ {len(data)/samplerate:.2f}s")

    print("Reproduciendo...")
    sd.play(data, samplerate)
    sd.wait()
    print("Listo.")


if __name__ == "__main__":
    hablar("Hola Tomas, soy Jarvis. Este es un test de mi voz.")