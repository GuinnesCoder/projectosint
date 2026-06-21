import os
import aiohttp

async def run_greynoise(ip: str, send_log, report_results):
    api_key = os.getenv("GREYNOISE_API_KEY")
    if not api_key:
        await send_log("[!] GREYNOISE: Missing API Key.")
        return

    await send_log(f"[+] Starting GREYNOISE noise/scanner detection for: {ip}")
    
    url = f"https://api.greynoise.io/v3/community/{ip}"
    headers = {
        'Accept': 'application/json',
        'key': api_key
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    is_noise = data.get('noise', False)
                    riot = data.get('riot', False) # Rule It Out (benign services)
                    name = data.get('name', 'Unknown')
                    classification = data.get('classification', 'unknown')
                    
                    if is_noise:
                        await send_log(f"[!] GREYNOISE: Target is a known MASS SCANNER (Classification: {classification})")
                    elif riot:
                        await send_log(f"[ABUSEIPDB] Target is a known BENIGN SERVICE (RIoT): {name}")
                    else:
                        await send_log(f"[GREYNOISE] Target is not internet background noise.")

                    await report_results("Threat Intel (GreyNoise)", {
                        "is_noise": is_noise,
                        "is_riot": riot,
                        "classification": classification,
                        "actor_name": name,
                        "last_seen": data.get("last_seen")
                    })
                elif response.status == 404:
                    await send_log(f"[GREYNOISE] Target has not been observed scanning the internet.")
                else:
                    await send_log(f"[-] GREYNOISE Error: API returned status {response.status}")
    except Exception as e:
        await send_log(f"[!] GREYNOISE Exception: {str(e)}")
