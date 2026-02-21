import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_save_invalid_preference_value_shows_inline_error():
    # First log in to get a valid JWT token for authorization
    login_url = f"{BASE_URL}/api/auth/login"
    login_payload = {
        "email": "testuser@example.com",
        "password": "TestPass123!"
    }
    try:
        login_resp = requests.post(login_url, json=login_payload, timeout=TIMEOUT)
        assert login_resp.status_code == 200, f"Login failed with status {login_resp.status_code}"
        token = login_resp.json().get("token")
        assert token, "JWT token not found in login response"
    except Exception as e:
        assert False, f"Login request failed: {e}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Prepare an invalid preferences payload for PUT /api/settings
    # Example: Assume preference 'tone' must be one of ['friendly','formal','casual'],
    # and here we send an invalid value to trigger validation error.
    invalid_preferences = {
        "tone_default": "invalid-tone-value-xyz",
        "ui_option": True
    }

    settings_url = f"{BASE_URL}/api/settings"

    try:
        put_resp = requests.put(settings_url, json=invalid_preferences, headers=headers, timeout=TIMEOUT)
    except Exception as e:
        assert False, f"PUT /api/settings request failed: {e}"

    # Validate the response is 422 Unprocessable Entity with validation errors
    assert put_resp.status_code == 422, f"Expected 422 status but got {put_resp.status_code}"

    resp_json = None
    try:
        resp_json = put_resp.json()
    except Exception:
        assert False, "Response is not valid JSON"

    # Check that response contains field errors, typically an errors dict with field names
    field_errors = resp_json.get("errors") or resp_json.get("field_errors")
    assert field_errors and isinstance(field_errors, dict), "Field errors not found in response"

    # Confirm that the invalid field 'tone_default' has an inline error message
    error_for_tone = field_errors.get("tone_default")
    assert error_for_tone and isinstance(error_for_tone, str) and len(error_for_tone) > 0, \
        "Inline error message for 'tone_default' preference not found or empty"


test_save_invalid_preference_value_shows_inline_error()