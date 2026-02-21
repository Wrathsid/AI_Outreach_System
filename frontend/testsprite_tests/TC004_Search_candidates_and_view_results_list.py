import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_search_candidates_and_view_results_list():
    # Credentials for login (must exist in the system for the test to pass)
    email = "testuser@example.com"
    password = "testpassword"

    # Step 1: Log in to get the JWT token
    try:
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT,
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        json_resp = login_resp.json()
        token = json_resp.get("token") or json_resp.get("access_token") or json_resp.get("jwt")
        assert token, f"No token received from login response: {login_resp.text}"
    except requests.RequestException as e:
        assert False, f"Login request exception: {e}"

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Perform candidate search
    search_query = "software engineer"
    try:
        search_resp = requests.get(
            f"{BASE_URL}/api/candidates",
            params={"query": search_query},
            headers=headers,
            timeout=TIMEOUT,
        )
        assert search_resp.status_code == 200, f"Search request failed: {search_resp.text}"
        data = search_resp.json()
        assert isinstance(data, dict), "Search response is not a JSON object"
        leads = data.get("leads") or data.get("lead_list") or data.get("candidates") or data.get("results")
        # The PRD states "Receive 200 with lead list". The exact field might vary; accept any list under keys.
        assert leads is not None, "No leads list found in search response"
        assert isinstance(leads, list), "Leads is not a list"
        # Optional: validate at least one lead or allow empty list (depends on DB state)
        # Just verify list structure if any results exist
        for lead in leads:
            assert isinstance(lead, dict), "Each lead should be an object/dict"
            assert "id" in lead or "lead_id" in lead, "Lead missing id"
            assert "name" in lead or "headline" in lead or "title" in lead, "Lead missing identifying info"
    except requests.RequestException as e:
        assert False, f"Search request exception: {e}"


test_search_candidates_and_view_results_list()
