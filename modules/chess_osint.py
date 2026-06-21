import aiohttp

async def run_chess_osint(username: str, send_log, report_results):
    await send_log(f"[+] Starting CHESS.COM Intelligence for: {username}")
    
    url = f"https://api.chess.com/pub/player/{username}"
    stats_url = f"https://api.chess.com/pub/player/{username}/stats"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    name = data.get("name")
                    country_url = data.get("country", "")
                    country = country_url.split("/")[-1] if country_url else "Unknown"
                    location = data.get("location")
                    joined = data.get("joined")
                    last_online = data.get("last_online")
                    
                    await send_log(f"[CHESS] Profile found!")
                    if name:
                        await send_log(f"[CHESS] Real Name: {name}")
                    await send_log(f"[CHESS] Country: {country}")
                    
                    result = {
                        "username": username,
                        "real_name": name,
                        "country": country,
                        "location": location,
                        "joined_timestamp": joined,
                        "last_online_timestamp": last_online,
                        "avatar": data.get("avatar")
                    }
                    
                    # Get ratings
                    async with session.get(stats_url, timeout=10) as stats_resp:
                        if stats_resp.status == 200:
                            stats = await stats_resp.json()
                            rapid = stats.get("chess_rapid", {}).get("last", {}).get("rating")
                            blitz = stats.get("chess_blitz", {}).get("last", {}).get("rating")
                            if rapid:
                                await send_log(f"[CHESS] Rapid Rating: {rapid}")
                                result["rapid_rating"] = rapid
                            if blitz:
                                await send_log(f"[CHESS] Blitz Rating: {blitz}")
                                result["blitz_rating"] = blitz
                    
                    await report_results("Social (Chess.com)", result)
                elif response.status == 404:
                    await send_log("[-] CHESS: Player not found on Chess.com")
                else:
                    await send_log(f"[-] CHESS: API returned {response.status}")
    except Exception as e:
        await send_log(f"[!] CHESS Exception: {str(e)}")
