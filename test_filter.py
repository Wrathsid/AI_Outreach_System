import re
import time

def parse_time_filter(url: str, snippet: str, max_days: int = 7) -> bool:
    # 1. Check LinkedIn Activity ID (Guarantees absolute timestamp)
    match = re.search(r'activity-(\d{19})', url)
    if match:
        activity_id = int(match.group(1))
        timestamp_ms = activity_id >> 22
        current_time_ms = int(time.time() * 1000)
        age_days = (current_time_ms - timestamp_ms) / (1000 * 60 * 60 * 24)
        if age_days > max_days:
            return False
            
    # 2. Check Snippet String for old dates (e.g. "4mo \u2022", "1yr \u2022", "2 yrs", "3 months ago")
    snippet_lower = snippet.lower()
    
    # Common LinkedIn prefixes in snippets: "4mo \u2022", "1yr \u2022", "1 yr", "month"
    bad_patterns = [
        r'\d+\s*mo\b',
        r'\d+\s*mos\b',
        r'\d+\s*month',
        r'\d+\s*yr\b',
        r'\d+\s*yrs\b',
        r'\d+\s*year'
    ]
    
    for pattern in bad_patterns:
        if re.search(pattern, snippet_lower):
            return False
            
    return True

url = "https://www.linkedin.com/posts/username_hiring-react-developer-activity-7434916116767870977-Y2n0"
print(parse_time_filter(url, "4d • Every recruiter runs a")) # true
print(parse_time_filter(url, "4mo • Every recruiter runs a")) # false
print(parse_time_filter("nourl", "1yr • Web developer needed")) # false
print(parse_time_filter("nourl", "3d • We are hiring")) # true
print(parse_time_filter("nourl", "1w • We are hiring")) # true
