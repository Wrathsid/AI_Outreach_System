import requests

BASE_URL = "http://localhost:3001"
TIMEOUT = 30

def test_signup_with_missing_required_fields_shows_validation_feedback():
    url = f"{BASE_URL}/api/auth/signup"
    headers = {
        "Content-Type": "application/json"
    }
    # Missing required fields: submitting empty payload
    payload = {}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    # Expecting 400 Bad Request or similar validation error status code
    assert response.status_code in (400, 422), f"Expected 400 or 422, got {response.status_code}"
    
    # Response should contain validation errors indicating missing required fields
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate presence of error messages related to required fields
    errors_found = False
    error_keys = ['name', 'email', 'password']
    for key in error_keys:
        if key in data and (isinstance(data[key], list) or isinstance(data[key], str)):
            errors_found = True
            break
        if 'errors' in data and key in data['errors']:
            errors_found = True
            break
    assert errors_found, f"Expected validation error messages for missing required fields in response, got: {data}"

test_signup_with_missing_required_fields_shows_validation_feedback()