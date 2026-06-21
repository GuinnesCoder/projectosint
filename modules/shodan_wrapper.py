import os
import aiohttp

async def run_shodan(ip: str, send_log, report_results):
    api_key = os.getenv("SHODAN_API_KEY")
    if not api_key:
        await send_log("[!] SHODAN: Missing API Key.")
        return

    await send_log(f"[+] Starting SHODAN deep infrastructure scan for: {ip}")
    
    url = f"https://api.shodan.io/shodan/host/{ip}"
    params = {
        'key': api_key
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    ports = data.get('ports', [])
                    hostnames = data.get('hostnames', [])
                    vulns = data.get('vulns', [])
                    os_name = data.get('os', 'Unknown OS')
                    
                    await send_log(f"[SHODAN] Host OS: {os_name}")
                    if hostnames:
                        await send_log(f"[SHODAN] Associated Hostnames: {', '.join(hostnames)}")
                    
                    if vulns:
                        await send_log(f"[!] SHODAN: TARGET IS VULNERABLE! Found {len(vulns)} CVEs!")
                        await send_log(f"[!] CVEs: {', '.join(vulns[:5])}...")
                        
                    await report_results("Threat Intel (Shodan)", {
                        "os": os_name,
                        "ports": ports,
                        "hostnames": hostnames,
                        "vulnerabilities": vulns[:15], # limit dict size
                        "isp": data.get("isp"),
                        "org": data.get("org")
                    })
                elif response.status == 404:
                    await send_log(f"[-] SHODAN: IP is not indexed in Shodan database.")
                elif response.status == 401:
                    await send_log(f"[-] SHODAN: Invalid API Key.")
                else:
                    await send_log(f"[-] SHODAN Error: API returned status {response.status}")
    except Exception as e:
        await send_log(f"[!] SHODAN Exception: {str(e)}")
