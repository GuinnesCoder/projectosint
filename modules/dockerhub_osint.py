import aiohttp

async def run_dockerhub_osint(username: str, send_log, report_results):
    await send_log(f"[+] Starting DOCKERHUB Container Recon for: {username}")
    
    url = f"https://hub.docker.com/v2/users/{username}"
    repos_url = f"https://hub.docker.com/v2/repositories/{username}/?page_size=10&ordering=last_updated"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    full_name = data.get("full_name", "")
                    company = data.get("company", "")
                    location = data.get("location", "")
                    date_joined = data.get("date_joined", "")
                    
                    await send_log(f"[DOCKER] DockerHub profile found!")
                    if full_name:
                        await send_log(f"[DOCKER] Name: {full_name}")
                    if company:
                        await send_log(f"[DOCKER] Company: {company}")
                    
                    result = {
                        "username": username,
                        "full_name": full_name,
                        "company": company,
                        "location": location,
                        "joined": date_joined
                    }
                    
                    # Get their repos
                    async with session.get(repos_url, timeout=10) as repos_resp:
                        if repos_resp.status == 200:
                            repos_data = await repos_resp.json()
                            repos = repos_data.get("results", [])
                            
                            if repos:
                                repo_names = []
                                for r in repos[:5]:
                                    name = r.get("name", "")
                                    pulls = r.get("pull_count", 0)
                                    stars = r.get("star_count", 0)
                                    repo_names.append(name)
                                    await send_log(f"[DOCKER] Image: {username}/{name} (↓{pulls} ★{stars})")
                                
                                result["public_images"] = repo_names
                                result["total_repos"] = repos_data.get("count", 0)
                    
                    await report_results("Dev Stack (DockerHub)", result)
                elif response.status == 404:
                    await send_log("[-] DOCKER: No DockerHub user found.")
                else:
                    await send_log(f"[-] DOCKER Error: API returned {response.status}")
    except Exception as e:
        await send_log(f"[!] DOCKER Exception: {str(e)}")
