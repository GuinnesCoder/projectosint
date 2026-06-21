import aiohttp

async def run_pastebin_osint(query: str, send_log, report_results):
    await send_log(f"[+] Starting PASTE DUMP Search for: {query}")
    
    # Try multiple paste search endpoints (psbdmp is often down)
    endpoints = [
        f"https://psbdmp.ws/api/v3/search/{query}",
        f"https://api.psbdmp.cc/v3/search/{query}",
    ]
    
    for url in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=8) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if isinstance(data, list) and len(data) > 0:
                            await send_log(f"[!] PASTEBIN: Found {len(data)} paste(s) mentioning target!")
                            
                            paste_ids = []
                            for paste in data[:10]:
                                pid = paste.get("id", "")
                                time = paste.get("time", "")
                                tags = paste.get("tags", "")
                                await send_log(f"[PASTEBIN] Paste ID: {pid} | Time: {time}")
                                paste_ids.append({"id": pid, "time": time, "tags": tags})
                            
                            await report_results("Darkweb (Paste Dumps)", {
                                "query": query,
                                "total_pastes_found": len(data),
                                "pastes": paste_ids
                            })
                            return
                        else:
                            await send_log("[-] PASTEBIN: No paste dumps found for this target.")
                            return
                    elif response.status == 404:
                        await send_log("[-] PASTEBIN: No results in paste dump database.")
                        return
        except (aiohttp.ClientConnectorError, aiohttp.ClientError):
            continue  # Try next endpoint silently
        except Exception:
            continue
    
    await send_log("[-] PASTEBIN: All paste dump endpoints are currently unreachable.")
