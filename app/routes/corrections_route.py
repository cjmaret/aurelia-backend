from typing import List, Union
from fastapi import APIRouter, Depends, UploadFile, File
from app.controllers.corrections_controller import add_new_correction, delete_correction, get_corrections, search_corrections
from app.schemas.reponse_schemas.correction_response_schema import CorrectionResponse
from app.utils.auth_utils import get_current_user_from_token

router = APIRouter()


@router.post("/api/v1/corrections", response_model=CorrectionResponse)
def add_correction_route(file: UploadFile = File(...), user_id: str = Depends(get_current_user_from_token)):
    return add_new_correction(user_id, file)


@router.get("/api/v1/corrections", response_model=CorrectionResponse)
def fetch_corrections_route(
    user_id: str = Depends(get_current_user_from_token),
    page: int = 1,
    limit: int = 10
):
    return get_corrections(user_id, page, limit)


@router.get("/api/v1/corrections/search", response_model=CorrectionResponse)
def search_corrections_route(
    query: str,
    user_id: str = Depends(get_current_user_from_token),
    page: int = 1,
    limit: int = 10
):
    return search_corrections(user_id, query, page, limit)


@router.delete("/api/v1/corrections/{conversationId}")
def delete_correction_route(conversationId: str):
    return delete_correction(conversationId)
