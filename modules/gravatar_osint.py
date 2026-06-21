import aiohttp
import hashlib

async def run_gravatar_osint(email: str, send_log, report_results):
    await send_log(f"[+] Starting DIGITAL FOOTPRINT Hash resolving for: {email}")
    
    email_hash = hashlib.md5(email.lower().strip().encode('utf-8')).hexdigest()
    url = f"https://en.gravatar.com/{email_hash}.json"
    
    try:
        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
            async with session.get(url, timeout=8) as response:
                if response.status == 200:
                    data = await response.json()
                    entry = data.get('entry', [])
                    
                    if entry:
                        profile = entry[0]
                        username = profile.get('preferredUsername')
                        name = profile.get('name', {}).get('formatted')
                        photos = profile.get('photos', [])
                        
                        await send_log("[GRAVATAR] Email mapped to Gravatar network!")
                        if username:
                            await send_log(f"[GRAVATAR] Shadow Username: {username}")
                        if name:
                            await send_log(f"[GRAVATAR] Hidden Name: {name}")
                        
                        avatar = photos[0].get('value') if photos else None
                            
                        await report_results("Shadow Profile (Gravatar)", {
                            "username": username,
                            "display_name": name,
                            "avatar_url": avatar,
                            "profile_url": profile.get("profileUrl")
                        })
                elif response.status == 404:
                    await send_log("[-] GRAVATAR: No hidden avatar profile found for this email.")
                else:
                    await send_log(f"[-] GRAVATAR Error: Server returned {response.status}")
    except Exception as e:
        await send_log(f"[!] GRAVATAR Exception: {str(e)}")
