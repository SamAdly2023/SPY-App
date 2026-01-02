import requests
import whois
import os
from duckduckgo_search import DDGS
from urllib.parse import urlparse

def perform_whois_lookup(domain):
    """
    Performs a Whois lookup for a domain.
    """
    results = []
    try:
        w = whois.whois(domain)
        if w.domain_name:
            # Create a result card for the domain info
            info = f"Registrar: {w.registrar}\nCreation Date: {w.creation_date}\nEmails: {w.emails}"
            results.append({
                "title": f"Whois: {domain}",
                "link": f"https://who.is/whois/{domain}", # Link to external whois
                "type": "Websites",
                "image": "https://cdn-icons-png.flaticon.com/512/2065/2065064.png", # Globe icon
                "details": str(w) # Store full details if needed
            })
    except Exception as e:
        print(f"Error in Whois: {e}")
    return results

def perform_google_search(query, num_results=10):
    """
    Performs a Google Custom Search and returns a list of results.
    Requires GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX environment variables.
    """
    results = []
    
    # Try Google Custom Search first
    api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
    # Use the provided CX as default if not in env
    cx = os.environ.get("GOOGLE_SEARCH_CX", "452d685a5b79d4c2e")
    
    if api_key and cx:
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'q': query,
                'key': api_key,
                'cx': cx,
                'num': num_results
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'items' in data:
                for item in data['items']:
                    image = ""
                    if 'pagemap' in item and 'cse_image' in item['pagemap']:
                        image = item['pagemap']['cse_image'][0].get('src', '')
                        
                    results.append({
                        "title": item.get('title', 'No Title'),
                        "link": item.get('link', ''),
                        "snippet": item.get('snippet', ''),
                        "type": "Websites",
                        "image": image
                    })
                return results # Return immediately if successful
            elif 'error' in data:
                print(f"Google API Error: {data['error']}")
                
        except Exception as e:
            print(f"Error in Google Search: {e}")

    # Fallback to DuckDuckGo if Google fails or keys are missing
    print("Falling back to DuckDuckGo...")
    try:
        with DDGS() as ddgs:
            # ddgs.text() returns a generator of results
            search_gen = ddgs.text(query, max_results=int(num_results))
            for r in search_gen:
                results.append({
                    "title": r.get('title', 'No Title'),
                    "link": r.get('href', ''),
                    "snippet": r.get('body', ''),
                    "type": "Websites", # Default type
                    "image": ""
                })
    except Exception as e:
        print(f"Error in DuckDuckGo Search: {e}")
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
        "Pinterest": "https://www.pinterest.com/{}",
        "LinkedIn": "https://www.linkedin.com/in/{}",
        "SoundCloud": "https://soundcloud.com/{}",
        "Spotify": "https://open.spotify.com/user/{}",
        "Vimeo": "https://vimeo.com/{}",
        "Behance": "https://www.behance.net/{}",
        "Dribbble": "https://dribbble.com/{}",
        "Flickr": "https://www.flickr.com/people/{}",
        "Steam": "https://steamcommunity.com/id/{}",
        "Twitch": "https://www.twitch.tv/{}",
        "Telegram": "https://t.me/{}",
        "Patreon": "https://www.patreon.com/{}",
        "About.me": "https://about.me/{}",
        "Gravatar": "https://en.gravatar.com/{}",
        "SlideShare": "https://www.slideshare.net/{}",
        "DeviantArt": "https://www.deviantart.com/{}",
        "Wattpad": "https://www.wattpad.com/user/{}",
        "ReverbNation": "https://www.reverbnation.com/{}",
        "Gumroad": "https://gumroad.com/{}",
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
    if "reddit.com" in domain: return "Reddit"
    if "tiktok.com" in domain: return "TikTok"
    if "pinterest.com" in domain: return "Pinterest"
    if "t.me" in domain or "telegram.org" in domain: return "Telegram"
    if "medium.com" in domain: return "Medium"
    if "stackoverflow.com" in domain: return "StackOverflow"
    if "whatsapp.com" in domain: return "WhatsApp"
    if "pdf" in url.lower(): return "Documents"
    return "Websites"

def run_osint_scan(query, depth):
    """
    Main function to orchestrate the scan.
    """
    results = []
    
    # Check for Google Search Operators (Advanced Mode)
    # Ref: https://support.google.com/websearch/answer/2466433?hl=en
    # If the user is using operators, we trust their query and don't wrap it in quotes.
    advanced_operators = ['site:', 'intitle:', 'inurl:', 'allintitle:', 'allinurl:', 'filetype:', 'ext:', 'related:', 'OR', 'AND', '-', '"']
    is_advanced = any(op in query for op in advanced_operators)
    
    if is_advanced:
        final_query = query
        print(f"Advanced query detected: {final_query}")
    else:
        # If simple query, enforce exact match for better consistency
        final_query = f'"{query}"'
        print(f"Simple query, applying exact match: {final_query}")
    
    # 1. Check if the query looks like a domain (Only if simple)
    if not is_advanced and "." in query and " " not in query:
        print(f"Checking Whois for: {query}")
        whois_results = perform_whois_lookup(query)
        results.extend(whois_results)

    # 2. Check if the query looks like a username (Only if simple)
    if not is_advanced and " " not in query and "." not in query:
        print(f"Checking username: {query}")
        social_results = check_social_media(query)
        results.extend(social_results)
    
    # 3. Perform General Search
    print(f"Searching Web for: {final_query}")
    num_results = int(depth) * 5 
    google_results = perform_google_search(final_query, num_results)
    for res in google_results:
        res['type'] = categorize_url(res['link'])
        results.append(res)

    # 4. Perform Targeted Social Search (Search Engine Dorking)
    # Only run automated dorks if the user hasn't provided a specific advanced query.
    if not is_advanced:
        print(f"Searching Social Media for: {final_query}")
        
        # Split into groups to ensure diversity in results and better coverage
        social_dorks = [
            f'site:linkedin.com {final_query}',
            f'site:facebook.com OR site:instagram.com {final_query}',
            f'site:twitter.com OR site:x.com OR site:tiktok.com OR site:youtube.com {final_query}',
            f'site:pinterest.com OR site:reddit.com OR site:t.me {final_query}',
            f'site:github.com OR site:gitlab.com OR site:stackoverflow.com {final_query}', # Dev sites
            f'site:pastebin.com OR site:ghostbin.com OR intitle:"index of" {final_query}' # Leaks/Files
        ]

        for dork in social_dorks:
            # Search for each group
            social_search_results = perform_google_search(dork, 10)
            for res in social_search_results:
                res['type'] = categorize_url(res['link'])
                # Avoid duplicates
                if not any(r['link'] == res['link'] for r in results):
                    results.append(res)

    # 5. Perform Document/File Search (Only if not advanced)
    if not is_advanced:
        print(f"Searching Documents for: {final_query}")
        doc_dork = f'filetype:pdf OR filetype:docx OR filetype:xlsx OR filetype:pptx {final_query}'
        doc_results = perform_google_search(doc_dork, 5)
        for res in doc_results:
            res['type'] = "Documents"
            res['image'] = "https://cdn-icons-png.flaticon.com/512/337/337946.png" # Document icon
            if not any(r['link'] == res['link'] for r in results):
                results.append(res)
        res['image'] = "https://cdn-icons-png.flaticon.com/512/337/337946.png" # Document icon
        if not any(r['link'] == res['link'] for r in results):
            results.append(res)
        
    return results
