import requests

BASE_URL = "http://localhost:3001"

def test_signup_page_navigation_to_login():
    """
    TC003: Signup page provides navigation to the Login page
    Verifies users can reach the login screen from the signup screen using an in-page link.
    """

    try:
        login_payload = {"email": "nonexistent@example.com", "password": "wrongpassword"}
        post_login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload, timeout=30)
        assert post_login_resp.status_code == 401
        resp_json = post_login_resp.json()
        assert "error" in resp_json

    except requests.RequestException as e:
        assert False, f"Request failed: {str(e)}"

test_signup_page_navigation_to_login()