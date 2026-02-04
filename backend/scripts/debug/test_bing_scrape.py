import requests
from bs4 import BeautifulSoup

def test_bing():
    query = 'site:linkedin.com/in "Frontend Developer"'
    url = f"https://www.bing.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Testing Bing Scrape for: {query}")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Try new selector approach
            results = soup.select('li.b_algo')
            print(f"Found {len(results)} results (li.b_algo)")
            
            if not results:
                 print("Trying H2 selector...")
                 h2s = soup.select('h2')
                 print(f"Found {len(h2s)} h2 tags")
                 print("\n--- HTML DUMP START ---")
                 print(soup.prettify()[:1000])
                 print("--- HTML DUMP END ---")
            else:
                for res in results[:3]:
                    h2 = res.select_one('h2 a')
                    if h2:
                        print(f"Title: {h2.get_text()}")
                        print(f"URL: {h2['href']}")
        else:
            print("Block/Error from Bing")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bing()
