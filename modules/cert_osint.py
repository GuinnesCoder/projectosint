import aiohttp

async def run_cert_osint(domain: str, send_log, report_results):
    await send_log(f"[+] Starting CTR.SH Subdomain Enumeration for: {domain}")
    
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    subdomains = set()
                    for entry in data:
                        name_value = entry.get('name_value', '')
                        for sub in name_value.split('\n'):
                            if sub and not sub.startswith('*'):
                                subdomains.add(sub)
                                
                    subs_list = list(subdomains)
                    await send_log(f"[CRT.SH] Found {len(subs_list)} hidden/historical subdomains in certificate transparency logs.")
                    
                    if subs_list:
                        await send_log(f"[CRT.SH] Sample: {', '.join(subs_list[:5])}...")
                        await report_results("Infrastructure (Certificates)", {
                            "domain": domain,
                            "total_subdomains_found": len(subs_list),
                            "subdomains": subs_list[:50] # Send up to 50
                        })
                else:
                    await send_log(f"[-] CRT.SH Error: Database returned status {response.status}")
    except Exception as e:
        await send_log(f"[!] CRT.SH Exception: {str(e)}")
