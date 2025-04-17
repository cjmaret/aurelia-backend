
from ai_models.whisper_model import whisper_model
# handles audio file conversion and manipulation
from pydub import AudioSegment

def format_and_transcribe_audio(file_path):
    # convert to WAV
    wav_path = clean_audio(file_path)

    # transcribe
    return whisper_model.transcribe(wav_path)

def clean_audio(input_path: str) -> str:
    output_path = input_path.replace(".mp3", ".wav").replace(".m4a", ".wav")
    convert_to_wav(input_path, output_path)
    return output_path

# wav is commonly used for audio processing because its uncompressed
def convert_to_wav(input_path: str, output_path: str):
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(
        16000)  # mono, 16khz (standard format)
    audio.export(output_path, format="wav")

def transcribe(wav_path: str) -> str:
    return whisper_model.transcribe(wav_path)
