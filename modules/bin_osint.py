import aiohttp

async def run_bin_osint(bin_code: str, send_log, report_results):
    await send_log(f"[+] Starting CREDIT CARD BIN Lookup for: {bin_code[:6]}****")
    
    url = f"https://lookup.binlist.net/{bin_code[:6]}"
    
    try:
        async with aiohttp.ClientSession(headers={"Accept-Version": "3"}) as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    scheme = data.get("scheme", "Unknown").upper()
                    card_type = data.get("type", "Unknown")
                    brand = data.get("brand", "Unknown")
                    bank = data.get("bank", {})
                    bank_name = bank.get("name", "Unknown")
                    country = data.get("country", {})
                    country_name = country.get("name", "Unknown")
                    
                    await send_log(f"[BIN] Card Network: {scheme}")
                    await send_log(f"[BIN] Card Type: {card_type} / {brand}")
                    await send_log(f"[BIN] Issuing Bank: {bank_name}")
                    await send_log(f"[BIN] Country: {country_name}")
                    
                    await report_results("Finance (Card BIN)", {
                        "bin": bin_code[:6],
                        "network": scheme,
                        "type": card_type,
                        "brand": brand,
                        "bank": bank_name,
                        "country": country_name,
                        "prepaid": data.get("prepaid")
                    })
                elif response.status == 404:
                    await send_log("[-] BIN: Card prefix not found in BIN database.")
                elif response.status == 429:
                    await send_log("[-] BIN: Rate limit exceeded. Try again later.")
                else:
                    await send_log(f"[-] BIN Error: API returned {response.status}")
    except Exception as e:
        await send_log(f"[!] BIN Exception: {str(e)}")
