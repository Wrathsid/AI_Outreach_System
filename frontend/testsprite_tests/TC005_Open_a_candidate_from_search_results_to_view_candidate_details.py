import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30


def test_open_candidate_from_search_to_view_details():
    # Setup: signup and login to obtain an auth token
    signup_url = f"{BASE_URL}/api/auth/signup"
    login_url = f"{BASE_URL}/api/auth/login"
    candidates_search_url = f"{BASE_URL}/api/candidates"
    
    # Use unique email to avoid conflicts
    import uuid
    unique_email = f"testuser_{uuid.uuid4().hex}@example.com"
    password = "TestPass123!"

    # Signup payload
    signup_payload = {
        "name": "Test User",
        "email": unique_email,
        "password": password
    }
    # signup user
    signup_resp = requests.post(signup_url, json=signup_payload, timeout=TIMEOUT)
    assert signup_resp.status_code == 201, f"Signup failed: {signup_resp.text}"
    user_id = signup_resp.json().get("user_id")
    assert user_id, "No user_id returned on signup"

    try:
        # Login to get JWT token
        login_payload = {"email": unique_email, "password": password}
        login_resp = requests.post(login_url, json=login_payload, timeout=TIMEOUT)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("token")
        assert token, "No token returned on login"

        headers = {"Authorization": f"Bearer {token}"}

        # Search candidates with a query that is likely to have results: "software engineer"
        params = {"query": "software engineer"}
        search_resp = requests.get(candidates_search_url, headers=headers, params=params, timeout=TIMEOUT)
        assert search_resp.status_code == 200, f"Candidate search failed: {search_resp.text}"

        candidates_data = search_resp.json()
        # Validate it returns a list of candidates (lead list)
        assert isinstance(candidates_data, dict), "Candidate search response is not a dict"
        lead_list = candidates_data.get("lead_list")
        assert isinstance(lead_list, list), "lead_list not found or not a list in search response"
        assert len(lead_list) > 0, "No candidates found in search results"

        # Pick the first candidate lead_id
        first_candidate = lead_list[0]
        lead_id = first_candidate.get("id") or first_candidate.get("lead_id")
        assert lead_id, "No lead_id found for candidate in search results"

        # Get candidate details by lead_id
        candidate_detail_url = f"{BASE_URL}/api/candidates/{lead_id}"
        detail_resp = requests.get(candidate_detail_url, headers=headers, timeout=TIMEOUT)
        assert detail_resp.status_code == 200, f"Candidate details fetch failed: {detail_resp.text}"

        candidate_details = detail_resp.json()
        # Check candidate details have expected keys - e.g. profile fields
        expected_keys = ["id", "name", "headline", "experience", "skills"]
        for key in expected_keys:
            assert key in candidate_details, f"Candidate detail missing key: {key}"
        assert candidate_details["id"] == lead_id, "Candidate ID mismatch in detail response"

    finally:
        # Cleanup: no candidate creation or other resources were made, so nothing to delete
        pass


test_open_candidate_from_search_to_view_details()