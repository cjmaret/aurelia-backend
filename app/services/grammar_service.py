from datetime import datetime
import os
import json
import uuid
import nltk
from spacy import load
import ollama
from langdetect import detect
# used for file manipulation (copying files)
import shutil
from ai_models.ollama_client import chat_with_ollama
from app.services.transcription_service import format_and_transcribe_audio
from paths import DATA_DIR

nltk.download('punkt')
nlp = load("en_core_web_sm")


def correct_grammar(file, user, target_language: str):
    file_path = os.path.join(DATA_DIR, file.filename)

    # save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    transcription = format_and_transcribe_audio(file_path);

    # analyze text
    response = analyze_text(transcription, target_language, user.app_language)

    return response

# def identify_language(transcription: str) -> str:
#     try:
#         language = detect(transcription)
#         return language
#     except Exception as e:
#         return f"Error identifying language: {e}"


def analyze_text(transcription: str, target_language: str, app_language: str):
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


def chunk_sentences(text, max_sentences=5):
    sentences = nltk.sent_tokenize(text)
    chunks = []

    # Loop over sentences, grouping them into chunks of max_sentences
    for i in range(0, len(sentences), max_sentences):
        chunk = sentences[i:i+max_sentences]
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": " ".join(chunk)
        })

    return chunks


def ollama_analysis(chunk: dict, target_language: str, app_language: str):
    #TODO: different prompts based on app_language
    
    sentences = chunk["text"].split(". ")

    print('sentences', sentences)

    sentence_id = chunk["id"]

    # if the unique Id doesnt work can just add it in in analyze_text
    sentence_templates = ""
    for sentence in sentences:
        sentence_templates += f"""
      {{
        "id": {sentence_id},
        "original": {sentence.strip()},
        "corrected": the_corrected_version_of_the_sentence",
        "errors": [
          {{
              "id": {str(uuid.uuid4())}
              "error": "description_of_the_error",
              "reason": "grammatical_reason_for_the_error",
              "suggestion": "suggestion_to_fix_the_error",
              "improvedClause": "the_corrected_version_of_the_clause"
            }}
        ],
      }},
      """

    sentence_templates = sentence_templates.strip().rstrip(",")

    prompt = f"""
    The following transcription is in {target_language}. Please process the transcription and return the analysis in this structured format:
        {sentence_templates}
    
    For each sentence in the transcription, please:
    1. If an error exists, create an error object with a description of the `error`.
    2. For each error object, provide the following data based on the error:
      1. `error`: what the error is
      2. `reason` a grammatical reason for the error
      3. `suggestion`: instructions of how to fix the error, based on the `improvedClause` of the same error object
      4. `improvedClause`: the clause of the sentence with the error corrected
    3. Provide the `correctedSentence` with all identified errors fixed.
    4. If a single error has multiple possible correction, keep error as a single error in errorCount, and provide corrections as separate objects with the same errorIndex

    
    ### Transcription:
    {chunk["text"]}
    """

    try:
        response = chat_with_ollama(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", prompt=prompt)

        return response
    except json.JSONDecodeError:
        return {"error": "Ollama returned invalid JSON"}
    except Exception as e:
        return {"error": f"Ollama API error: {str(e)}"}

