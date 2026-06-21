import aiohttp

async def run_reddit_osint(username: str, send_log, report_results):
    await send_log(f"[+] Starting REDDIT Footprint tracking for: {username}")
    
    url = f"https://www.reddit.com/user/{username}/about.json"
    headers = {"User-Agent": "windows:ghost.osint.tool:v1.0 (by /u/osint)"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    user = data.get('data', {})
                    
                    comment_karma = user.get('comment_karma', 0)
                    link_karma = user.get('link_karma', 0)
                    is_employee = user.get('is_employee', False)
                    has_verified_email = user.get('has_verified_email', False)
                    created_utc = user.get('created_utc')
                    
                    await send_log(f"[REDDIT] Profile mapped successfully!")
                    await send_log(f"[REDDIT] Total Karma: {comment_karma + link_karma}")
                    if has_verified_email:
                        await send_log(f"[REDDIT] Account is linked to a verified email.")
                        
                    await report_results("Social Footprint (Reddit)", {
                        "total_karma": comment_karma + link_karma,
                        "comment_karma": comment_karma,
                        "post_karma": link_karma,
                        "verified_email": has_verified_email,
                        "is_employee": is_employee,
                        "creation_timestamp": created_utc,
                        "avatar": user.get('icon_img')
                    })
                elif response.status == 404:
                    await send_log("[-] REDDIT: Shadow profile not found under this name.")
                elif response.status == 429:
                    await send_log("[-] REDDIT: API Rate limit encountered.")
                else:
                    await send_log(f"[-] REDDIT Error: API returned {response.status}")
    except Exception as e:
        await send_log(f"[!] REDDIT Exception: {str(e)}")
