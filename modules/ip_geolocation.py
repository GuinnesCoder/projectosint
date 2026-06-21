import aiohttp

async def run_ip_geolocation(ip: str, send_log, report_results):
    await send_log(f"[+] Starting IP GEOLOCATION for: {ip}")
    
    url = f"http://ip-api.com/json/{ip}"
    results = {}
    
    try:
        async with aiohttp.ClientSession() as session:
            await send_log(f"[IP-API] Fetching data from {url}")
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    await send_log(f"[IP-API] Received data gracefully.")
                    results = data
                    
                    if data.get('status') == 'success':
                        await send_log(f"[IP-API] City: {data.get('city')}")
                        await send_log(f"[IP-API] ISP: {data.get('isp')}")
                        await send_log(f"[IP-API] ORG: {data.get('org')}")
                    else:
                        await send_log(f"[!] IP-API error: {data.get('message')}")
                else:
                    await send_log(f"[!] IP-API HTTP Error: {response.status}")
    except Exception as e:
        await send_log(f"[!] Exception during IP Geolocate: {str(e)}")
        results["error"] = str(e)
        
    await send_log(f"[-] IP GEOLOCATION completed.")
    await report_results("IP Geolocation (ip-api)", results)
