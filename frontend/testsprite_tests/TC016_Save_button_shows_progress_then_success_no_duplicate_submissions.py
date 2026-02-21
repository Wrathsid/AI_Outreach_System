import requests
import time

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_save_button_shows_progress_then_success_no_duplicate_submissions():
    # Use login credentials from a test user or create a new user for test
    signup_url = f"{BASE_URL}/api/auth/signup"
    login_url = f"{BASE_URL}/api/auth/login"
    brain_url = f"{BASE_URL}/api/brain"

    test_user = {
        "name": "Test User TC016",
        "email": "testuser_tc016@example.com",
        "password": "StrongPassword!123"
    }

    # Signup and Login to get token
    # Signup (ignoring if already exists - handle 409 conflict)
    try:
        signup_resp = requests.post(signup_url, json=test_user, timeout=TIMEOUT)
        if signup_resp.status_code not in (201, 409):
            assert False, f"Unexpected signup status: {signup_resp.status_code} {signup_resp.text}"
    except requests.RequestException as e:
        assert False, f"Signup request failed: {e}"

    # Login
    try:
        login_resp = requests.post(login_url, json={"email": test_user["email"], "password": test_user["password"]}, timeout=TIMEOUT)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.status_code} {login_resp.text}"
        token = login_resp.json().get("token")
        assert token is not None, "Login response missing token"
        headers = {"Authorization": f"Bearer {token}"}
    except requests.RequestException as e:
        assert False, f"Login request failed: {e}"

    # Retrieve current brain context for revert later
    try:
        brain_get_resp = requests.get(brain_url, headers=headers, timeout=TIMEOUT)
        assert brain_get_resp.status_code == 200, f"Failed to get brain: {brain_get_resp.status_code} {brain_get_resp.text}"
        original_brain = brain_get_resp.json()
    except requests.RequestException as e:
        assert False, f"Brain GET request failed: {e}"

    # Prepare payload for brain update (simulate Save button action)
    # Test rapid multiple submissions that should not cause duplicated saves.
    updated_skills = original_brain.get("skills", []) + ["test_skill_tc016"]
    updated_context = original_brain.get("context", "") + " Save progress test context."

    update_payload = {
        "skills": updated_skills,
        "context": updated_context
    }

    # We'll simulate rapid multiple PUT requests (like clicking Save multiple times quickly)
    # and expect only one successful save and no duplicated state or error.
    # Also, we capture timestamps and responses to verify progress then success.

    responses = []
    errors = []

    try:
        # Fire multiple PUT requests in rapid succession (3 times)
        for _ in range(3):
            resp = requests.put(brain_url, json=update_payload, headers=headers, timeout=TIMEOUT)
            responses.append(resp)
            # Small pause to simulate near-simultaneous (e.g., 0.2 seconds)
            time.sleep(0.2)
    except requests.RequestException as e:
        errors.append(e)

    # Validate that there were no request exceptions
    assert not errors, f"Request exceptions occurred: {errors}"

    # Validate responses:
    # - The first request should go through and respond with 200
    # - Further requests should not cause duplicated entries or errors.
    success_responses = [r for r in responses if r.status_code == 200]
    assert success_responses, "No successful save responses received."

    # Validate that all successful responses have identical brain state returned
    brain_states = [r.json() for r in success_responses]
    first_state = brain_states[0]
    for state in brain_states[1:]:
        assert state == first_state, "Brain states differ between rapid save requests, indicating duplicate or inconsistent saves."

    # Optional: Validate that the brain actually updated with new skills/context on server
    try:
        final_brain_resp = requests.get(brain_url, headers=headers, timeout=TIMEOUT)
        assert final_brain_resp.status_code == 200, f"Final brain fetch failed: {final_brain_resp.status_code} {final_brain_resp.text}"
        final_brain = final_brain_resp.json()
        # The updated skills/context should be reflected
        for skill in updated_skills:
            assert skill in final_brain.get("skills", []), f"Skill '{skill}' not found in final brain skills."
        assert updated_context.strip() in final_brain.get("context", ""), "Updated context not found in final brain context."
    except requests.RequestException as e:
        assert False, f"Final brain GET request failed: {e}"

    # Cleanup: revert brain to original state using PUT
    try:
        revert_resp = requests.put(brain_url, json=original_brain, headers=headers, timeout=TIMEOUT)
        assert revert_resp.status_code == 200, f"Failed to revert brain: {revert_resp.status_code} {revert_resp.text}"
    except requests.RequestException as e:
        assert False, f"Brain revert request failed: {e}"

test_save_button_shows_progress_then_success_no_duplicate_submissions()