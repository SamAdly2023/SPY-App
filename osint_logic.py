import requests
from googlesearch import search as gsearch
import whois
import socket
import concurrent.futures
from urllib.parse import urlparse

# Configuration for Social Media Checks
SOCIAL_SITES = [
    {"name": "Twitter", "url": "https://twitter.com/{}", "check_status": 200},
    {"name": "Facebook", "url": "https://www.facebook.com/{}", "check_status": 200},
    {"name": "Instagram", "url": "https://www.instagram.com/{}", "check_status": 200},
    {"name": "GitHub", "url": "https://github.com/{}", "check_status": 200},
    {"name": "Reddit", "url": "https://www.reddit.com/user/{}", "check_status": 200},
    {"name": "Pinterest", "url": "https://www.pinterest.com/{}", "check_status": 200},
    {"name": "TikTok", "url": "https://www.tiktok.com/@{}", "check_status": 200},
    {"name": "Medium", "url": "https://medium.com/@{}", "check_status": 200},
    {"name": "YouTube", "url": "https://www.youtube.com/@{}", "check_status": 200},
    {"name": "Telegram", "url": "https://t.me/{}", "check_status": 200}
]

def check_username(site, username):
    """Checks if a username exists on a specific site."""
    url = site["url"].format(username)
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == site["check_status"]:
            # Some sites return 200 even if user not found (soft 404), but for simple demo this is okay.
            # Enhancements would involve checking page content.
            return {
                "title": f"{site['name']} Profile: {username}",
                "link": url,
                "type": site["name"],
                "image": "" 
            }
    except:
        pass
    return None

def run_username_search(username):
    """Runs username checks in parallel."""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_site = {executor.submit(check_username, site, username): site for site in SOCIAL_SITES}
        for future in concurrent.futures.as_completed(future_to_site):
            data = future.result()
            if data:
                results.append(data)
    return results

def run_google_search(query, num_results=10):
    """Performs a Google search."""
    results = []
    try:
        # advanced=True returns Result objects with title, url, description
        for res in gsearch(query, num_results=num_results, advanced=True):
            # Determine type based on URL
            site_type = "Websites"
            domain = urlparse(res.url).netloc.lower()
            
            if "twitter.com" in domain or "x.com" in domain: site_type = "Twitter"
            elif "facebook.com" in domain: site_type = "Facebook"
            elif "linkedin.com" in domain: site_type = "LinkedIn"
            elif "instagram.com" in domain: site_type = "Instagram"
            elif "youtube.com" in domain: site_type = "YouTube"
            
            results.append({
                "title": res.title,
                "link": res.url,
                "type": site_type,
                "image": ""
            })
    except Exception as e:
        print(f"Google Search Error: {e}")
    return results

def run_whois_lookup(domain):
    """Performs a WHOIS lookup if the query looks like a domain."""
    results = []
    try:
        w = whois.whois(domain)
        if w.domain_name:
            # Handle list or string return types from whois
            d_name = w.domain_name[0] if isinstance(w.domain_name, list) else w.domain_name
            registrar = w.registrar
            
            results.append({
                "title": f"WHOIS: {d_name}",
                "link": f"https://who.is/whois/{domain}",
                "type": "Websites",
                "image": ""
            })
            
            if w.emails:
                emails = w.emails if isinstance(w.emails, list) else [w.emails]
                for email in emails:
                    results.append({
                        "title": f"Registrant Email: {email}",
                        "link": f"mailto:{email}",
                        "type": "Emails",
                        "image": ""
                    })
    except:
        pass # Not a domain or lookup failed
    return results

def perform_osint_scan(query, depth=2):
    """Main entry point for the scan."""
    all_results = []
    
    # 1. Username Search (assuming query might be a username)
    # We strip spaces for username check
    username_query = query.replace(" ", "")
    print(f"Checking username: {username_query}")
    all_results.extend(run_username_search(username_query))
    
    # 2. Google Search
    # Depth maps to number of results roughly
    num_google = int(depth) * 5 
    print(f"Google searching: {query}")
    all_results.extend(run_google_search(query, num_results=num_google))
    
    # 3. Domain Check (if it looks like a domain)
    if "." in query and " " not in query:
        print(f"Checking domain: {query}")
        all_results.extend(run_whois_lookup(query))
        
    return all_results
