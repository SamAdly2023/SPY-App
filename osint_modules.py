import requests
from duckduckgo_search import DDGS
from urllib.parse import urlparse

def perform_google_search(query, num_results=10):
    """
    Performs a DuckDuckGo search and returns a list of results.
    """
    results = []
    try:
        with DDGS() as ddgs:
            # ddgs.text() returns a generator of results
            search_gen = ddgs.text(query, max_results=int(num_results))
            for r in search_gen:
                results.append({
                    "title": r.get('title', 'No Title'),
                    "link": r.get('href', ''),
                    "type": "Websites", # Default type
                    "image": ""
                })
    except Exception as e:
        print(f"Error in Search: {e}")
    return results

def check_social_media(username):
    """
    Checks for the existence of a username on popular social media platforms.
    """
    social_networks = {
        "Twitter": "https://twitter.com/{}",
        "Instagram": "https://www.instagram.com/{}",
        "Facebook": "https://www.facebook.com/{}",
        "GitHub": "https://github.com/{}",
        "Reddit": "https://www.reddit.com/user/{}",
        "TikTok": "https://www.tiktok.com/@{}",
        "Medium": "https://medium.com/@{}",
        "Pinterest": "https://www.pinterest.com/{}"
    }
    
    found_accounts = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for site, url_template in social_networks.items():
        url = url_template.format(username)
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                # Basic check: Some sites return 200 even if user doesn't exist but show "Not Found" text.
                # For a simple version, status code 200 is a strong indicator.
                # We can refine this with content checks later.
                found_accounts.append({
                    "title": f"{site} Profile",
                    "link": url,
                    "type": site,
                    "image": ""
                })
        except Exception as e:
            print(f"Error checking {site}: {e}")
            
    return found_accounts

def categorize_url(url):
    """
    Helper to categorize a URL based on its domain.
    """
    domain = urlparse(url).netloc.lower()
    if "twitter.com" in domain or "x.com" in domain: return "Twitter"
    if "facebook.com" in domain: return "Facebook"
    if "instagram.com" in domain: return "Instagram"
    if "linkedin.com" in domain: return "LinkedIn"
    if "youtube.com" in domain: return "YouTube"
    if "github.com" in domain: return "GitHub"
    return "Websites"

def run_osint_scan(query, depth):
    """
    Main function to orchestrate the scan.
    """
    results = []
    
    # 1. Check if the query looks like a username (no spaces)
    if " " not in query:
        print(f"Checking username: {query}")
        social_results = check_social_media(query)
        results.extend(social_results)
    
    # 2. Perform Google Search
    print(f"Searching Google for: {query}")
    # Map depth 1-5 to number of results (e.g., 1 page = 10 results)
    num_results = int(depth) * 5 
    google_results = perform_google_search(query, num_results)
    
    # Post-process Google results to fix types
    for res in google_results:
        res['type'] = categorize_url(res['link'])
        results.append(res)
        
    return results
