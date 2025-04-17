from fastapi import APIRouter, Depends
from app.controllers.user_controller import get_user_details, update_user_details
from app.schemas.request_schemas.user_details_request_schema import UserDetailsRequestSchema
from app.utils.auth_utils import get_current_user_from_token

router = APIRouter()


@router.get("/api/v1/user/details")
def get_user_details_route(user_id: str = Depends(get_current_user_from_token)):
    return get_user_details(user_id)


@router.patch("/api/v1/user/details")
def update_user_details_route(
    userDetails: UserDetailsRequestSchema,
    user_id: str = Depends(get_current_user_from_token)
):
    return update_user_details(user_id, userDetails)
