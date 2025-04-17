from fastapi import UploadFile, File
from app.services.database_service import upsert_correction, get_corrections_by_user_id 
from app.services.grammar_service import correct_grammar



#TODO user_id should be passed in the request body
async def add_new_correction(file: UploadFile = File(...), user_id: str = None):

    response = correct_grammar(file)
    
    correction = upsert_correction(response, user_id)

    return correction
 

def get_corrections(user_id: str):
    return get_corrections_by_user_id(user_id)