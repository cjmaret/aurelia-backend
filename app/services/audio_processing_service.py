import logging
import os
# handles audio file conversion and manipulation
import numpy as np
from scipy.signal import resample
import audioread
# used for file manipulation (copying files)
import shutil
from app.mongo.schemas.db_user_schema import DbUserSchema
from paths import DATA_DIR
import soundfile as sf


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


logger = logging.getLogger(__name__)

def convert_to_wav(input_path: str, output_path: str):
    try:
        logger.info(
            f"Converting audio: input_path={input_path}, output_path={output_path}")
        
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file does not exist: {input_path}")
        logger.info(f"Input file exists: {input_path}")

        # Use audioread to decode the input audio file
        with audioread.audio_open(input_path) as infile:
            samplerate = infile.samplerate
            channels = infile.channels
            logger.info(
                f"Audio properties: samplerate={samplerate}, channels={channels}")
            frames = b''.join(infile.read_data())

        # Convert frames to numpy array
        data = np.frombuffer(frames, dtype=np.int16)
        logger.info(f"Audio data length: {len(data)}")

        # Resample to 16kHz if necessary
        if samplerate != 16000:
            num_samples = int(len(data) * 16000 / samplerate)
            logger.info(
                f"Resampling audio: original_samples={len(data)}, target_samples={num_samples}")
            data = resample(data, num_samples).astype(np.int16)

        # Convert to mono if necessary
        if channels > 1:
            logger.info("Converting audio to mono")
            data = data[:len(data) - (len(data) % channels)]
            data = data.reshape(-1, channels).mean(axis=1).astype(np.int16)

        # Write the output WAV file
        sf.write(output_path, data, 16000, format='WAV', subtype='PCM_16')
        logger.info(f"Audio successfully converted to WAV: {output_path}")
        print(f"Audio successfully converted to WAV: {output_path}")
    except Exception as e:
        logger.error(f"Error in convert_to_wav: {e}")
        raise RuntimeError(f"Failed to convert audio: {e}")


def transcribe(wav_path: str) -> str:
    return whisper_model.transcribe(wav_path)
