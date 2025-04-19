from fastapi import HTTPException, UploadFile, File
from app.schemas.reponse_schemas.correction_response_schema import CorrectionResponse
from app.services.database_service import get_user_by_id, upsert_correction, get_corrections_by_user_id
from app.services.grammar_service import correct_grammar


def add_new_correction(user_id: str, file: UploadFile = File(...)) -> CorrectionResponse:
    try:

        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        response = correct_grammar(file, user)
        if not response["success"]:
            raise HTTPException(status_code=422, detail=response["error"])

        correction = upsert_correction(response, user_id)
        return correction

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


def get_corrections(user_id: str) -> CorrectionResponse:
    return get_corrections_by_user_id(user_id)
