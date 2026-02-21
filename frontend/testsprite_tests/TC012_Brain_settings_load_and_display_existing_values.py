import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_brain_settings_load_and_display_existing_values():
    # Credentials for authentication - replace with valid test user
    email = "testuser@example.com"
    password = "TestPassword123!"

    session = requests.Session()

    try:
        # Login to get JWT token
        login_resp = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=TIMEOUT
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("token")
        assert token, "No token received from login"

        headers = {"Authorization": f"Bearer {token}"}

        # Call GET /api/brain to fetch current brain settings
        brain_resp = session.get(f"{BASE_URL}/api/brain", headers=headers, timeout=TIMEOUT)

        assert brain_resp.status_code == 200, f"Failed to load brain settings: {brain_resp.text}"
        data = brain_resp.json()
        
        # Validate that skills and context keys exist and are of expected types
        assert "skills" in data, "Key 'skills' missing in brain settings response"
        assert isinstance(data["skills"], list), "'skills' should be a list"
        for skill in data["skills"]:
            assert isinstance(skill, str), "Each skill should be a string"
        assert "context" in data, "Key 'context' missing in brain settings response"
        assert isinstance(data["context"], str), "'context' should be a string"

    finally:
        session.close()

test_brain_settings_load_and_display_existing_values()