import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_login_page_navigates_to_signup_page():
    """
    Verifies users can reach the signup screen from the login screen using an in-page link.
    
    Since this is a frontend navigation scenario and the backend PRD does not specify
    any API endpoint for checking navigation links, this test will simulate the 
    behavior by verifying that the signup page is reachable (HTTP 200) and that the login
    page is reachable (HTTP 200). This infers that navigation can occur between these pages.

    This aligns with the files referenced in PRD under Authentication feature:
    - src/app/login/page.tsx
    - src/app/signup/page.tsx

    """
    try:
        # Access login page URL
        login_resp = requests.get(f"{BASE_URL}/login", timeout=TIMEOUT)
        assert login_resp.status_code == 200, f"Expected 200 OK on login page, got {login_resp.status_code}"

        # Access signup page URL
        signup_resp = requests.get(f"{BASE_URL}/signup", timeout=TIMEOUT)
        assert signup_resp.status_code == 200, f"Expected 200 OK on signup page, got {signup_resp.status_code}"

        # Check that signup page content contains a sign-up form identifier or heading
        signup_content = signup_resp.text.lower()
        assert "sign up" in signup_content or "signup" in signup_content, "Signup page content missing 'Sign Up' indicators"

        # Check that login page content contains a link or indicator for signup navigation
        login_content = login_resp.text.lower()
        # look for href or text referring to signup page or route
        assert ("signup" in login_content or "/signup" in login_content), "Login page content missing link to signup page"

    except requests.RequestException as e:
        assert False, f"HTTP request failed: {str(e)}"

test_login_page_navigates_to_signup_page()