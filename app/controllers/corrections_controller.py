from fastapi import UploadFile, File
from app.services.database_service import get_user_by_id, upsert_correction, get_corrections_by_user_id 
from app.services.grammar_service import correct_grammar


async def add_new_correction(file: UploadFile = File(...), user_id: str = None):

    user = get_user_by_id(user_id)

    response = correct_grammar(file, user)
    
    correction = upsert_correction(response, user_id)

    return correction
 

def get_corrections(user_id: str):
    return get_corrections_by_user_id(user_id)