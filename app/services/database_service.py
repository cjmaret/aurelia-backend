from datetime import datetime, timedelta
from typing import List, Optional
import uuid
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from app.mongo.MongoClient import get_mongo_client
from app.mongo.schemas.db_correction_schema import DbCorrection
from app.mongo.schemas.db_user_schema import DbUserSchema
from app.schemas.request_schemas.user_details_request_schema import UserDetailsRequestSchema


def get_collection(collection: str):
    client = get_mongo_client()
    db = client["conversant-ai"]
    return db[collection]


def store_refresh_token(user_id: str, refresh_token: str):
    users_collection = get_collection("users")
    users_collection.update_one(
        {"userId": user_id},
        {"$set": {"refreshToken": refresh_token}}
    )

def invalidate_refresh_token(user_id: str):
    users_collection = get_collection("users")
    users_collection.update_one(
        {"userId": user_id},
        {"$unset": {"refreshToken": ""}}
)

def get_user_by_refresh_token(refresh_token: str):
    users_collection = get_collection("users")
    return users_collection.find_one({"refreshToken": refresh_token})

def get_user_by_email(userEmail: str) -> DbUserSchema | None: 
    users_collection = get_collection("users")

    return users_collection.find_one({"userEmail": userEmail})


def create_user(userEmail: str, hashed_password: str) -> None:
    users_collection = get_collection("users")
    new_user = DbUserSchema(
        userId=str(uuid.uuid4()),
        userEmail=userEmail,
        username="New User",
        targetLanguage="English",
        appLanguage="English",
        createdAt=datetime.utcnow(),
        password=hashed_password,
    )
    users_collection.insert_one(new_user.dict())


def get_user_by_id(user_id: str) -> DbUserSchema | None:
    users_collection = get_collection("users")
    return users_collection.find_one({"userId": user_id})


def update_user_details_in_db(user_id: str, userDetails: UserDetailsRequestSchema) -> bool:
    users_collection = get_collection("users")
    update_data = {key: value for key,
                   value in userDetails.items() if value is not None}
    result = users_collection.update_one(
        {"userId": user_id}, {"$set": update_data}
    )
    return result.modified_count > 0


def get_corrections_by_user_id(user_id: str) -> List[DbCorrection]:
    corrections_collection = get_collection("corrections")

    # exclude internal id
    all_corrections_cursor = corrections_collection.find({"userId": user_id}, {"_id": 0})

    # convert the cursor to a list of dictionaries
    all_corrections = list(all_corrections_cursor)

    return all_corrections

def upsert_correction(response: dict, user_id) -> DbCorrection:

    response["userId"] = user_id

    corrections_collection = get_collection("corrections")
    created_at_datetime = datetime.strptime(
        response["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
    
    # check if a recent correction exists in the db
    existing_data = check_for_recent_correction(user_id,
        corrections_collection, created_at_datetime)

    if existing_data:
        if existing_data["userId"] != user_id:
            raise HTTPException(status_code=403, detail="You do not have permission to modify this correction.")
        
        print(f"Existing data found. Merging data.")
        return merge_correction(corrections_collection, existing_data, created_at_datetime, response)
    else:
        print(
            f"Existing correction not found. Creating new correction.")
        return create_new_correction(corrections_collection, created_at_datetime, response)

def create_new_correction(collection, created_at_datetime: datetime, response: dict) -> DbCorrection:
    new_correction = DbCorrection(
        conversationId=str(uuid.uuid4()),
        createdAt=created_at_datetime,
        originalText=response["originalText"],
        sentenceFeedback=response["sentenceFeedback"],
    )

    collection.insert_one(new_correction.dict(by_alias=True))
    return new_correction

def merge_correction(collection, existing_data: dict, created_at_datetime: datetime, response: dict) -> DbCorrection:
    if not existing_data:
        raise KeyError(
            f"Existing data not found in the database.")


    existing_data["originalText"] += " " + response["originalText"]
    existing_data["sentenceFeedback"].extend(response["sentenceFeedback"])
    existing_data["createdAt"] = created_at_datetime

    collection.update_one(
        {"conversationId": existing_data["conversationId"]},
        {"$set": existing_data}
    )
    
    # convert internal id to string for json serialization
    if "_id" in existing_data:
        existing_data["_id"] = str(existing_data["_id"])

    # return updated document in a JSON-serializable format
    return jsonable_encoder(existing_data)


def check_for_recent_correction(user_id: str, collection, created_at_datetime: datetime) -> Optional[DbCorrection]:
    # find most recent correction
    most_recent_correction = (
        collection
        .find({"user_id": user_id})
        .sort("createdAt", -1)  # descending order
        .limit(1)
    )

    most_recent_correction = next(most_recent_correction, None)

    if most_recent_correction:
        time_diff = created_at_datetime - most_recent_correction["createdAt"]
        print('time_diff', time_diff)
        if time_diff < timedelta(minutes=5):
            return most_recent_correction

    return None


# def get_correction_by_conversation_id(db: Dict[str, dict], conversation_id: str):
#     return db.query(DbCorrection).filter(DbCorrection.conversation_id == conversation_id).first()
