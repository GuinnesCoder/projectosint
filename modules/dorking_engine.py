import aiohttp
from bs4 import BeautifulSoup
import re
import urllib.parse

async def run_dorking(query: str, send_log, report_results):
    await send_log(f"[+] Starting DORKING ENGINE for cross-platform connections on: {query}")
    
    # Exact match search to avoid noise
    search_query = f'"{query}"'
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    data = {"q": search_query}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    urls = soup.find_all('a', class_='result__url')
                    
                    found_links = []
                    linked_platforms = set()
                    
                    # Shadow Identity & Social Linkage platforms
                    platforms_to_watch = ["vk.com", "steamcommunity.com", "github.com", "instagram.com", "t.me", "facebook.com", "reddit.com", "twitter.com", "x.com", "pastebin.com", "pikabu.ru"]
                    
                    for u in urls:
                        link = u.get('href', '')
                        if not link:
                            continue
                            
                        # Resolve DDG redirect URL if necessary
                        if 'uddg=' in link:
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                            if 'uddg' in parsed:
                                link = parsed['uddg'][0]
                                
                        # Only grab unique targeted footprint URLs
                        for p in platforms_to_watch:
                            if p in link and link not in found_links:
                                linked_platforms.add(p)
                                found_links.append(link)
                                
                    if found_links:
                        await send_log(f"[DORKING] Found {len(found_links)} targeted cross-platform links!")
                        await send_log(f"[DORKING] Platforms identified: {', '.join(linked_platforms)}")
                        
                        await report_results("Entity Linkage (Dorking)", {
                            "query": query,
                            "related_links": found_links[:10],
                            "platforms": list(linked_platforms)
                        })
                    else:
                        await send_log(f"[-] DORKING: No obvious linked platforms extracted from public web.")
                else:
                    await send_log(f"[-] DORKING Error: DuckDuckGo returned {response.status}. Bot protection likely triggered.")
    except Exception as e:
        await send_log(f"[!] DORKING Exception: {str(e)}")
