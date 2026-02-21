import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_search_empty_query_does_not_break_page():
    """
    Verifies submitting an empty search query does not crash and keeps the user on the Candidates page.
    Expected behavior: API returns 200 OK with valid structure (likely an empty or default candidate list).
    """

    # Assumption: Authentication is required. We'll login first to get a token.
    login_url = f"{BASE_URL}/api/auth/login"
    credentials = {"email": "testuser@example.com", "password": "TestPassword123!"}
    headers = {"Content-Type": "application/json"}

    try:
        login_response = requests.post(login_url, json=credentials, headers=headers, timeout=TIMEOUT)
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("token") or login_response.json().get("access_token")
        assert token, "Authorization token not found in login response"

        # Make the search request with empty query
        candidates_url = f"{BASE_URL}/api/candidates"
        search_params = {"query": ""}
        auth_headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(candidates_url, headers=auth_headers, params=search_params, timeout=TIMEOUT)

        # Validate the response to ensure no crash and stable UI expected
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        data = response.json()
        # According to PRD, GET /api/candidates?query=... returns lead list
        # For empty query, expect a list present (empty array or default list)
        assert isinstance(data, dict) or isinstance(data, list), "Response should be JSON object or list"

        # If dict, check keys for typical response like lead list
        if isinstance(data, dict):
            # There may be a lead list key or candidate list
            assert any(key in data for key in ["leads", "candidates", "lead_list", "candidate_list"]), \
                f"Response JSON keys unexpected: {list(data.keys())}"

        # If list, it should be an empty list or list of leads
        if isinstance(data, list):
            # No crash if empty or leads list
            assert True

    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

test_search_empty_query_does_not_break_page()