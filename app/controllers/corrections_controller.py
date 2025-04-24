from app.services.database_service import search_corrections_in_db
from fastapi import HTTPException, UploadFile, File
from app.schemas.reponse_schemas.correction_response_schema import CorrectionResponse
from app.services.audio_processing_service import format_and_transcribe_audio
from app.services.database_service import get_user_by_id, upsert_correction, get_corrections_by_user_id
from app.services.grammar_service import correct_grammar


def add_new_correction(user_id: str, file: UploadFile = File(...)) -> CorrectionResponse:
    try:

        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        transcription = format_and_transcribe_audio(file)

        response = correct_grammar(transcription, user)
        if not response["success"]:
            raise HTTPException(status_code=422, detail=response["error"])

        correction = upsert_correction(response, user_id)
        return correction

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


def get_corrections(user_id: str, page: int, limit: int) -> CorrectionResponse:
    return get_corrections_by_user_id(user_id, page, limit)


def search_corrections(user_id: str, query: str, page: int, limit: int):
    if not query.strip(): 
        return get_corrections_by_user_id(user_id, page, limit)
    
    return search_corrections_in_db(user_id, query, page, limit)
