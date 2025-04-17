from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from app.controllers.corrections_controller import add_new_correction, get_corrections
from app.schemas.reponse_schemas.correction_response_schema import CorrectionResponse
from app.utils.auth_utils import get_current_user_from_token

router = APIRouter()


@router.post("/api/v1/corrections", response_model=CorrectionResponse)
async def add_correction(file: UploadFile = File(...), user_id: str = Depends(get_current_user_from_token)):
    return await add_new_correction(file, user_id)


@router.get("/api/v1/corrections", response_model=List[CorrectionResponse])
def fetch_corrections(user_id: str = Depends(get_current_user_from_token)):
    return get_corrections(user_id)
