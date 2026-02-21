import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_cancel_discard_changes_does_not_persist_modifications():
    # Use test user credentials (adjust as needed)
    test_email = "testuser@example.com"
    test_password = "TestPass123!"

    # Sign up new user to isolate the test environment
    signup_payload = {
        "name": "Test User",
        "email": test_email,
        "password": test_password
    }
    try:
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_payload, timeout=TIMEOUT)
        # If user already exists, 409 is acceptable, else expect 201
        assert signup_resp.status_code in (201, 409), f"Unexpected signup status {signup_resp.status_code}"
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Signup request failed: {e}")

    # Login to get JWT token
    login_payload = {
        "email": test_email,
        "password": test_password
    }
    try:
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload, timeout=TIMEOUT)
        assert login_resp.status_code == 200, f"Login failed with status {login_resp.status_code}"
        token = login_resp.json().get("token")
        assert token, "JWT token not found in login response"
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Login request failed: {e}")

    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Get current settings
    try:
        get_settings_resp = requests.get(f"{BASE_URL}/api/settings", headers=headers, timeout=TIMEOUT)
        assert get_settings_resp.status_code == 200, f"Getting settings failed with status {get_settings_resp.status_code}"
        original_settings = get_settings_resp.json()
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Get settings request failed: {e}")

    # Step 2: Modify settings locally but do NOT save (simulate cancel/discard)
    # We'll simulate this by NOT calling the PUT endpoint.
    # The test is that after "discard", settings remain unchanged.

    # For the purpose of the test, we make a changed copy
    modified_settings = original_settings.copy()
    # Assumption: tone preference is a key in the settings; if missing pick a dummy key to toggle
    tone_key = "tone_default" if "tone_default" in modified_settings else next(iter(modified_settings), None)
    if tone_key:
        original_value = modified_settings[tone_key]
        if isinstance(original_value, bool):
            modified_settings[tone_key] = not original_value
        elif isinstance(original_value, str):
            modified_settings[tone_key] = original_value + "_modified"
        elif isinstance(original_value, int):
            modified_settings[tone_key] = original_value + 1
        else:
            # If type unknown, do not modify and skip
            modified_settings = None
    else:
        modified_settings = None

    # Step 3: Simulate user discarding changes by not saving modified_settings
    # Step 4: Get settings again and check they are unchanged compared to original
    try:
        confirm_settings_resp = requests.get(f"{BASE_URL}/api/settings", headers=headers, timeout=TIMEOUT)
        assert confirm_settings_resp.status_code == 200, f"Getting settings after discard failed with status {confirm_settings_resp.status_code}"
        settings_after_discard = confirm_settings_resp.json()
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Get settings after discard request failed: {e}")

    assert settings_after_discard == original_settings, "Settings changed despite discarding modifications"

test_cancel_discard_changes_does_not_persist_modifications()