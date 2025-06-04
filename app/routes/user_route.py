from fastapi import APIRouter, Depends
from app.controllers.user_controller import get_user_details, request_email_change, update_user_details
from app.schemas.request_schemas.change_email_request_schema import ChangeEmailRequestSchema
from app.schemas.request_schemas.request_email_change_request_schema import RequestEmailChangeRequestSchema
from app.schemas.request_schemas.user_details_request_schema import UserDetailsRequestSchema
from app.utils.auth_utils import get_current_user_from_token
from app.controllers.user_controller import change_user_email


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

@router.post("/api/v1/user/request-email-change")
def request_email_change_route(
    request: RequestEmailChangeRequestSchema,
    user_id: str = Depends(get_current_user_from_token)
):
    return request_email_change(user_id, request.newEmail)


@router.post("/api/v1/user/change-email")
def change_email_route(request: ChangeEmailRequestSchema):
    print("request", request)
    return change_user_email(request.token, request.password)
