import aiohttp

async def run_gitlab_osint(username: str, send_log, report_results):
    await send_log(f"[+] Starting GITLAB Developer Recon for: {username}")
    
    url = f"https://gitlab.com/api/v4/users?username={username}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        user = data[0]
                        
                        name = user.get("name")
                        bio = user.get("bio", "")
                        location = user.get("location", "")
                        website = user.get("website_url", "")
                        avatar = user.get("avatar_url")
                        user_id = user.get("id")
                        
                        await send_log(f"[GITLAB] Profile Found!")
                        if name:
                            await send_log(f"[GITLAB] Name: {name}")
                        if location:
                            await send_log(f"[GITLAB] Location: {location}")
                        if website:
                            await send_log(f"[GITLAB] Website: {website}")
                        
                        result = {
                            "username": username,
                            "name": name,
                            "bio": bio,
                            "location": location,
                            "website": website,
                            "avatar_url": avatar
                        }
                        
                        # Get their public projects
                        if user_id:
                            proj_url = f"https://gitlab.com/api/v4/users/{user_id}/projects?per_page=5&order_by=updated_at"
                            async with session.get(proj_url, timeout=10) as proj_resp:
                                if proj_resp.status == 200:
                                    projects = await proj_resp.json()
                                    proj_names = [p.get("name") for p in projects if p.get("name")]
                                    if proj_names:
                                        await send_log(f"[GITLAB] Recent projects: {', '.join(proj_names)}")
                                        result["recent_projects"] = proj_names
                        
                        await report_results("Dev Stack (GitLab)", result)
                    else:
                        await send_log("[-] GITLAB: No user found by this name.")
                else:
                    await send_log(f"[-] GITLAB Error: API returned {response.status}")
    except Exception as e:
        await send_log(f"[!] GITLAB Exception: {str(e)}")
