import aiohttp

async def run_fns_osint(inn: str, send_log, report_results):
    await send_log(f"[+] Starting FNS / BUSINESS Intelligence for INN: {inn}")
    
    # DADATA suggestions API (free tier, no key needed for basic lookup)
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {"query": inn}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    suggestions = data.get("suggestions", [])
                    
                    if suggestions:
                        company = suggestions[0]
                        value = company.get("value", "")
                        comp_data = company.get("data", {})
                        
                        status = comp_data.get("state", {}).get("status", "Unknown")
                        director = comp_data.get("management", {}).get("name", "Hidden")
                        address = comp_data.get("address", {}).get("value", "Hidden")
                        ogrn = comp_data.get("ogrn", "")
                        kpp = comp_data.get("kpp", "")
                        
                        await send_log(f"[FNS] Entity Found: {value}")
                        await send_log(f"[FNS] Status: {status}")
                        await send_log(f"[FNS] Director / CEO: {director}")
                        await send_log(f"[FNS] Legal Address: {address}")
                        
                        await report_results("Business Intel (FNS/INN)", {
                            "inn": inn,
                            "company_name": value,
                            "status": status,
                            "director": director,
                            "address": address,
                            "ogrn": ogrn,
                            "kpp": kpp
                        })
                    else:
                        await send_log("[-] FNS: No business entity found for this INN.")
                elif response.status == 403:
                    await send_log("[-] FNS: Access denied (API token may be required).")
                else:
                    await send_log(f"[-] FNS Error: API returned {response.status}")
    except Exception as e:
        await send_log(f"[!] FNS Exception: {str(e)}")
