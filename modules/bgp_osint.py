import aiohttp

async def run_bgp_osint(asn: str, send_log, report_results):
    await send_log(f"[+] Starting BGP / ASN Reconnaissance for: {asn.upper()}")
    
    # Strip "AS" prefix for the API
    asn_num = asn.upper().replace("AS", "")
    url = f"https://api.bgpview.io/asn/{asn_num}"
    prefixes_url = f"https://api.bgpview.io/asn/{asn_num}/prefixes"
    
    try:
        async with aiohttp.ClientSession() as session:
            result = {"asn": f"AS{asn_num}"}
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    info = data.get("data", {})
                    
                    name = info.get("name", "Unknown")
                    desc = info.get("description_full", "")
                    country = info.get("country_code", "Unknown")
                    
                    await send_log(f"[BGP] Organization: {name}")
                    await send_log(f"[BGP] Country: {country}")
                    if desc:
                        await send_log(f"[BGP] Description: {desc[:120]}")
                    
                    result["organization"] = name
                    result["country"] = country
                    result["description"] = desc
                else:
                    await send_log(f"[-] BGP: ASN lookup returned {response.status}")
                    return
            
            async with session.get(prefixes_url, timeout=10) as pref_resp:
                if pref_resp.status == 200:
                    pref_data = await pref_resp.json()
                    v4 = pref_data.get("data", {}).get("ipv4_prefixes", [])
                    v6 = pref_data.get("data", {}).get("ipv6_prefixes", [])
                    
                    v4_list = [p.get("prefix") for p in v4[:20]]
                    
                    await send_log(f"[BGP] IPv4 Prefixes owned: {len(v4)} | IPv6: {len(v6)}")
                    if v4_list:
                        await send_log(f"[BGP] Sample subnets: {', '.join(v4_list[:5])}")
                    
                    result["ipv4_prefixes_count"] = len(v4)
                    result["ipv6_prefixes_count"] = len(v6)
                    result["sample_subnets"] = v4_list[:10]
            
            await report_results("Network (BGP/ASN)", result)
    except Exception as e:
        await send_log(f"[!] BGP Exception: {str(e)}")
