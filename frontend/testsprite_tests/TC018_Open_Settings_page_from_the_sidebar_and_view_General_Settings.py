import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

# Replace these with valid test user credentials
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "TestPassword123"

def test_TC018_open_settings_page_and_view_general_settings():
    # Step 1: Login to get JWT token
    login_url = f"{BASE_URL}/api/auth/login"
    login_payload = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    }
    login_response = requests.post(login_url, json=login_payload, timeout=TIMEOUT)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    login_json = login_response.json()
    token = login_json.get("token") or login_json.get("jwt")
    assert token, "JWT token not found in login response"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Step 2: Access the Settings page content (General Settings) via GET /api/settings
    settings_url = f"{BASE_URL}/api/settings"
    settings_response = requests.get(settings_url, headers=headers, timeout=TIMEOUT)
    assert settings_response.status_code == 200, f"Failed to access Settings: {settings_response.text}"
    settings_json = settings_response.json()

    # Validate that settings JSON contains known user preference keys commonly expected in General Settings
    assert isinstance(settings_json, dict), "Settings response is not a JSON object"
    expected_keys = ["tone_defaults", "ui_options", "preferences"]
    found_key = any(key in settings_json for key in expected_keys)
    assert found_key, "Settings response does not contain expected General Settings keys"

test_TC018_open_settings_page_and_view_general_settings()