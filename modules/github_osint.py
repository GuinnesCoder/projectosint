import aiohttp

async def run_github_osint(username: str, send_log, report_results):
    await send_log(f"[+] Starting GITHUB Developer Recon for: {username}")
    
    url = f"https://api.github.com/users/{username}"
    
    try:
        async with aiohttp.ClientSession(headers={"User-Agent": "GHOST-OSINT-App"}) as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    user_type = data.get('type')
                    name = data.get('name')
                    company = data.get('company')
                    location = data.get('location')
                    email = data.get('email')
                    pub_repos = data.get('public_repos', 0)
                    created_at = data.get('created_at')
                    
                    await send_log(f"[GITHUB] Exact Profile Found! Type: {user_type}")
                    if name: await send_log(f"[GITHUB] Name: {name}")
                    if company: await send_log(f"[GITHUB] Organization: {company}")
                    if location: await send_log(f"[GITHUB] Location: {location}")
                    if email: await send_log(f"[!] GITHUB: Exposed Email: {email}")
                    
                    await report_results("Dev Stack (GitHub)", {
                        "name": name,
                        "company": company,
                        "location": location,
                        "public_email": email,
                        "public_repositories": pub_repos,
                        "created_date": created_at,
                        "avatar_url": data.get("avatar_url")
                    })
                elif response.status == 404:
                    await send_log("[-] GITHUB: No user by this name found.")
                elif response.status == 403: # Rate limit
                    await send_log("[-] GITHUB: Rate limit exceeded for public API.")
                else:
                    await send_log(f"[-] GITHUB Error: API returned {response.status}")
    except Exception as e:
        await send_log(f"[!] GITHUB Exception: {str(e)}")
