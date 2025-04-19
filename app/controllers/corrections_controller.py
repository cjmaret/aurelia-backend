from fastapi import UploadFile, File
from app.schemas.reponse_schemas.correction_response_schema import CorrectionResponse
from app.services.database_service import get_user_by_id, upsert_correction, get_corrections_by_user_id
from app.services.grammar_service import correct_grammar


def add_new_correction(user_id: str, file: UploadFile = File(...)) -> CorrectionResponse:

    user = get_user_by_id(user_id)

    if not user:
        return CorrectionResponse(success=False, data=None, error="User not found")

    response = correct_grammar(file, user)

    if not response["success"]:
        return CorrectionResponse(success=False, data=None, error=response["error"])

    correction = upsert_correction(response, user_id)

    return correction

def get_corrections(user_id: str) -> CorrectionResponse:
    return get_corrections_by_user_id(user_id)
