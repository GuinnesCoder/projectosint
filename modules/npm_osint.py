import aiohttp

async def run_npm_osint(username: str, send_log, report_results):
    await send_log(f"[+] Starting NPM REGISTRY developer search for: {username}")
    
    url = f"https://registry.npmjs.org/-/v1/search?text=maintainer:{username}&size=10"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    packages = data.get("objects", [])
                    
                    if not packages:
                        await send_log("[-] NPM: No published packages found for this username.")
                        return
                    
                    pkg_names = []
                    for obj in packages:
                        pkg = obj.get("package", {})
                        name = pkg.get("name")
                        desc = pkg.get("description", "")[:60]
                        if name:
                            pkg_names.append(name)
                            await send_log(f"[NPM] Package: {name} — {desc}")
                    
                    await report_results("Dev Stack (NPM Registry)", {
                        "username": username,
                        "published_packages": len(pkg_names),
                        "package_list": pkg_names
                    })
                else:
                    await send_log(f"[-] NPM: Registry returned {response.status}")
    except Exception as e:
        await send_log(f"[!] NPM Exception: {str(e)}")
