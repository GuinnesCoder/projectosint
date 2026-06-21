import os
import aiohttp

async def run_abuseipdb(ip: str, send_log, report_results):
    api_key = os.getenv("ABUSEIPDB_API_KEY")
    if not api_key:
        await send_log("[!] ABUSEIPDB: Missing API Key.")
        return

    await send_log(f"[+] Starting AbuseIPDB threat scan for: {ip}")
    
    url = 'https://api.abuseipdb.com/api/v2/check'
    headers = {
        'Accept': 'application/json',
        'Key': api_key
    }
    params = {
        'ipAddress': ip,
        'maxAgeInDays': '90'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    info = data.get('data', {})
                    
                    score = info.get('abuseConfidenceScore', 0)
                    reports = info.get('totalReports', 0)
                    isp = info.get('isp', 'Unknown')
                    
                    await send_log(f"[ABUSEIPDB] Target ISP: {isp}")
                    if reports > 0:
                        await send_log(f"[!] ABUSEIPDB: Found {reports} malicious reports! Confidence score: {score}%")
                    else:
                        await send_log(f"[ABUSEIPDB] No malicious reports found (Score: 0%).")

                    await report_results("Threat Intel (AbuseIPDB)", {
                        "isp": isp,
                        "usageType": info.get("usageType"),
                        "domain": info.get("domain"),
                        "totalReports": reports,
                        "abuseConfidenceScore": score
                    })
                else:
                    await send_log(f"[-] ABUSEIPDB Error: API returned status {response.status}")
    except Exception as e:
        await send_log(f"[!] ABUSEIPDB Exception: {str(e)}")
