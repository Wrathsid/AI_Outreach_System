import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_add_candidate_to_pipeline_from_details():
    session = requests.Session()
    try:
        # Step 1: Sign up a new user
        signup_payload = {
            "name": "Test User TC006",
            "email": "testuser_tc006@example.com",
            "password": "StrongPassw0rd!"
        }
        resp_signup = session.post(f"{BASE_URL}/api/auth/signup", json=signup_payload, timeout=TIMEOUT)
        assert resp_signup.status_code == 201, f"Signup failed: {resp_signup.text}"
        user_id = resp_signup.json().get("user_id")
        assert user_id, "Signup response missing user_id"

        # Step 2: Login with the new user to get JWT token
        login_payload = {
            "email": signup_payload["email"],
            "password": signup_payload["password"]
        }
        resp_login = session.post(f"{BASE_URL}/api/auth/login", json=login_payload, timeout=TIMEOUT)
        assert resp_login.status_code == 200, f"Login failed: {resp_login.text}"
        token = resp_login.json().get("token")
        assert token, "Login response missing token"
        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: Search for candidates (use sample query "software engineer")
        search_params = {"query": "software engineer"}
        resp_search = session.get(f"{BASE_URL}/api/candidates", headers=headers, params=search_params, timeout=TIMEOUT)
        assert resp_search.status_code == 200, f"Candidate search failed: {resp_search.text}"
        candidates = resp_search.json()
        assert isinstance(candidates, list) or "results" in resp_search.json(), "Candidate search response invalid"

        # Pick first candidate lead_id safely from results
        if isinstance(candidates, list):
            candidate_list = candidates
        elif "results" in resp_search.json():
            candidate_list = resp_search.json().get("results")
        else:
            candidate_list = None
        assert candidate_list and len(candidate_list) > 0, "No candidates found for adding to pipeline"
        lead_id = None
        # Support different formats gracefully
        # If response is list of candidates, expect dict with id keys maybe
        for c in candidate_list:
            if isinstance(c, dict):
                lead_id = c.get("id") or c.get("lead_id") or c.get("candidate_id")
                if lead_id:
                    break
        assert lead_id, "Lead ID not found in candidate list"

        # Step 4: Get candidate details with lead_id
        resp_details = session.get(f"{BASE_URL}/api/candidates/{lead_id}", headers=headers, timeout=TIMEOUT)
        assert resp_details.status_code == 200, f"Getting candidate details failed: {resp_details.text}"

        # Step 5: Add candidate to pipeline
        add_payload = {"lead_id": lead_id}
        resp_add = session.post(f"{BASE_URL}/api/pipeline/add", json=add_payload, headers=headers, timeout=TIMEOUT)
        assert resp_add.status_code == 201, f"Adding candidate to pipeline failed: {resp_add.text}"
        pipeline_item_id = resp_add.json().get("pipeline_item_id")
        assert pipeline_item_id, "Response missing pipeline_item_id after adding candidate to pipeline"

    finally:
        # Cleanup: Remove the candidate from pipeline to maintain test idempotency
        # Assuming DELETE /api/pipeline/{pipeline_item_id} exists per API patterns (not explicit in PRD)
        if 'pipeline_item_id' in locals() and pipeline_item_id:
            try:
                session.delete(f"{BASE_URL}/api/pipeline/{pipeline_item_id}", headers=headers, timeout=TIMEOUT)
            except Exception:
                pass

        # Cleanup: Delete the created user
        if 'user_id' in locals() and user_id:
            # Assuming DELETE /api/users/{user_id} or similar exists (not explicit in PRD)
            # If not available, just ignore
            try:
                session.delete(f"{BASE_URL}/api/users/{user_id}", headers=headers, timeout=TIMEOUT)
            except Exception:
                pass

test_add_candidate_to_pipeline_from_details()