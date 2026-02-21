import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_TC020_verify_saved_tone_preference_persists_after_page_refresh():
    # Test data for authentication (use a test user)
    signup_payload = {
        "name": "Test User",
        "email": "testuser_tc020@example.com",
        "password": "TestPass123!"
    }
    login_payload = {
        "email": signup_payload["email"],
        "password": signup_payload["password"]
    }
    headers = {"Content-Type": "application/json"}

    # Preset tone preference to save and verify
    tone_preference = "friendly"

    user_id = None
    token = None

    try:
        # Sign up the user (ignore if user exists, proceed to login)
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_payload, headers=headers, timeout=TIMEOUT)
        if signup_resp.status_code not in (201, 409):
            signup_resp.raise_for_status()
        # If 409 Conflict returned, user already exists - continue

        # Login to get token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload, headers=headers, timeout=TIMEOUT)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("token") or login_resp.json().get("access_token")
        assert token, "JWT token missing in login response"

        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Get current user profile to obtain user_id (optional, but better for cleanup)
        profile_resp = requests.get(f"{BASE_URL}/api/profile", headers=auth_headers, timeout=TIMEOUT)
        assert profile_resp.status_code == 200, f"Could not get profile: {profile_resp.text}"
        user = profile_resp.json()
        user_id = user.get("user_id") or user.get("id")

        # Step 1: Save tone preference via PUT /api/settings
        # Get initial settings first to preserve other settings if any
        get_settings_resp = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers, timeout=TIMEOUT)
        assert get_settings_resp.status_code == 200, f"Get settings failed: {get_settings_resp.text}"
        current_settings = get_settings_resp.json()

        updated_settings = current_settings.copy()
        updated_settings["tone_default"] = tone_preference

        put_settings_resp = requests.put(f"{BASE_URL}/api/settings", json=updated_settings, headers=auth_headers, timeout=TIMEOUT)
        assert put_settings_resp.status_code == 200, f"Saving settings failed: {put_settings_resp.text}"
        saved_settings = put_settings_resp.json()
        assert saved_settings.get("tone_default") == tone_preference, "Tone preference was not saved properly"

        # Step 2: Refresh Settings page: GET /api/settings and verify tone_default persists
        refreshed_settings_resp = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers, timeout=TIMEOUT)
        assert refreshed_settings_resp.status_code == 200, f"Reloading settings failed: {refreshed_settings_resp.text}"
        refreshed_settings = refreshed_settings_resp.json()
        assert refreshed_settings.get("tone_default") == tone_preference, "Tone preference did not persist after refresh"

    finally:
        # Cleanup: reset tone_default to prior value or null if possible
        if token:
            cleanup_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            try:
                # Attempt to get current settings again
                resp = requests.get(f"{BASE_URL}/api/settings", headers=cleanup_headers, timeout=TIMEOUT)
                if resp.status_code == 200:
                    original_settings = resp.json()
                    # Remove tone_default or reset to previous if known; here remove it
                    if "tone_default" in original_settings:
                        original_settings.pop("tone_default", None)
                    requests.put(f"{BASE_URL}/api/settings", json=original_settings, headers=cleanup_headers, timeout=TIMEOUT)
            except Exception:
                pass
        # Optionally, could delete test user if API supports - not specified in PRD

test_TC020_verify_saved_tone_preference_persists_after_page_refresh()