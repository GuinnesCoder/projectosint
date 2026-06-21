import os
import aiohttp
import base64

async def run_censys(ip: str, send_log, report_results):
    api_id = os.getenv("CENSYS_API_ID")
    api_secret = os.getenv("CENSYS_API_SECRET")
    
    if not api_id or not api_secret:
        await send_log("[!] CENSYS: Missing API Credentials.")
        return

    await send_log(f"[+] Starting CENSYS port/certificate deep scan for: {ip}")
    
    url = f"https://search.censys.io/api/v2/hosts/{ip}"
    auth_string = f"{api_id}:{api_secret}"
    b64_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Basic {b64_auth}'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=12) as response:
                if response.status == 200:
                    data = await response.json()
                    host_info = data.get('result', {})
                    services = host_info.get('services', [])
                    
                    open_ports = [svc.get('port') for svc in services]
                    await send_log(f"[CENSYS] Target is exposing {len(open_ports)} services.")
                    if open_ports:
                        await send_log(f"[CENSYS] Exposed ports: {', '.join(map(str, open_ports[:10]))}")

                    await report_results("Threat Intel (Censys)", {
                        "exposed_ports": open_ports,
                        "autonomous_system": host_info.get("autonomous_system", {}).get("name"),
                        "location": host_info.get("location", {}).get("country")
                    })
                elif response.status == 404:
                    await send_log(f"[-] CENSYS: Target IP not found in recent scans.")
                else:
                    await send_log(f"[-] CENSYS Error: API returned status {response.status}")
    except Exception as e:
        await send_log(f"[!] CENSYS Exception: {str(e)}")
