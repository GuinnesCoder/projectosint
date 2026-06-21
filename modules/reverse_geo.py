import aiohttp
import re

async def run_reverse_geo(query: str, send_log, report_results):
    # Try parsing coordinates "lat, lon"
    coords = re.findall(r"[-+]?\d*\.\d+|\d+", query)
    if len(coords) < 2:
        return
        
    lat, lon = coords[0], coords[1]
    
    await send_log(f"[+] Starting GPS REVERSE-GEOCODING for: {lat}, {lon}")
    
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    headers = {"User-Agent": "OSINT-GHOST-App/1.0"}
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    address = data.get('display_name')
                    address_details = data.get('address', {})
                    
                    if address:
                        await send_log(f"[GEO] Entity Mapped to Physical Address: {address}")
                        
                        await report_results("Physical Location (GPS)", {
                            "coordinates": f"{lat}, {lon}",
                            "full_address": address,
                            "city": address_details.get("city") or address_details.get("town"),
                            "country": address_details.get("country"),
                            "postcode": address_details.get("postcode")
                        })
                else:
                    await send_log(f"[-] GEO Error: Satellite DB returned {response.status}")
    except Exception as e:
        await send_log(f"[!] GEO Exception: {str(e)}")
