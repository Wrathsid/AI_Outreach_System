import requests
from bs4 import BeautifulSoup

def test_manual_ddg():
    url = "https://html.duckduckgo.com/html/"
    params = {'q': 'Frontend Developer site:linkedin.com/in'}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://duckduckgo.com/"
    }
    
    print("Requesting manual DDG HTML...")
    try:
        r = requests.post(url, data=params, headers=headers, timeout=10)
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            results = soup.find_all('div', class_='result')
            print(f"Found {len(results)} raw HTML elements.")
            
            if results:
                title = results[0].find('a', class_='result__a').text
                print(f"First Title: {title}")
        else:
            print("Failed to fetch.")
            print(r.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_manual_ddg()
