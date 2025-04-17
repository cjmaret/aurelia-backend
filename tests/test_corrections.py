import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app import app  # Import your FastAPI app
from app.services.database_service import get_collection

client = TestClient(app)

corrections_collection = get_collection("corrections")

# Mock data for testing
USER_A_TOKEN = "user_a_token"
USER_B_TOKEN = "user_b_token"

USER_A_ID = "user_a"
USER_B_ID = "user_b"

# Mock JWT decoding for testing
def mock_decode_token(token: str):
    if token == USER_A_TOKEN:
        return USER_A_ID
    elif token == USER_B_TOKEN:
        return USER_B_ID
    return None

# Patch the decode_token function in auth.py
@pytest.fixture(autouse=True)
def patch_decode_token(monkeypatch):
    from app.utils.auth_utils import decode_token
    monkeypatch.setattr(decode_token, "__call__", mock_decode_token)

# Helper function to create a correction
def create_correction(file_content: str, token: str):
    response = client.post(
        "/api/v1/corrections",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", file_content)},
    )
    return response

# Test Scenario 1: User Owns the Correction
def test_user_owns_correction():
    # Step 1: User A uploads a file, creating a correction
    response_1 = create_correction("This is the first file.", USER_A_TOKEN)
    assert response_1.status_code == 200
    correction_1 = response_1.json()
    assert correction_1["userId"] == USER_A_ID

    # Step 2: User A uploads another file within 5 minutes, triggering a merge
    response_2 = create_correction("This is the second file.", USER_A_TOKEN)
    assert response_2.status_code == 200
    correction_2 = response_2.json()

    # Verify that the correction was merged
    assert correction_1["conversationId"] == correction_2["conversationId"]
    assert "This is the first file." in correction_2["originalText"]
    assert "This is the second file." in correction_2["originalText"]

# Test Scenario 2: User Does Not Own the Correction
def test_user_does_not_own_correction():
    # Step 1: User A uploads a file, creating a correction
    response_1 = create_correction("This is User A's file.", USER_A_TOKEN)
    assert response_1.status_code == 200
    correction_1 = response_1.json()
    assert correction_1["userId"] == USER_A_ID

    # Step 2: User B uploads a file within 5 minutes, attempting to merge with User A's correction
    response_2 = create_correction("This is User B's file.", USER_B_TOKEN)
    assert response_2.status_code == 403  # Forbidden
    assert response_2.json()["detail"] == "You do not have permission to modify this correction."