import time
from datetime import datetime
import json
import uuid
import nltk
from spacy import load
from ai_models.ollama_client import chat_with_ollama

nltk.download('punkt')
nlp = load("en_core_web_sm")


def correct_grammar(transcription, user, target_language: str = None):

    if not user or "targetLanguage" not in user or "appLanguage" not in user:
        return {
            "success": False,
            "data": None,
            "error": "Invalid user object"
        }

    target_language = target_language or user["targetLanguage"]
    app_language = user["appLanguage"]

    # analyze text
    response = analyze_text(transcription, target_language, app_language)

    if not response.get("sentenceFeedback") or all("error" in feedback for feedback in response["sentenceFeedback"]):
        return {
            "success": False,
            "data": None,
            "error": "Failed to process transcription. No valid feedback was generated."
        }

    # assign ids to sentence and errors
    response["sentenceFeedback"] = assign_ids_to_feedback(
        response["sentenceFeedback"])

    return {
        "success": True,
        "data": response,
        "error": None
    }


def analyze_text(transcription: str, target_language: str, app_language: str):
    if not transcription.strip():
        return {"error": "Transcription is empty"}

    chunks = chunk_sentences(transcription)

    sentence_feedback = []
    for chunk in chunks:
        feedback = ollama_analysis_with_retry(
            chunk, target_language, app_language)

        if "error" in feedback:
            print(f"Error in chunk analysis: {feedback['error']}")
            continue

        # if feedback is a list, extend instead of append to sentence_feedback
        if isinstance(feedback, list):
            sentence_feedback.extend(feedback)
        else:
            sentence_feedback.append(feedback)

    return {
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "originalText": transcription,
        "sentenceFeedback": sentence_feedback
    }


def chunk_sentences(text, max_sentences=5):
    sentences = nltk.sent_tokenize(text)

    chunks = []

    # Loop over sentences, grouping them into chunks of max_sentences
    for i in range(0, len(sentences), max_sentences):
        chunk = sentences[i:i+max_sentences]
        chunks.append(chunk)

    return chunks


def ollama_analysis_with_retry(chunk: list, target_language: str, app_language: str, retries: int = 3, delay: int = 2):
    for attempt in range(retries):
        response = ollama_analysis(chunk, target_language, app_language)
        if "error" not in response:
            return response
        print(f"Retrying Ollama API... Attempt {attempt + 1}/{retries}")
        time.sleep(delay)

    return {
        "error": "Failed to get a valid response from Ollama after multiple attempts.",
        "original": chunk,
        "corrected": None,
        "errors": []
    }


def ollama_analysis(chunk: list, target_language: str, app_language: str):

    if not chunk or not any(sentence.strip() for sentence in chunk):
        return {
            "error": "Chunk is empty or contains only invalid sentences",
            "original": chunk,
            "corrected": None,
            "errors": []
        }
    
    LANGUAGE_MAP = {
            "en": "English",
            "es": "Spanish",
            "fr": "French"
    }

    target_language_full = LANGUAGE_MAP.get(target_language, target_language)
    app_language_full = LANGUAGE_MAP.get(app_language, app_language)
    

    sentence_templates = []
    for sentence in chunk:
        sentence_templates.append({
            "original": sentence.strip(),
            "corrected": "the_corrected_version_of_the_sentence",
            "errors": [
                {
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
    The following transcription is in {target_language_full}. Analyze the transcription and return the results in this structured JSON format:
    {sentence_templates_json}

    For each sentence:
    1. Identify errors and create an `errors` array.
    2. For each error, include:
       - `error`: A description of the error.
       - `reason`: The grammatical reason for the error.
       - `suggestion`: How to fix the error.
       - `improvedClause`: The corrected clause.
    3. Provide the `corrected` sentence with all errors fixed.

    Your explanations should be in {app_language_full}.

    ### Transcription:
    {chunk}
    """

    try:
        response = chat_with_ollama(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", prompt=prompt
        )

        return response
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return {
            "error": "Failed to process transcription due to invalid JSON response from Ollama.",
            "original": chunk,
            "corrected": None,
            "errors": []
        }
    except Exception as e:
        print(f"Ollama API Error: {e}")
        return {
            "error": f"An unexpected error occurred while processing the transcription: {str(e)}",
            "original": chunk,
            "corrected": None,
            "errors": []
        }


def assign_ids_to_feedback(sentence_feedback: list) -> list:
    for sentence in sentence_feedback:
        sentence["id"] = str(uuid.uuid4())

        for error in sentence.get("errors", []):
            error["id"] = str(uuid.uuid4())

    return sentence_feedback
