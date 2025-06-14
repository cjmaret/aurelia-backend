import logging
import os
# used for file manipulation (copying files)
import shutil
import uuid
from app.mongo.schemas.db_user_schema import DbUserSchema
from paths import DATA_DIR
# handles audio file conversion and manipulation
from pydub import AudioSegment
import nltk
from ai_models.whisper_model import whisper_model

nltk.download("punkt")
nltk.download("punkt_tab")


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def format_and_transcribe_audio(file, user: DbUserSchema):

    print(f"Received file: {file.filename}")

    unique_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".m4a"
    file_path = os.path.join(DATA_DIR, f"{unique_id}{ext}")

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

    print(f"File saved to: {file_path}")
    # convert to WAV
    wav_path = clean_audio(file_path)

    if is_silent(wav_path):
        raise ValueError("No speech detected in the audio file (silence).")

    print(f"Converted to WAV: {wav_path}")
    
    target_language = user["targetLanguage"]

    # transcribe
    transcription = whisper_model.transcribe(wav_path, target_language)
    if not transcription.strip():
        raise ValueError("No speech detected in the audio file.")

    # clean up temporary files
    try:
        os.remove(file_path)
        os.remove(wav_path)
    except Exception:
        pass

    return transcription


def clean_audio(input_path: str) -> str:
    output_path = input_path.replace(".mp3", ".wav").replace(".m4a", ".wav")
    convert_to_wav(input_path, output_path)
    print(f"Converted audio file saved to: {output_path}")
    return output_path

# wav is commonly used for audio processing because its uncompressed
def convert_to_wav(input_path: str, output_path: str):
    print(f"Converting audio file to WAV: {input_path} -> {output_path}")
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(
        16000)  # mono, 16khz (standard format)
    audio.export(output_path, format="wav")


def is_silent(wav_path: str, silence_thresh: float = -40.0) -> bool:
    audio = AudioSegment.from_file(wav_path)
    print(f"Is audio silent?: {audio.dBFS < silence_thresh}")
    return audio.dBFS < silence_thresh

def transcribe(wav_path: str) -> str:
    print(f"Transcribing audio file: {wav_path}")
    thing = whisper_model.transcribe(wav_path)
    print(f"Transcription result: {thing}")
    return thing
