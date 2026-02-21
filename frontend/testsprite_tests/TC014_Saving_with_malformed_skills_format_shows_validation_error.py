import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_saving_with_malformed_skills_format_shows_validation_error():
    # Credentials for login (assuming a pre-existing test user)
    login_payload = {
        "email": "testuser@example.com",
        "password": "TestPassword123!"
    }
    try:
        # Login to get JWT token
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_payload,
            timeout=TIMEOUT
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("token")
        assert token, "JWT token not found in login response"

        headers = {"Authorization": f"Bearer {token}"}

        # Prepare malformed skills payloads to test validation
        malformed_skills_payloads = [
            # Skills as a number instead of expected text or array
            {"skills": 12345, "context": "Some context info"},
            # Skills as a list with mixed types, including invalid objects
            {"skills": ["Python", {"skill": "JavaScript"}, 42], "context": "Context"},
            # Skills as a dict instead of list or string
            {"skills": {"not": "a valid structure"}, "context": "Context"},
            # Skills with non-text characters or badly encoded data
            {"skills": ["Python", "\ud83d\ude00", "\x00\x01"], "context": "Context"},
            # Skills as an empty object (invalid structure)
            {"skills": {}, "context": "Context"},
        ]

        for payload in malformed_skills_payloads:
            resp = requests.put(
                f"{BASE_URL}/api/brain",
                json=payload,
                headers=headers,
                timeout=TIMEOUT
            )
            # Expecting 400 Bad Request for malformed payload
            assert resp.status_code == 400, (
                f"Expected 400 Bad Request for payload {payload} but got {resp.status_code}: {resp.text}"
            )
            json_resp = resp.json()
            # Validate response contains message or errors key indicating validation issues
            assert (
                "validation" in resp.text.lower()
                or "error" in resp.text.lower()
                or "message" in json_resp
                or "errors" in json_resp
            ), f"Validation error details missing in response for payload {payload}: {resp.text}"

    except requests.RequestException as e:
        assert False, f"HTTP request failed: {e}"

test_saving_with_malformed_skills_format_shows_validation_error()