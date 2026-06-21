import aiohttp

async def run_mac_osint(mac: str, send_log, report_results):
    await send_log(f"[+] Starting BSSID/MAC Hardware Tracker for: {mac}")
    
    # MacVendors API
    url = f"https://api.macvendors.com/{mac}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    vendor = await response.text()
                    await send_log(f"[MAC/BSSID] Hardware Vendor Identified: {vendor}")
                    
                    await report_results("Hardware (MAC)", {
                        "mac_address": mac,
                        "vendor_name": vendor
                    })
                elif response.status == 404:
                    await send_log(f"[-] MAC/BSSID: Block not assigned to any known vendor in IEEE registry.")
                else:
                    await send_log(f"[-] MAC Error: Registry returned status {response.status}")
    except Exception as e:
        await send_log(f"[!] MAC Exception: {str(e)}")
