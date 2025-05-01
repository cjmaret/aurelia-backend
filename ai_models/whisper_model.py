import whisper
from paths import MODEL_SIZE

class WhisperModel:
    def __init__(self):
        print(f"Loading Whisper model ({MODEL_SIZE})...")
        self.model = whisper.load_model(MODEL_SIZE)

    def transcribe(self, audio_path: str, target_language: str = "en"):
        result = self.model.transcribe(audio_path, language=target_language)
        return result["text"]

whisper_model = WhisperModel()
