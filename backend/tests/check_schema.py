import requests

# Hardcoded from main.py or env?
# I'll rely on verify_endpoints.py structure but I need the keys.
# Actually main.py has them. I'll ask main.py to print them or just use the local file if I can read it.
# Check main.py lines 20-40 for keys.

API_URL = "http://localhost:8000"


def check_schema():
    print("Checking Brain Context Schema via API...")
    # This invokes get_brain_context
    try:
        res = requests.get(f"{API_URL}/brain")
        data = res.json()
        print(f"Keys received: {list(data.keys())}")
        if "extracted_skills" in data:
            print("extracted_skills column EXISTS in API response")
        else:
            print("extracted_skills column MISSING in API response")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_schema()
