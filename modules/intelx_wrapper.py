import aiohttp
import os
import asyncio

async def run_intelx(query: str, send_log, report_results):
    api_key = os.getenv("INTELX_API_KEY", "")
    await send_log(f"[+] Starting INTELX Data Breach Search for: {query}")
    
    if not api_key:
        await send_log("[!] INTELX API KEY is missing. Skipping module.")
        await report_results("Darkweb Leaks (IntelX)", {"error": "Missing API Key"})
        return
        
    headers = {"x-key": api_key, "User-Agent": "OSINT-App-v1"}
    base_url = "https://free.intelx.io"
    results = {}
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            # Step 1: Initialize the search
            search_url = f"{base_url}/intelligent/search"
            payload = {
                "term": query,
                "maxresults": 10,
                "media": 0,
                "sort": 2,
                "terminate": []
            }
            
            await send_log(f"[INTELX] Initializing search...")
            async with session.post(search_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    search_id = data.get("id")
                    await send_log(f"[INTELX] Search ID obtained: {search_id}")
                    
                    if not search_id:
                        await send_log("[!] IntelX returned no search ID.")
                        await report_results("Darkweb Leaks (IntelX)", {"error": "No Search ID"})
                        return
                        
                    # Step 2: Retrieve results (sleep briefly to let IntelX gather them)
                    await asyncio.sleep(2)
                    results_url = f"{base_url}/intelligent/search/result?id={search_id}&limit=10"
                    
                    async with session.get(results_url) as res_resp:
                        if res_resp.status == 200:
                            res_data = await res_resp.json()
                            records = res_data.get("records", []) or []
                            await send_log(f"[INTELX] Found {len(records)} records.")
                            
                            leak_names = [rec.get('name') for rec in records if rec.get('name')]
                            results["leaks"] = leak_names
                            
                            for leak in leak_names[:5]:
                                await send_log(f"[INTELX] LEAK FOUND: {leak}")
                        else:
                            await send_log(f"[!] IntelX Result Error: HTTP {res_resp.status}")
                else:
                    await send_log(f"[!] IntelX Initialization Error: HTTP {resp.status}")
                    
    except Exception as e:
        await send_log(f"[!] Exception during IntelX: {str(e)}")
        results["error"] = str(e)
        
    await send_log(f"[-] INTELX search completed.")
    await report_results("Darkweb Leaks (IntelX)", results)
