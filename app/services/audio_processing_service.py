import os
# used for file manipulation (copying files)
import shutil
# handles audio file conversion and manipulation
import subprocess
from app.mongo.schemas.db_user_schema import DbUserSchema
from paths import DATA_DIR

from ai_models.whisper_model import whisper_model


def format_and_transcribe_audio(file, user: DbUserSchema):

    file_path = os.path.join(DATA_DIR, file.filename)

    # save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Failed to save file: {str(e)}"
        }

    # convert to WAV
    wav_path = clean_audio(file_path)
    
    target_language = user["targetLanguage"]

    # transcribe
    transcription = whisper_model.transcribe(wav_path, target_language)
    if not transcription.strip():
        raise ValueError("No speech detected in the audio file.")

    return transcription


def clean_audio(input_path: str) -> str:
    output_path = input_path.replace(".mp3", ".wav").replace(".m4a", ".wav")
    convert_to_wav(input_path, output_path)
    return output_path

# wav is commonly used for audio processing because its uncompressed
def convert_to_wav(input_path: str, output_path: str):
    try:
        # Use ffmpeg to convert the audio file to WAV
        subprocess.run(
            [
                "ffmpeg",
                "-y",              # Automatically overwrite the output file
                "-i", input_path,  # Input file
                "-ac", "1",        # Mono audio
                "-ar", "16000",    # 16kHz sample rate
                output_path        # Output file
            ],
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to convert audio: {e}")


def transcribe(wav_path: str) -> str:
    return whisper_model.transcribe(wav_path)
