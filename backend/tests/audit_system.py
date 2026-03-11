import requests

API_URL = "http://localhost:8000"


def log(msg):
    print(f"[AUDIT] {msg}")


def audit_logic():
    log("Starting Logic Audit...")

    # 1. Create Candidate
    candidate_data = {
        "name": "Audit Target",
        "company": "Test Corp",
        "email": "target@test.com",
        "linkedin_url": "https://linkedin.com/in/test",
        "match_score": 88,
    }
    log(f"Creating Candidate: {candidate_data['name']}")
    res = requests.post(f"{API_URL}/candidates", json=candidate_data)
    if res.status_code != 200:
        log(f"FAILED: Create Candidate ({res.status_code})")
        return
    candidate = res.json()
    c_id = candidate["id"]
    log(f"Candidate Created ID: {c_id}")

    # 2. Verify Stats (People Found)
    res = requests.get(f"{API_URL}/stats")
    stats_before = res.json()
    log(f"Stats Before: {stats_before}")
    # Note: Stats people_found count all candidates, so it should be consumed.

    # 3. Generate Draft (The Critical Test)
    log("Generating Draft...")
    res = requests.post(f"{API_URL}/generate-draft", params={"candidate_id": c_id})
    if res.status_code != 200:
        log(f"FAILED: Generate Draft ({res.text})")
        return
    draft = res.json()
    log("Draft Generated!")
    print("-" * 40)
    print(draft["body"])
    print("-" * 40)

    # CHECK LOGIC: Does it have user context?
    # Since we know settings aren't connected, we expect Generic sign-off.
    if (
        "Best regards," in draft["body"] and "Siddharth" not in draft["body"]
    ):  # Assuming 'Siddharth' is user
        log("ISSUE IDENTIFIED: Draft signature is generic. Settings not connected.")
    else:
        log("Draft seems personalized ( Unexpected?)")

    # 4. Send Email
    log("Sending Email...")
    send_req = {
        "candidate_id": c_id,
        "to": candidate["email"],
        "subject": draft["subject"],
        "body": draft["body"],
    }
    res = requests.post(f"{API_URL}/send-email", json=send_req)
    if res.status_code != 200:
        log(f"FAILED: Send Email ({res.text})")
    else:
        log("Email Sent Successfully")

    # 5. Verify Stats Update (Emails Sent)
    res = requests.get(f"{API_URL}/stats")
    stats_after = res.json()

    if stats_after["emails_sent"] > stats_before["emails_sent"]:
        log("SUCCESS: 'Emails Sent' stat incremented.")
    else:
        log(
            f"ISSUE IDENTIFIED: Stats did not update. Before: {stats_before['emails_sent']}, After: {stats_after['emails_sent']}"
        )


if __name__ == "__main__":
    try:
        audit_logic()
    except Exception as e:
        log(f"Audit Crashed: {e}")
