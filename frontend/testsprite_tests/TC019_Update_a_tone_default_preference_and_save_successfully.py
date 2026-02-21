import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_update_tone_default_preference_and_save_successfully():
    # Credentials for login - assumed to be valid for testing
    auth_email = "testuser@example.com"
    auth_password = "TestPassword123!"

    signup_url = f"{BASE_URL}/api/auth/signup"
    login_url = f"{BASE_URL}/api/auth/login"
    settings_url = f"{BASE_URL}/api/settings"

    user_info = {
        "name": "Test User",
        "email": auth_email,
        "password": auth_password
    }

    # Prepare headers and variables
    token = None
    created_user_id = None

    try:
        # Signup the user
        signup_resp = requests.post(signup_url, json=user_info, timeout=TIMEOUT)
        assert signup_resp.status_code == 201, f"Signup failed: {signup_resp.text}"
        created_user_id = signup_resp.json().get("user_id")
        assert created_user_id, "Signup response missing user_id"

        # Login to get JWT token
        login_resp = requests.post(login_url, json={"email": auth_email, "password": auth_password}, timeout=TIMEOUT)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("token")
        assert token, "Login response missing token"

        headers = {"Authorization": f"Bearer {token}"}

        # First, get current settings to know existing tone preference
        get_resp = requests.get(settings_url, headers=headers, timeout=TIMEOUT)
        assert get_resp.status_code == 200, f"Get settings failed: {get_resp.text}"
        current_settings = get_resp.json()
        current_tone = current_settings.get("tone_default") or current_settings.get("tone") or "neutral"

        # Pick a new tone preference different from current (example tones)
        possible_tones = ["friendly", "formal", "casual", "professional", "enthusiastic", "neutral"]
        new_tone = next((tone for tone in possible_tones if tone != current_tone), "friendly")

        # Update settings with new tone preference
        update_payload = current_settings.copy()
        # Depending on schema tone preference field could be tone_default or a nested preferences. Here we assume tone_default key
        update_payload["tone_default"] = new_tone

        put_resp = requests.put(settings_url, headers={**headers, "Content-Type": "application/json"}, json=update_payload, timeout=TIMEOUT)
        assert put_resp.status_code == 200, f"Update settings failed: {put_resp.text}"
        updated_settings = put_resp.json()
        assert updated_settings.get("tone_default") == new_tone or updated_settings.get("tone") == new_tone, "Tone default preference not updated in response"

    finally:
        # Cleanup: delete the created user if possible
        # Assuming no API to delete user in PRD, so skipping deletion
        pass


test_update_tone_default_preference_and_save_successfully()