import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_candidate_details_core_sections():
    # Credentials for login - should be valid user in test env
    login_payload = {
        "email": "testuser@example.com",
        "password": "TestPassword123"
    }
    # Authenticate user
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload, timeout=TIMEOUT)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    login_json = login_resp.json()
    # Try to get token from common fields
    token = login_json.get("token") or login_json.get("access_token") or login_json.get("jwt")
    assert token, f"No token received on login, response keys: {list(login_json.keys())}"

    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Search candidates to get a candidate ID
    search_params = {"query": "software engineer"}
    search_resp = requests.get(f"{BASE_URL}/api/candidates", headers=headers, params=search_params, timeout=TIMEOUT)
    assert search_resp.status_code == 200, f"Candidate search failed: {search_resp.text}"
    candidates = search_resp.json()
    assert isinstance(candidates, list), "Candidates list is not a list"
    assert len(candidates) > 0, "No candidates found for query"

    candidate = candidates[0]
    candidate_id = candidate.get("id")
    assert candidate_id, "Candidate ID missing in search result"

    # Step 2: Get candidate details by ID
    details_resp = requests.get(f"{BASE_URL}/api/candidates/{candidate_id}", headers=headers, timeout=TIMEOUT)
    assert details_resp.status_code == 200, f"Candidate details fetch failed: {details_resp.text}"
    details = details_resp.json()
    # Check for core profile sections: headline, experience, skills
    # Assuming keys: 'headline', 'experience', 'skills' present as per typical profile data model
    assert "headline" in details and isinstance(details["headline"], str) and details["headline"], "Headline missing or empty"
    assert "experience" in details and isinstance(details["experience"], list) and len(details["experience"]) > 0, "Experience section missing or empty"
    assert "skills" in details and isinstance(details["skills"], list) and len(details["skills"]) > 0, "Skills section missing or empty"

test_candidate_details_core_sections()
