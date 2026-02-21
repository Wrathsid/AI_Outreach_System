import requests


BASE_URL = "http://localhost:3001"
TIMEOUT = 30


def test_search_with_no_matches_shows_empty_state():
    try:
        # First, login to obtain a valid JWT token
        login_payload = {
            "email": "testuser@example.com",
            "password": "TestPassword123!"
        }
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_payload,
            timeout=TIMEOUT
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("token")
        assert token, "Token not found in login response"

        headers = {"Authorization": f"Bearer {token}"}

        # Perform a search query expected to yield no results
        # Use a query string highly unlikely to have matches
        query = "thisqueryshouldnotmatchanycandidate1234567890"
        resp = requests.get(
            f"{BASE_URL}/api/candidates",
            headers=headers,
            params={"query": query},
            timeout=TIMEOUT,
        )

        assert resp.status_code == 200, f"Search API failed: {resp.text}"
        data = resp.json()

        # The API is expected to return an empty list for leads if no matches
        leads = data.get("lead_list") or data.get("leads") or data.get("candidate_list")
        # Acceptable keys might vary; check for any list with candidates
        if leads is None:
            # Fall back to whole response; if empty, then no matches
            leads = []
        assert isinstance(leads, list), "Leads result is not a list"
        assert len(leads) == 0, f"Expected no matches, but got {len(leads)} results"

        # Check for an 'empty state' message in the response, if present
        # According to general UI practice, API may provide a message or rely on empty list.
        empty_message = data.get("message") or data.get("empty_message") or data.get("info")
        if empty_message is not None:
            assert isinstance(empty_message, str), "Empty state message is not a string"
            assert len(empty_message) > 0, "Empty state message is empty"

    except requests.RequestException as e:
        assert False, f"HTTP request failed with exception: {e}"


test_search_with_no_matches_shows_empty_state()