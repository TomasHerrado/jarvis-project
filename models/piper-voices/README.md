# Voces de Piper TTS

Los modelos `.onnx` no se versionan en git (pesan +100MB). Para descargar la voz usada actualmente:

```powershell
Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/es_AR-daniela-high.onnx" -OutFile "es_AR-daniela-high.onnx"
Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/es_AR-daniela-high.onnx.json" -OutFile "es_AR-daniela-high.onnx.json"
```