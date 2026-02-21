import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_saving_with_empty_skills_shows_validation_error():
    # Credentials for an existing test user (adjust as necessary)
    email = "testuser@example.com"
    password = "TestPassword123"

    # Authenticate: login to get JWT token
    login_url = f"{BASE_URL}/api/auth/login"
    login_payload = {"email": email, "password": password}
    login_response = requests.post(login_url, json=login_payload, timeout=TIMEOUT)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json().get("token")
    assert token, "Token not found in login response"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    brain_url = f"{BASE_URL}/api/brain"

    # Retrieve current brain context and skills to restore after test
    get_response = requests.get(brain_url, headers=headers, timeout=TIMEOUT)
    assert get_response.status_code == 200, f"Failed to get brain data: {get_response.text}"
    original_brain = get_response.json()

    try:
        # Attempt to save empty skills (empty array) - expect validation error (HTTP 400)
        put_payload = {
            "skills": [],   # empty skills list as per test case
            "context": original_brain.get("context", "")
        }
        put_response = requests.put(brain_url, json=put_payload, headers=headers, timeout=TIMEOUT)
        assert put_response.status_code == 400 or put_response.status_code == 422, (
            f"Expected validation error status 400 or 422 but got {put_response.status_code}"
        )
        error_body = put_response.json()
        # Check for validation error message presence
        assert (
            "validation" in error_body.get("message", "").lower()
            or "skills" in str(error_body.get("errors", "")).lower()
        ), f"Expected validation error message about skills, got: {error_body}"
    finally:
        # Restore original brain skills and context to not affect other tests
        restore_payload = {
            "skills": original_brain.get("skills", []),
            "context": original_brain.get("context", "")
        }
        restore_response = requests.put(brain_url, json=restore_payload, headers=headers, timeout=TIMEOUT)
        assert restore_response.status_code == 200, f"Failed to restore brain data: {restore_response.text}"

test_saving_with_empty_skills_shows_validation_error()