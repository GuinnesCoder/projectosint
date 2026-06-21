import asyncio
import os
import httpx

async def run_lampyre(target: str, send_log, report_results):
    await send_log(f"[+] Starting Lampyre Lighthouse REST API for: {target}")
    
    # Verify the environment key exists
    api_token = os.getenv("LAMPYRE_API_KEY", "")
    if not api_token:
        await send_log("[!] LAMPYRE_API_KEY missing in .env! Please configure your token.")
        await report_results("Lampyre Analysis", {"error": "API Key missing"})
        return
        
    base_url = "https://api.lampyre.io/api/v1"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Abstract search for Lighthouse Graph Engine
    # Note: Lampyre requires specific task routing in real scenarios (e.g., 'email_info', 'phone_search')
    # Since search must be automatic, we post a universal indicator target
    payload = {
        "request": target,
        "tasks": ["universal_search_auto"] 
    }
    
    data = {"nodes": [], "edges": [], "status": ""}
    
    # We use httpx instead of requests to prevent blocking the async FastApi event loop
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Dispatch Task to Engine
            await send_log(f"[*] [LAMPYRE] Dispatching graph query to {base_url}...")
            create_resp = await client.post(f"{base_url}/tasks", headers=headers, json=payload)
            
            if create_resp.status_code == 401:
                await send_log("[!] [LAMPYRE] Unauthorized (401). Invalid LAMPYRE_API_KEY.")
                data["error"] = "Unauthorized API Key"
                await report_results("Lampyre Analysis", data)
                return
            elif create_resp.status_code != 200 and create_resp.status_code != 201 and create_resp.status_code != 202:
                data["error"] = f"API Error {create_resp.status_code}: {create_resp.text}"
                await report_results("Lampyre Analysis", data)
                return
                
            task_info = create_resp.json()
            task_id = task_info.get("task_id") or task_info.get("id")
            
            if not task_id:
                data["status"] = "No resolvable task created by the engine."
                await report_results("Lampyre Analysis", data)
                return
                
            # 2. Asynchronous Polling loop
            await send_log(f"[*] [LAMPYRE] Task {task_id} generated. Polling graph engine for resolution...")
            
            max_polls = 12
            for i in range(max_polls):
                await asyncio.sleep(5)  # Wait 5 seconds between polls
                poll_resp = await client.get(f"{base_url}/tasks/{task_id}", headers=headers)
                
                if poll_resp.status_code == 200:
                    status_info = poll_resp.json()
                    status = status_info.get("status", "").lower()
                    
                    if status in ["done", "completed", "success"]:
                        await send_log("[+] [LAMPYRE] Graph engine correlations completed.")
                        # Parse out resulting graph artifacts from Lampyre ontology
                        results = status_info.get("results", {})
                        
                        data["nodes"] = results.get("nodes", [])
                        data["edges"] = results.get("edges", [])
                        data["status"] = "Success"
                        
                        if data["nodes"]:
                            await send_log(f"[*] [LAMPYRE] Extracted {len(data['nodes'])} nodes from ontology graph!")
                        break
                    elif status in ["error", "failed"]:
                        await send_log(f"[!] [LAMPYRE] Remote task failed: {status_info.get('message')}")
                        data["status"] = "Failed on remote engine"
                        break
                    else:
                        await send_log(f"[*] [LAMPYRE] Polling status: {status.upper()}... (wait)")
                else:
                    await send_log(f"[!] [LAMPYRE] Polling error HTTP {poll_resp.status_code}")
                    break
                    
        except httpx.RequestError as exc:
            await send_log(f"[!] [LAMPYRE] HTTP Client network error: {exc}")
            data["error"] = f"Connection failed: {exc}"
        except Exception as e:
            await send_log(f"[!] [LAMPYRE] Unexpected engine execution error: {str(e)}")
            data["error"] = f"Runtime exception: {str(e)}"
            
    await send_log(f"[-] Lampyre scanning cycle finished.")
    await report_results("Lampyre Analysis", data)
