from backend.services.email_generator import EmailGenerator
from backend.services.hr_extractor import (
    parse_linkedin_title,
    extract_role_from_post_body,
    parse_linkedin_post_url
)
from backend.services.crawler import Crawler

def test_email_generator_clean_name():
    name = "John Doe (HR)"
    cleaned = EmailGenerator.clean_name(name)
    assert cleaned["first"] == "john"
    assert cleaned["last"] == "doe"

def test_email_generator_guess_domain():
    domain = EmailGenerator.guess_domain("Google Inc.")
    assert domain == "google.com"

def test_email_generator_generate_patterns():
    patterns = EmailGenerator.generate_patterns("Jane Smith", "Google Inc.")
    assert any("jane.smith@google.com" == p["email"] for p in patterns)
    assert any("janesmith@google.com" == p["email"] for p in patterns)
    assert any("jane@google.com" == p["email"] for p in patterns)

def test_parse_linkedin_title():
    info = parse_linkedin_title("John Doe - Senior Engineer - at - Antigravity")
    assert info["role"] == "Senior Engineer"
    assert info["company"] == "Antigravity"
    
def test_extract_role_from_post_body():
    role = extract_role_from_post_body("We are looking for a Product Manager to join us.")
    assert "product manager" in role.lower()

def test_parse_linkedin_post_url():
    url = "https://www.linkedin.com/posts/john-doe_we-are-hiring-a-senior-engineer-activity-123456789"
    role = parse_linkedin_post_url(url)
    assert role["name"] == "John Doe"

def test_crawler_get_queries_for_role():
    c = Crawler()
    queries = c.get_queries_for_role("Software Engineer")
    assert len(queries) > 0
    assert any("Software Engineer" in q for q in queries)

def test_crawler_get_broad_queries():
    c = Crawler()
    queries = c.get_broad_queries("Software Engineer")
    assert len(queries) > 0
