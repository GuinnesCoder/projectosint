import asyncio
import subprocess
import re

async def run_holehe(email: str, send_log, report_results):
    await send_log(f"[+] Starting HOLEHE email discovery for: {email}")
    cmd = f"holehe --only-used {email}"
    
    loop = asyncio.get_running_loop()
    registered_sites = []
    
    def _run_cmd():
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        for line in process.stdout:
            text = line.strip()
            clean_text = ansi_escape.sub('', text)
            if clean_text:
                # Schedule the async send_log from this sync thread
                asyncio.run_coroutine_threadsafe(send_log(f"[HOLEHE] {clean_text}"), loop)
                if "[+]" in clean_text:
                    registered_sites.append(clean_text.replace("[+]", "").strip())
                    
        process.wait()
        
    # Run the synchronous subprocess code in a thread pool to avoid blocking the event loop
    await asyncio.to_thread(_run_cmd)
    
    await send_log(f"[-] HOLEHE scan completed.")
    await report_results("Email Discovery (Holehe)", {"registered_on": registered_sites})
