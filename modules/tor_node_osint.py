import aiohttp

async def run_tor_node_osint(ip: str, send_log, report_results):
    await send_log(f"[+] Starting TOR EXIT NODE check for: {ip}")
    
    url = "https://check.torproject.org/torbulkexitlist"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    text = await response.text()
                    exit_nodes = set(text.strip().split("\n"))
                    
                    if ip in exit_nodes:
                        await send_log(f"[!] TOR: IP {ip} IS a known Tor Exit Node!")
                        await send_log("[!] TOR: Traffic from this IP may be anonymized.")
                        await report_results("DarkWeb (Tor Exit Node)", {
                            "ip": ip,
                            "is_tor_exit": True,
                            "total_known_exits": len(exit_nodes)
                        })
                    else:
                        await send_log(f"[-] TOR: IP is NOT a known Tor exit node.")
                else:
                    await send_log(f"[-] TOR: Tor Project API returned {response.status}")
    except Exception as e:
        await send_log(f"[!] TOR Exception: {str(e)}")
