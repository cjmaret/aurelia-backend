import logging
from app.services.database_service import delete_correction_by_id, search_corrections_in_db
from fastapi import HTTPException, UploadFile, File
from app.schemas.reponse_schemas.correction_response_schema import CorrectionResponse
from app.services.audio_processing_service import format_and_transcribe_audio
from app.services.database_service import get_user_by_id, upsert_correction, get_corrections_by_user_id
from app.services.grammar_service import correct_grammar

logger = logging.getLogger(__name__)

def add_new_correction(user_id: str, file: UploadFile = File(...)) -> CorrectionResponse:
    try:
        logger.info(f"Starting add_new_correction for user_id: {user_id}")
        
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info("User found, starting transcription")
        transcription = format_and_transcribe_audio(file, user)

        logger.info("Transcription completed, starting grammar correction")
        response = correct_grammar(transcription, user)
        if not response["success"]:
            logger.error(f"Grammar correction failed: {response['error']}")
            raise HTTPException(status_code=422, detail=response["error"])

        logger.info("Grammar correction successful, upserting correction")
        correction = upsert_correction(response, user_id)
        logger.info("Correction upserted successfully")
        return correction

    except ValueError as e:
        logger.error(f"ValueError: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


def get_corrections(user_id: str, page: int, limit: int) -> CorrectionResponse:
    return get_corrections_by_user_id(user_id, page, limit)


def search_corrections(user_id: str, query: str, page: int, limit: int):
    if not query.strip(): 
        return get_corrections_by_user_id(user_id, page, limit)
    
    return search_corrections_in_db(user_id, query, page, limit)


def delete_correction(conversationId: str):
    success = delete_correction_by_id(conversationId)
    if not success:
        raise HTTPException(status_code=404, detail="Correction not found")
    return {"success": True, "message": "Correction deleted successfully"}
