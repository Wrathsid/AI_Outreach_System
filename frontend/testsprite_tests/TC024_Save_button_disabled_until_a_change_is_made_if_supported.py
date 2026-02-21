import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_save_button_disabled_until_change():
    """
    Verifies the page prevents saving when no settings have changed.
    Since this is an API test, we will:
    - GET current user settings
    - Try to PUT same settings back without changes
    - Expect success (200) but no actual change or indication of update
    - To detect that "save button is disabled if no change", we infer by confirming
      that PUT with identical data does not alter the resource or returns an appropriate response.
    """
    session = requests.Session()
    # Assuming we have valid credentials for testing
    email = "testuser@example.com"
    password = "TestPass123!"

    # Authenticate to get token
    try:
        login_resp = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=TIMEOUT
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("token")
        assert token, "No token in login response"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Get current settings
        get_resp = session.get(f"{BASE_URL}/api/settings", headers=headers, timeout=TIMEOUT)
        assert get_resp.status_code == 200, f"Failed to get settings: {get_resp.text}"
        current_settings = get_resp.json()

        # PUT the exact same settings back
        put_resp = session.put(f"{BASE_URL}/api/settings", headers=headers, json=current_settings, timeout=TIMEOUT)

        # Expect 200 OK since no change is made, and no error
        assert put_resp.status_code == 200, f"PUT with no changes failed: {put_resp.text}"

        updated_settings = put_resp.json()

        # Assert that settings remain unchanged
        assert updated_settings == current_settings, "Settings changed despite no modifications"

    finally:
        session.close()

test_save_button_disabled_until_change()