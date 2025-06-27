import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app import app  # Import your FastAPI app
from app.services.database_service import get_collection


# THIS FILE IS A PLACEHOLDER FOR TESTING CONVERSATIONS, DEMO OF PYTHON TEST FILE STRUCTURE

client = TestClient(app)

conversations_collection = get_collection("conversations")


USER_A_TOKEN = "user_a_token"
USER_B_TOKEN = "user_b_token"

USER_A_ID = "user_a"
USER_B_ID = "user_b"

def mock_decode_token(token: str):
    if token == USER_A_TOKEN:
        return USER_A_ID
    elif token == USER_B_TOKEN:
        return USER_B_ID
    return None

@pytest.fixture(autouse=True)
def patch_decode_token(monkeypatch):
    from app.utils.auth_utils import decode_token
    monkeypatch.setattr(decode_token, "__call__", mock_decode_token)

def create_correction(file_content: str, token: str):
    response = client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", file_content)},
    )
    return response

def test_user_owns_correction():
    response_1 = create_correction("This is the first file.", USER_A_TOKEN)
    assert response_1.status_code == 200
    correction_1 = response_1.json()
    assert correction_1["userId"] == USER_A_ID

    response_2 = create_correction("This is the second file.", USER_A_TOKEN)
    assert response_2.status_code == 200
    correction_2 = response_2.json()

    assert correction_1["conversationId"] == correction_2["conversationId"]
    assert "This is the first file." in correction_2["originalText"]
    assert "This is the second file." in correction_2["originalText"]

def test_user_does_not_own_correction():
    response_1 = create_correction("This is User A's file.", USER_A_TOKEN)
    assert response_1.status_code == 200
    correction_1 = response_1.json()
    assert correction_1["userId"] == USER_A_ID

    response_2 = create_correction("This is User B's file.", USER_B_TOKEN)
    assert response_2.status_code == 403  # Forbidden
    assert response_2.json()["detail"] == "You do not have permission to modify this correction."