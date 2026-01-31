import requests
import io
    
API_URL = "http://localhost:8000"

def test_linkedin():
    print("\n--- Testing LinkedIn Verification ---")
    valid_url = "https://www.linkedin.com/in/siddharth"
    invalid_url = "https://facebook.com/siddharth"
    malformed_url = "linkedin.com/in/valid-format" # Should be valid with our regex

    res1 = requests.post(f"{API_URL}/verify-linkedin", params={"url": valid_url})
    print(f"Valid URL: {res1.json()}")
    
    res2 = requests.post(f"{API_URL}/verify-linkedin", params={"url": invalid_url})
    print(f"Invalid URL: {res2.json()}")
    
    res3 = requests.post(f"{API_URL}/verify-linkedin", params={"url": malformed_url})
    print(f"Malformed URL: {res3.json()}")

def test_pdf_upload():
    print("\n--- Testing PDF Upload ---")
    # Create a dummy PDF content
    # Note: Creating a real valid PDF binary is complex in a simple string, 
    # so we will test the graceful error handling or text file fallback first 
    # 3. Upload Resume (Trigger AI)
    print("Testing Upload...")
    text_content = """
    John Doe
    Software Engineer
    Summary: Experienced developer with expertise in Python, JavaScript, React, and AWS. 
    Looking for backend roles using FastAPI or Django. 
    Previously worked at Tech Corp using Docker and Kubernetes.
    This text is long enough to trigger the AI extraction logic which requires more than 50 characters.
    """
    files = {'file': ('resume.txt', text_content)}
    try:
        res = requests.post(f"{API_URL}/brain/upload", files=files)
        print(f"Upload Status: {res.status_code}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"Upload Failed: {e}")

if __name__ == "__main__":
    try:
        test_linkedin()
        test_pdf_upload()
    except Exception as e:
        print(f"Test Failed: {e}")
