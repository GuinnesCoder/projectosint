import aiohttp

async def run_wayback_osint(domain: str, send_log, report_results):
    await send_log(f"[+] Starting WAYBACK MACHINE analysis for: {domain}")
    
    url = f"https://archive.org/wayback/available?url={domain}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    snapshots = data.get('archived_snapshots', {})
                    closest = snapshots.get('closest', {})
                    
                    if closest and closest.get('available'):
                        timestamp = closest.get('timestamp')
                        snap_url = closest.get('url')
                        await send_log(f"[WAYBACK] Domain has historical snapshots!")
                        await send_log(f"[WAYBACK] Closest snapshot recorded at: {timestamp}")
                        
                        await report_results("Historical Web (Archive)", {
                            "domain": domain,
                            "has_snapshots": True,
                            "closest_snapshot_time": timestamp,
                            "snapshot_url": snap_url
                        })
                    else:
                        await send_log("[-] WAYBACK: No historical snapshots found in Archive.org.")
                else:
                    await send_log(f"[-] WAYBACK Error: Archive.org API returned status {response.status}")
    except Exception as e:
        await send_log(f"[!] WAYBACK Exception: {str(e)}")
