import traceback
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
from pydub import AudioSegment
import soundfile as sf
import audioread
import wave



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
logger.setLevel(logging.INFO)


def convert_to_wav(input_path: str, output_path: str):
    try:
        logger.info(
            f"Starting conversion: input_path={input_path}, output_path={output_path}")

        # Check if the input file exists
        if not os.path.exists(input_path):
            logger.error(f"Input file does not exist: {input_path}")
            raise FileNotFoundError(f"Input file does not exist: {input_path}")
        logger.info(f"Input file exists: {input_path}")

        # Open the input .m4a file using audioread
        with audioread.audio_open(input_path) as infile:
            samplerate = infile.samplerate
            channels = infile.channels
            logger.info(
                f"Audio properties: samplerate={samplerate}, channels={channels}")

            # Read all audio frames
            frames = b''.join(infile.read_data())
            logger.info(
                f"Successfully read audio frames. Total frame size: {len(frames)} bytes")

        # Convert frames to numpy array
        logger.info("Converting audio frames to numpy array...")
        data = np.frombuffer(frames, dtype=np.int16)
        logger.info(
            f"Audio data converted to numpy array. Data length: {len(data)}")

        # Resample to 16kHz if necessary
        if samplerate != 16000:
            logger.info(f"Resampling audio from {samplerate}Hz to 16000Hz...")
            num_samples = int(len(data) * 16000 / samplerate)
            data = resample(data, num_samples).astype(np.int16)
            logger.info(f"Resampling complete. New data length: {len(data)}")
        else:
            logger.info("No resampling needed. Audio is already at 16000Hz.")

        # Convert to mono if necessary
        if channels > 1:
            logger.info(
                f"Converting audio to mono. Original channels: {channels}")
            # Ensure the array length is divisible by the number of channels
            truncated_length = len(data) - (len(data) % channels)
            # Truncate to nearest multiple of channels
            data = data[:truncated_length]
            data = data.reshape(-1, channels).mean(axis=1).astype(np.int16)
            logger.info("Audio successfully converted to mono.")
        else:
            logger.info("Audio is already mono. No conversion needed.")

        # Write the output WAV file
        logger.info(f"Writing the output WAV file to: {output_path}")
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit PCM
            wav_file.setframerate(16000)  # 16kHz sample rate
            wav_file.writeframes(data.tobytes())
        logger.info(f"Audio successfully written to WAV file: {output_path}")

    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError: {e}")
        raise
    except audioread.DecodeError as e:
        logger.error(
            f"DecodeError: {e}. The input file format may not be supported.")
        raise RuntimeError(f"Failed to decode audio: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in convert_to_wav: {e}")
        # Log the full traceback for debugging
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to convert audio: {e}")
    

def transcribe(wav_path: str) -> str:
    return whisper_model.transcribe(wav_path)
