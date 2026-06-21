import aiohttp
from bs4 import BeautifulSoup

async def run_onion_osint(domain: str, send_log, report_results):
    if not domain.endswith(".onion"):
        return
        
    await send_log(f"[+] Starting DARKWEB ONION PING for: {domain}")
    
    # We use a Tor2Web proxy to check if the onion is alive without needing a local Tor daemon
    proxy_url = f"https://{domain}.ly"
    
    try:
        async with aiohttp.ClientSession() as session:
            await send_log(f"[ONION] Attempting proxy tunnel via Tor2Web...")
            async with session.get(proxy_url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    title = soup.title.string if soup.title else "No Title"
                    
                    await send_log(f"[!] ONION NODE IS ALIVE!")
                    await send_log(f"[ONION] Hidden Service Title: {title.strip()}")
                    
                    await report_results("Darknet (Onion)", {
                        "onion_address": domain,
                        "status": "Online",
                        "page_title": title.strip()
                    })
                else:
                    await send_log(f"[-] ONION: Node is offline or proxy failed (Status {response.status})")
    except Exception as e:
        await send_log(f"[-] ONION: Node is currently unreachable.")
