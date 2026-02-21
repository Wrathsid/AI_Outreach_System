import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_update_ui_option_preference_and_save_successfully():
    # Use test credentials - adjust if needed
    signup_url = f"{BASE_URL}/api/auth/signup"
    login_url = f"{BASE_URL}/api/auth/login"
    settings_url = f"{BASE_URL}/api/settings"

    test_user = {
        "name": "Test User TC021",
        "email": "testuser_tc021@example.com",
        "password": "ComplexPass!234"
    }

    # Headers for JSON content
    headers = {"Content-Type": "application/json"}

    # Try signup first; if user exists, ignore error
    try:
        resp = requests.post(signup_url, json={
            "name": test_user["name"],
            "email": test_user["email"],
            "password": test_user["password"]
        }, timeout=TIMEOUT, headers=headers)
        assert resp.status_code == 201 or (resp.status_code == 409), f"Unexpected signup status: {resp.status_code}"
    except Exception:
        pass

    # Login to obtain token
    login_resp = requests.post(login_url, json={
        "email": test_user["email"],
        "password": test_user["password"]
    }, timeout=TIMEOUT, headers=headers)
    assert login_resp.status_code == 200, f"Login failed with status {login_resp.status_code}"
    token = login_resp.json().get("token") or login_resp.json().get("access_token")
    assert token, "No token received on login"

    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Get current user settings
    get_settings_resp = requests.get(settings_url, headers=auth_headers, timeout=TIMEOUT)
    assert get_settings_resp.status_code == 200, f"Failed to get settings: {get_settings_resp.status_code}"
    current_settings = get_settings_resp.json()

    # Identify a UI option preference to toggle
    # Without exact schema, assume there's a boolean preference under 'uiOptions' or similar
    # Find first boolean UI pref to toggle, fallback to a default key "darkMode"
    preferences = current_settings.get("preferences") or current_settings.get("uiOptions") or current_settings
    key_to_toggle = None
    original_value = None
    if isinstance(preferences, dict):
        for k, v in preferences.items():
            if isinstance(v, bool):
                key_to_toggle = k
                original_value = v
                break

    if key_to_toggle is None:
        # fallback to 'darkMode' boolean option if exists
        key_to_toggle = "darkMode"
        original_value = preferences.get(key_to_toggle, False)
    
    # Toggle the boolean value
    updated_value = not original_value

    # Prepare updated preferences payload
    updated_preferences = preferences.copy() if isinstance(preferences, dict) else {}
    updated_preferences[key_to_toggle] = updated_value

    # PUT updated preferences
    put_resp = requests.put(settings_url, json={"preferences": updated_preferences}, headers=auth_headers, timeout=TIMEOUT)
    assert put_resp.status_code == 200, f"Failed to update settings: {put_resp.status_code}"

    saved_settings = put_resp.json()
    saved_prefs = saved_settings.get("preferences") or saved_settings
    assert saved_prefs.get(key_to_toggle) == updated_value, "Preference value not updated correctly"

    # Cleanup: revert to original preference value
    try:
        requests.put(settings_url, json={"preferences": {key_to_toggle: original_value}}, headers=auth_headers, timeout=TIMEOUT)
    except Exception:
        pass

test_update_ui_option_preference_and_save_successfully()