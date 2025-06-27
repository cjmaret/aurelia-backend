from datetime import datetime, timedelta
from typing import Optional
import uuid
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from app.mongo.MongoClient import get_mongo_client
from app.mongo.schemas.db_conversation_schema import DbConversation
from app.mongo.schemas.db_user_schema import DbUserSchema
from app.schemas.reponse_schemas.conversation_response_schema import ConversationData, ConversationResponse
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


def get_user_by_email(user_email: str) -> DbUserSchema | None:
    users_collection = get_collection("users")
    normalized_email = user_email.strip().lower()
    return users_collection.find_one({"userEmail": normalized_email})


def create_user(
        user_email: str = None,
        hashed_password: str = None,
        email_verified: bool = False,
        oauth_provider: str = None,
        oauth_user_id: str = None,
        is_anonymous: bool = False,
        anon_user_secret: str = None,
) -> None:
    users_collection = get_collection("users")
    user_id = str(uuid.uuid4())
    new_user = DbUserSchema(
        userId=user_id,
        userEmail=user_email.strip().lower() if user_email else None,
        emailVerified=email_verified,
        username="New User",
        targetLanguage="en",
        appLanguage="en",
        createdAt=datetime.utcnow(),
        setupComplete=False,
        password=hashed_password,
        oauthProvider=oauth_provider,
        oauthUserId=oauth_user_id,
        isAnonymous=is_anonymous,
        anonUserSecret=anon_user_secret
    )
    users_collection.insert_one(new_user.dict())
    return user_id


def delete_user_by_id(user_id: str) -> bool:
    users_collection = get_collection("users")
    result = users_collection.delete_one({"userId": user_id})
    return result.deleted_count > 0


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


def update_user_password_in_db(user_id: str, hashed_password: str):
    users_collection = get_collection("users")

    result = users_collection.update_one(
        {"userId": user_id},
        {"$set": {"password": hashed_password}}
    )
    return result


def get_conversations_by_user_id(user_id: str, page: int, limit: int) -> ConversationResponse:
    try:
        conversations_collection = get_collection("conversations")

        # num of documents to skip
        skip = (page - 1) * limit

        # fetch with pagination
        conversations_cursor = conversations_collection.find(
            {"userId": user_id}, {"_id": 0}
        ).sort("createdAt", -1).skip(skip).limit(limit)

        # convert cursor to list
        conversations = list(conversations_cursor)

        total_conversations = conversations_collection.count_documents(
            {"userId": user_id})

        return ConversationResponse(
            success=True,
            data={
                "conversations": conversations,
                "total": total_conversations,
                "page": page,
                "limit": limit
            },
            error=None
        )
    except Exception as e:
        return ConversationResponse(
            success=False,
            data=None,
            error=f"An error occurred while fetching conversations: {str(e)}"
        )
    
def get_conversation_by_user_id(user_id: str, conversation_id: str) -> dict | None:
    conversations_collection = get_collection("conversations")
    return conversations_collection.find_one({
        "userId": user_id,
        "conversationId": conversation_id
    }, {"_id": 0})

