import requests
import uuid

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_prevent_adding_same_candidate_to_pipeline_twice():
    # 1. Sign up a user
    signup_url = f"{BASE_URL}/api/auth/signup"
    login_url = f"{BASE_URL}/api/auth/login"
    headers = {"Content-Type": "application/json"}

    unique_email = f"testuser_{uuid.uuid4()}@example.com"
    password = "Password123!"
    signup_payload = {
        "name": "Test User",
        "email": unique_email,
        "password": password
    }

    signup_resp = requests.post(signup_url, json=signup_payload, headers=headers, timeout=TIMEOUT)
    assert signup_resp.status_code == 201, f"Signup failed: {signup_resp.text}"
    user_id = signup_resp.json().get("user_id")
    assert user_id, "user_id missing in signup response"

    # 2. Login to get JWT token
    login_payload = {
        "email": unique_email,
        "password": password
    }

    login_resp = requests.post(login_url, json=login_payload, headers=headers, timeout=TIMEOUT)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json().get("token")
    assert token, "JWT token missing in login response"
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 3. Search candidates to obtain a lead_id for testing
    candidates_search_url = f"{BASE_URL}/api/candidates"
    params = {"query": "software engineer"}

    search_resp = requests.get(candidates_search_url, headers=auth_headers, params=params, timeout=TIMEOUT)
    assert search_resp.status_code == 200, f"Search candidates failed: {search_resp.text}"
    leads = search_resp.json()
    assert isinstance(leads, list) and len(leads) > 0, "No leads found for candidate search"
    lead_id = leads[0].get("id") or leads[0].get("lead_id")
    assert lead_id, "Lead ID missing in candidate search result"

    pipeline_add_url = f"{BASE_URL}/api/pipeline/add"

    try:
        # 4. Add candidate to pipeline first time - should succeed
        add_payload = {"lead_id": lead_id}
        add_resp_1 = requests.post(pipeline_add_url, json=add_payload, headers=auth_headers, timeout=TIMEOUT)
        assert add_resp_1.status_code == 201, f"First add to pipeline failed: {add_resp_1.text}"
        pipeline_item_id = add_resp_1.json().get("pipeline_item_id")
        assert pipeline_item_id, "pipeline_item_id missing in add to pipeline response"

        # 5. Attempt to add same candidate again - expect 409 Conflict
        add_resp_2 = requests.post(pipeline_add_url, json=add_payload, headers=auth_headers, timeout=TIMEOUT)
        assert add_resp_2.status_code == 409, f"Second add to pipeline did not fail with 409: {add_resp_2.text}"
        error_message = add_resp_2.json().get("message")
        assert error_message == "Lead already in pipeline", f"Unexpected error message: {error_message}"

    finally:
        # 6. Cleanup: Remove the candidate from pipeline if added
        if pipeline_item_id:
            delete_url = f"{BASE_URL}/api/pipeline/{pipeline_item_id}"
            delete_resp = requests.delete(delete_url, headers=auth_headers, timeout=TIMEOUT)
            assert delete_resp.status_code in (200, 204), f"Cleanup delete pipeline item failed: {delete_resp.text}"


test_prevent_adding_same_candidate_to_pipeline_twice()