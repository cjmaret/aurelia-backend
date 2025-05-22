import logging
import os
# used for file manipulation (copying files)
import shutil
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

    print(f"File saved to: {file_path}")
    # convert to WAV
    wav_path = clean_audio(file_path)

    print(f"Converted to WAV: {wav_path}")
    
    target_language = user["targetLanguage"]

    # transcribe
    transcription = whisper_model.transcribe(wav_path, target_language)
    if not transcription.strip():
        raise ValueError("No speech detected in the audio file.")

    return transcription


def clean_audio(input_path: str) -> str:
    print(f"Cleaning audio file: {input_path}")
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

def transcribe(wav_path: str) -> str:
    print(f"Transcribing audio file: {wav_path}")
    thing = whisper_model.transcribe(wav_path)
    print(f"Transcription result: {thing}")
    return thing