def upsert_conversation(response: dict, user_id) -> ConversationResponse:
    if not response.get("success") or "data" not in response or not response["data"]:
        return ConversationResponse(
            success=False,
            data=None,
            error="Invalid response object. Missing required fields"
        )

    data = response["data"]

    conversations_collection = get_collection("conversations")

    data["userId"] = user_id
    created_at_datetime = datetime.strptime(
        data["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")

    # check if a recent conversation exists in the db
    existing_data = check_for_recent_conversation(
        user_id, conversations_collection, created_at_datetime)

    if existing_data:
        if existing_data["userId"] != user_id:
            raise HTTPException(
                status_code=403, detail="You do not have permission to modify this conversation.")

        print(f"Existing conversation found. Merging conversation.")
        return merge_conversation(conversations_collection, existing_data, created_at_datetime, data)
    else:
        print(
            f"Existing conversation not found. Creating new conversation.")
        return create_new_conversation(conversations_collection, created_at_datetime, data)


def create_new_conversation(collection, created_at_datetime: datetime, data: ConversationData) -> ConversationResponse:
    # check and use only if valid feedback
    valid_feedback = [
        feedback for feedback in data["sentenceFeedback"]
        if "id" in feedback and "original" in feedback and "corrected" in feedback and "errors" in feedback
    ]

    new_conversation = DbConversation(
        userId=data["userId"],
        conversationId=str(uuid.uuid4()),
        createdAt=created_at_datetime,
        originalText=data["originalText"],
        sentenceFeedback=valid_feedback,
    )

    collection.insert_one(new_conversation.dict(by_alias=True))

    return ConversationResponse(
        success=True,
        data=[ConversationData(
            conversationId=new_conversation.conversationId,
            createdAt=new_conversation.createdAt,
            originalText=new_conversation.originalText,
            sentenceFeedback=valid_feedback
        )],
        error=None
    )


def merge_conversation(collection, existing_data: dict, created_at_datetime: datetime, data: ConversationData) -> ConversationResponse:

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

    return ConversationResponse(
        success=True,
        data=[ConversationData(
            conversationId=existing_data["conversationId"],
            createdAt=existing_data["createdAt"],
            originalText=existing_data["originalText"],
            sentenceFeedback=existing_data["sentenceFeedback"],
        )],
        error=None
    )


def check_for_recent_conversation(user_id: str, collection, created_at_datetime: datetime) -> Optional[DbConversation]:

    # find most recent conversation
    most_recent_conversation = (
        collection
        .find({"userId": user_id})
        .sort("createdAt", -1)  # descending order
        .limit(1)
    )

    most_recent_conversation = next(most_recent_conversation, None)

    if most_recent_conversation:
        time_diff = created_at_datetime - most_recent_conversation["createdAt"]

        if time_diff < timedelta(minutes=.5):
            return most_recent_conversation

    return None


def search_conversations_in_db(user_id: str, query: str, page: int, limit: int) -> ConversationResponse:
    try:
        conversations_collection = get_collection("conversations")

        skip = (page - 1) * limit

        # text search
        conversations_cursor = conversations_collection.find(
            {
                "userId": user_id,
                "$text": {"$search": query}
            },
            {"_id": 0}
        ).sort("createdAt", -1).skip(skip).limit(limit)

        conversations = list(conversations_cursor)

        total_conversations = conversations_collection.count_documents(
            {
                "userId": user_id,
                "$text": {"$search": query}
            }
        )

        return ConversationResponse(
            success=True,
            data={
                "conversations": conversations,
                "total": total_conversations,
                "page": page,
                "limit": limit
            },
            error=None
        )
    except Exception as e:
        return ConversationResponse(
            success=False,
            data=None,
            error=f"An error occurred while searching conversations: {str(e)}"
        )


def delete_conversation_by_id(conversation_id: str) -> bool:
    conversations_collection = get_collection("conversations")
    result = conversations_collection.delete_one(
        {"conversationId": conversation_id})
    return result.deleted_count > 0


def delete_correction_from_conversation(conversation_id: str, correction_id: str) -> bool:
    conversations_collection = get_collection("conversations")
    result = conversations_collection.update_one(
        {"conversationId": conversation_id},
        {"$pull": {"sentenceFeedback": {"id": correction_id}}}
    )
    return result.modified_count > 0

def delete_all_conversations_by_user_id(user_id: str) -> int:
    conversations_collection = get_collection("conversations")
    result = conversations_collection.delete_many({"userId": user_id})
    return result.deleted_count


def add_verification_code(user_id: str, code: str, expires_at: datetime, purpose: str, email: str = None):
    codes_collection = get_collection("verificationCodes")

    # delete any existing codes for this user and purpose
    codes_collection.delete_many({"userId": user_id, "purpose": purpose})

    codes_collection.insert_one({
        "userId": user_id,
        "code": code,
        "email": email,
        "expiresAt": expires_at,
        "purpose": purpose,
        "createdAt": datetime.utcnow()
    })


def get_verification_code(user_id: str, purpose: str):
    codes_collection = get_collection("verificationCodes")
    return codes_collection.find_one({"userId": user_id, "purpose": purpose})
