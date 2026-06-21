import asyncio
import subprocess

async def run_maigret(username: str, send_log, report_results):
    await send_log(f"[+] Starting MAIGRET username scan for: {username}")
    
    cmd = f"python -m maigret {username} --no-extract --timeout 10 -n 50"
    
    loop = asyncio.get_running_loop()
    found_sites = []
    
    def _run_cmd():
        import os
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env
        )
        
        for line in process.stdout:
            text = line.strip()
            if text:
                # Schedule the async send_log from this sync thread
                asyncio.run_coroutine_threadsafe(send_log(f"[MAIGRET] {text}"), loop)
                
                # Very basic extraction of found sites based on Maigret output format
                if "Found" in text or "http" in text:
                    found_sites.append(text)
                    
        process.wait()
        
    # Run the synchronous subprocess code in a thread pool to avoid blocking the event loop
    await asyncio.to_thread(_run_cmd)
    
    await send_log(f"[-] MAIGRET scan completed.")
    await report_results("Username Search (Maigret)", {"found": found_sites})
