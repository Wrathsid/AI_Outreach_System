import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_edit_and_save_brain_skills_and_context_successfully():
    # User credentials for authentication (assumed test user exists)
    email = "testuser@example.com"
    password = "TestPassword123!"

    # Login to get JWT token
    login_url = f"{BASE_URL}/api/auth/login"
    login_payload = {"email": email, "password": password}
    try:
        login_resp = requests.post(login_url, json=login_payload, timeout=TIMEOUT)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("token")
        assert token, "No token received on login"
    except requests.RequestException as e:
        assert False, f"Login request failed: {e}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # First get current brain to revert back later
    brain_url = f"{BASE_URL}/api/brain"
    try:
        get_resp = requests.get(brain_url, headers=headers, timeout=TIMEOUT)
        assert get_resp.status_code == 200, f"Fetching brain failed: {get_resp.text}"
        original_brain = get_resp.json()
    except requests.RequestException as e:
        assert False, f"Get brain request failed: {e}"

    # Prepare updated brain payload
    updated_skills = ["Python", "Machine Learning", "Data Analysis"]
    updated_context = "Updated context for AI brain including latest projects and relevant experience."

    update_payload = {
        "skills": updated_skills,
        "context": updated_context
    }

    try:
        # Update brain with new skills and context
        put_resp = requests.put(brain_url, headers=headers, json=update_payload, timeout=TIMEOUT)
        assert put_resp.status_code == 200, f"Updating brain failed: {put_resp.text}"
        updated_brain = put_resp.json()
        # Validate the updated response matches what we sent
        assert "skills" in updated_brain and updated_brain["skills"] == updated_skills, "Skills not updated correctly"
        assert "context" in updated_brain and updated_brain["context"] == updated_context, "Context not updated correctly"
    except requests.RequestException as e:
        assert False, f"Update brain request failed: {e}"
    finally:
        # Revert changes to maintain test isolation
        try:
            requests.put(brain_url, headers=headers, json=original_brain, timeout=TIMEOUT)
        except:
            pass

test_edit_and_save_brain_skills_and_context_successfully()