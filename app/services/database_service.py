from datetime import datetime, timedelta
from typing import List, Optional
import uuid
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from app.mongo.MongoClient import get_mongo_client
from app.mongo.schemas.db_correction_schema import DbCorrection
from app.mongo.schemas.db_user_schema import DbUserSchema
from app.schemas.reponse_schemas.correction_response_schema import CorrectionData, CorrectionResponse
from app.schemas.request_schemas.user_details_request_schema import UserDetailsRequestSchema


def get_collection(collection: str):
    client = get_mongo_client()
    db = client["conversant-ai"]
    return db[collection]


def store_refresh_token(user_id: str, refresh_token: str):
    users_collection = get_collection("users")
    result = users_collection.update_one(
        {"userId": user_id},
        {"$set": {"refreshToken": refresh_token}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")


def invalidate_refresh_token(user_id: str):
    users_collection = get_collection("users")
    result = users_collection.update_one(
        {"userId": user_id},
        {"$unset": {"refreshToken": ""}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")


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


def get_corrections_by_user_id(user_id: str) -> CorrectionResponse:
    try:
        corrections_collection = get_collection("corrections")

        # exclude internal id from response
        all_corrections_cursor = corrections_collection.find(
            {"userId": user_id}, {"_id": 0})

        # convert the cursor to a list of dictionaries
        all_corrections = list(all_corrections_cursor)

        return CorrectionResponse(
            success=True,
            data=all_corrections,
            error=None
        )
    except Exception as e:
        return CorrectionResponse(
            success=False,
            data=None,
            error=f"An error occurred while fetching corrections: {str(e)}"
        )


def upsert_correction(response: dict, user_id) -> CorrectionResponse:

    if not response.get("success") or "data" not in response or not response["data"]:
        return CorrectionResponse(
            success=False,
            data=None,
            error="Invalid response object. Missing required fields"
        )

    data = response["data"]

    corrections_collection = get_collection("corrections")

    data["userId"] = user_id
    created_at_datetime = datetime.strptime(
        data["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")

    # check if a recent correction exists in the db
    existing_data = check_for_recent_correction(
        user_id, corrections_collection, created_at_datetime)

    if existing_data:
        if existing_data["userId"] != user_id:
            raise HTTPException(
                status_code=403, detail="You do not have permission to modify this correction.")

        print(f"Existing data found. Merging data.")
        return merge_correction(corrections_collection, existing_data, created_at_datetime, data)
    else:
        print(
            f"Existing correction not found. Creating new correction.")
        return create_new_correction(corrections_collection, created_at_datetime, data)


def create_new_correction(collection, created_at_datetime: datetime, data: CorrectionData) -> CorrectionResponse:
    # check and use only if valid feedback
    valid_feedback = [
        feedback for feedback in data["sentenceFeedback"]
        if "id" in feedback and "original" in feedback and "corrected" in feedback and "errors" in feedback
    ]

    new_correction = DbCorrection(
        userId=data["userId"],
        conversationId=str(uuid.uuid4()),
        createdAt=created_at_datetime,
        originalText=data["originalText"],
        sentenceFeedback=valid_feedback,
    )

    collection.insert_one(new_correction.dict(by_alias=True))

    return CorrectionResponse(
        success=True,
        data=[CorrectionData(
            conversationId=new_correction.conversationId,
            createdAt=new_correction.createdAt,
            originalText=new_correction.originalText,
            sentenceFeedback=valid_feedback
        )],
        error=None
    )


def merge_correction(collection, existing_data: dict, created_at_datetime: datetime, data: CorrectionData) -> CorrectionResponse:

    if not existing_data:
        return {"success": False, "data": None, "error": "Existing data not found in the database."}

    existing_data["originalText"] += " " + data["originalText"]
    existing_data["sentenceFeedback"].extend(data["sentenceFeedback"])
    existing_data["createdAt"] = created_at_datetime

    collection.update_one(
        {"conversationId": existing_data["conversationId"]},
        {"$set": existing_data}
    )

    # convert internal id to string for json serialization
    if "_id" in existing_data:
        existing_data["_id"] = str(existing_data["_id"])

    return CorrectionResponse(
        success=True,
        data=[CorrectionData(
            conversationId=existing_data["conversationId"],
            createdAt=existing_data["createdAt"],
            originalText=existing_data["originalText"],
            sentenceFeedback=existing_data["sentenceFeedback"],
        )],
        error=None
    )


def check_for_recent_correction(user_id: str, collection, created_at_datetime: datetime) -> Optional[DbCorrection]:

    # find most recent correction
    most_recent_correction = (
        collection
        .find({"userId": user_id})
        .sort("createdAt", -1)  # descending order
        .limit(1)
    )

    most_recent_correction = next(most_recent_correction, None)

    if most_recent_correction:
        time_diff = created_at_datetime - most_recent_correction["createdAt"]

        if time_diff < timedelta(minutes=5):
            return most_recent_correction

    return None
