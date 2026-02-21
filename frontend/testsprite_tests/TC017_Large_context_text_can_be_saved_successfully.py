import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30  # seconds

# Sample user credentials for authentication
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "TestPassword123!"

def authenticate():
    # Login to get JWT token
    login_url = f"{BASE_URL}/api/auth/login"
    login_payload = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    try:
        login_resp = requests.post(login_url, json=login_payload, timeout=TIMEOUT)
        assert login_resp.status_code == 200, f"Login failed with status {login_resp.status_code}"
        token = login_resp.json().get("token")
        assert token, "JWT token missing in login response"
        return token
    except (requests.RequestException, AssertionError) as e:
        raise RuntimeError(f"Authentication failed: {e}")

def get_current_brain(headers):
    url = f"{BASE_URL}/api/brain"
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to get current brain data: {e}")

def update_brain(headers, skills, context):
    url = f"{BASE_URL}/api/brain"
    payload = {
        "skills": skills,
        "context": context
    }
    try:
        resp = requests.put(url, headers=headers, json=payload, timeout=TIMEOUT)
        return resp
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to update brain: {e}")

def test_large_context_can_be_saved_successfully():
    token = authenticate()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    original_brain = get_current_brain(headers)
    original_skills = original_brain.get("skills", [])
    # In case original_skills is None, convert to empty list
    if original_skills is None:
        original_skills = []

    # Create a large context text, 10_000 characters approx
    large_context = "LargeContextText " * 700  # approx 14 chars * 700 ~ 9800 chars + spaces

    try:
        # Update brain with the original skills and large context
        resp = update_brain(headers, original_skills, large_context)
        assert resp.status_code == 200, f"Failed to save large context: {resp.status_code} - {resp.text}"

        updated_brain = resp.json()
        # Validate returned context matches what was sent
        saved_context = updated_brain.get("context", "")
        assert saved_context == large_context, "Saved context does not match the large context sent"

        # Optionally, validate skills unchanged
        saved_skills = updated_brain.get("skills", [])
        assert saved_skills == original_skills, "Skills changed unexpectedly during large context update"
    finally:
        # Restore original brain data to avoid side effects
        restore_resp = update_brain(headers, original_skills, original_brain.get("context", ""))
        assert restore_resp.status_code == 200, f"Failed to restore original brain data: {restore_resp.status_code}"

test_large_context_can_be_saved_successfully()