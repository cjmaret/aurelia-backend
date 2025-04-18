from datetime import datetime
import os
import json
import uuid
import nltk
from spacy import load
# used for file manipulation (copying files)
import shutil
from ai_models.ollama_client import chat_with_ollama
from app.services.transcription_service import format_and_transcribe_audio
from paths import DATA_DIR

nltk.download('punkt')
nlp = load("en_core_web_sm")


def correct_grammar(file, user, target_language: str = None):

    if not user or not hasattr(user, "target_language") or not hasattr(user, "app_language"):
        return {"error": "Invalid user object"}

    file_path = os.path.join(DATA_DIR, file.filename)

    # save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return {"error": f"Failed to save file: {str(e)}"}

    transcription = format_and_transcribe_audio(file_path)

    target_language = target_language or user.target_language
    app_language = user.app_language

    # analyze text
    response = analyze_text(transcription, target_language, app_language)

    return response

# def identify_language(transcription: str) -> str:
#     try:
#         language = detect(transcription)
#         return language
#     except Exception as e:
#         return f"Error identifying language: {e}"


def analyze_text(transcription: str, target_language: str, app_language: str):
    if not transcription.strip():
        return {"error": "Transcription is empty"}

    chunks = chunk_sentences(transcription)

    sentence_feedback = []
    for chunk in chunks:
        feedback = ollama_analysis(chunk, target_language, app_language)
        if "error" in feedback:
            print(f"Error in chunk analysis: {feedback['error']}")
            continue
        sentence_feedback.append(feedback)

    return {
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "originalText": transcription,
        "sentenceFeedback": sentence_feedback
    }


def chunk_sentences(text, max_tokens=200):
    # split sentences at their natural boundaries
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_token_count = 0

    for sentence in sentences:
        token_count = len(sentence.split())
        # if adding current sentences exceeds token count, create a new chunk
        if current_token_count + token_count > max_tokens:
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": " ".join(current_chunk)
            })
            # reset current chunk
            current_chunk = []
            current_token_count = 0

        current_chunk.append(sentence)
        current_token_count += token_count

    # add last chunk if it exists
    if current_chunk:
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": " ".join(current_chunk)
        })

    return chunks


def ollama_analysis(chunk: dict, target_language: str, app_language: str):
    if not chunk.get("text", "").strip():
        return {"error": "Chunk text is empty or invalid"}

    sentences = nltk.sent_tokenize(chunk["text"])
    sentence_id = chunk["id"]

    sentence_templates = []
    for sentence in sentences:
        sentence_templates.append({
            "id": sentence_id,
            "original": sentence.strip(),
            "corrected": "the_corrected_version_of_the_sentence",
            "errors": [
                {
                    "id": str(uuid.uuid4()),
                    "error": "description_of_the_error",
                    "reason": "grammatical_reason_for_the_error",
                    "suggestion": "suggestion_to_fix_the_error",
                    "improvedClause": "the_corrected_version_of_the_clause"
                }
            ]
        })

    # convert to JSON string
    sentence_templates_json = json.dumps(sentence_templates, indent=2)

    # Build the prompt
    prompt = f"""
    The following transcription is in {target_language}. Analyze the transcription and return the results in this structured JSON format:
    {sentence_templates_json}

    For each sentence:
    1. Identify errors and create an `errors` array.
    2. For each error, include:
       - `error`: A description of the error.
       - `reason`: The grammatical reason for the error.
       - `suggestion`: How to fix the error.
       - `improvedClause`: The corrected clause.
    3. Provide the `corrected` sentence with all errors fixed.

    ### Transcription:
    {chunk["text"]}
    """

    try:
        response = chat_with_ollama(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", prompt=prompt)
        return response
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return {"error": "Ollama returned invalid JSON"}
    except Exception as e:
        print(f"Ollama API Error: {e}")
        return {"error": f"Ollama API error: {str(e)}"}
