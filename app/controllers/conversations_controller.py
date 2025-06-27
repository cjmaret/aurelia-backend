from app.services.database_service import delete_correction_from_conversation, get_conversation_by_user_id
import logging
from app.services.database_service import delete_conversation_by_id, search_conversations_in_db
from fastapi import HTTPException, UploadFile, File
from app.schemas.reponse_schemas.conversation_response_schema import ConversationResponse
from app.services.audio_processing_service import format_and_transcribe_audio
from app.services.database_service import get_user_by_id, upsert_conversation, get_conversations_by_user_id
from app.services.grammar_service import correct_grammar

logger = logging.getLogger(__name__)


def add_new_conversation(user_id: str, file: UploadFile = File(...)) -> ConversationResponse:
    try:
        logger.info(f"Starting add_new_conversation for user_id: {user_id}")

        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info("User found, starting transcription")
        transcription = format_and_transcribe_audio(file, user)

        print(f"Transcription result: {transcription}")

        logger.info("Transcription completed, starting grammar correction")
        response = correct_grammar(transcription, user)
        if not response["success"]:
            logger.error(f"Grammar correction failed: {response['error']}")
            raise HTTPException(status_code=422, detail=response["error"])

        logger.info("Grammar correction successful, upserting conversation")
        conversation = upsert_conversation(response, user_id)
        logger.info("Conversation upserted successfully")
        return conversation

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


def get_conversations(user_id: str, page: int, limit: int) -> ConversationResponse:
    return get_conversations_by_user_id(user_id, page, limit)


def search_conversations(user_id: str, query: str, page: int, limit: int):
    if not query.strip():
        return get_conversations_by_user_id(user_id, page, limit)

    return search_conversations_in_db(user_id, query, page, limit)


def delete_conversation(conversation_id: str, user_id: str):
    conversation = get_conversation_by_user_id(user_id, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this conversation")

    success = delete_conversation_by_id(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True, "message": "Conversation deleted successfully"}


def delete_correction(conversation_id: str, correction_id: str, user_id: str, ):
    conversation = get_conversation_by_user_id(user_id, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this conversation")

    success = delete_correction_from_conversation(
        conversation_id, correction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Correction not found")
    return {"success": True, "message": "Correction deleted successfully"}
