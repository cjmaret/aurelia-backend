from fastapi import APIRouter, Depends, UploadFile, File
from app.controllers.conversations_controller import add_new_conversation, delete_conversation, delete_correction, get_conversations, search_conversations
from app.schemas.reponse_schemas.conversation_response_schema import ConversationResponse
from app.utils.auth_utils import get_current_user_from_token

router = APIRouter()


@router.post("/api/v1/conversations", response_model=ConversationResponse)
def add_conversation_route(file: UploadFile = File(...), user_id: str = Depends(get_current_user_from_token)):
    return add_new_conversation(user_id, file)


@router.get("/api/v1/conversations", response_model=ConversationResponse)
def fetch_conversations_route(
    user_id: str = Depends(get_current_user_from_token),
    page: int = 1,
    limit: int = 10
):
    return get_conversations(user_id, page, limit)


@router.get("/api/v1/conversations/search", response_model=ConversationResponse)
def search_conversations_route(
    query: str,
    user_id: str = Depends(get_current_user_from_token),
    page: int = 1,
    limit: int = 10
):
    return search_conversations(user_id, query, page, limit)


@router.delete("/api/v1/conversations/{conversation_id}")
def delete_conversation_route(conversation_id: str, user_id: str = Depends(get_current_user_from_token)):
    return delete_conversation(conversation_id, user_id)


@router.delete("/api/v1/conversations/{conversation_id}/corrections/{correction_id}")
def delete_correction_route(conversation_id: str, correction_id: str, user_id: str = Depends(get_current_user_from_token)):
    return delete_correction(conversation_id, correction_id, user_id)
