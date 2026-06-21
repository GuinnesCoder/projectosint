import aiohttp

async def run_twitch_osint(username: str, send_log, report_results):
    await send_log(f"[+] Starting TWITCH Tracker for: {username}")
    
    # We use a free 3rd party decapi endpoint for Twitch metadata to avoid needing Twitch API Tokens
    url = f"https://decapi.me/twitch/creation/{username}"
    url_avatar = f"https://decapi.me/twitch/avatar/{username}"
    url_accountage = f"https://decapi.me/twitch/accountage/{username}"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Check if user exists by checking creation date
            async with session.get(url, timeout=10) as response:
                creation = await response.text()
                
                if "User not found" in creation or "Twitch API error" in creation:
                    await send_log("[-] TWITCH: Account not found.")
                    return
                    
                await send_log(f"[TWITCH] Target Streaming profile located!")
                await send_log(f"[TWITCH] Created: {creation}")
                
            async with session.get(url_avatar, timeout=5) as resp_ava:
                avatar = await resp_ava.text() if resp_ava.status == 200 else None
                
            async with session.get(url_accountage, timeout=5) as resp_age:
                age = await resp_age.text() if resp_age.status == 200 else None
                if age:
                    await send_log(f"[TWITCH] Account Age: {age}")
                    
            await report_results("Gaming (Twitch)", {
                "username": username,
                "creation_date": creation.strip(),
                "account_age": age.strip() if age else "Unknown",
                "avatar_url": avatar.strip() if avatar and "http" in avatar else None
            })
    except Exception as e:
        await send_log(f"[!] TWITCH Exception: {str(e)}")
