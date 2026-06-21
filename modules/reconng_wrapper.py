import asyncio
import subprocess
import os
import sqlite3
import re
from pathlib import Path

async def run_reconng(target: str, send_log, report_results):
    await send_log(f"[+] Starting Recon-ng Automated Framework for: {target}")
    
    # Simple regex to check if it's an IP or a Domain
    is_ip = re.match(r"^\d{1,3}(\.\d{1,3}){3}$", target)
    
    workspace_name = f"osint_{target.replace('.', '_')}"
    
    # Fallback to standard modules depending on target type
    if is_ip:
        # IP based resolution
        modules = [
            "recon/netblocks-ports/census_2012",
            "recon/hosts-hosts/reverse_resolve"
        ]
    else:
        # Domain based resolution
        modules = [
            "recon/domains-hosts/hackertarget",
            "recon/domains-contacts/whois_pocs"
        ]
        
    cmds = [f"workspaces add {workspace_name}"]
    for mod in modules:
        cmds.append(f"marketplace install {mod}")
        cmds.append(f"modules load {mod}")
        cmds.append(f"options set SOURCE {target}")
        cmds.append("run")
    cmds.append("exit")
    
    rc_commands = "; ".join(cmds)
    cli_cmd = f"recon-cli -C \"{rc_commands}\""
    
    loop = asyncio.get_running_loop()
    
    def _run_cmd():
        # Execute recon-cli and stream specific output to UI
        process = subprocess.Popen(
            cli_cmd,
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
            if clean_text and ("[*]" in clean_text or "[+]" in clean_text or "[-]" in clean_text or "rror" in clean_text):
                # Filter out pure noise lines
                asyncio.run_coroutine_threadsafe(send_log(f"[RECON-NG CLI] {clean_text[:150]}"), loop)
                    
        process.wait()
        
    await asyncio.to_thread(_run_cmd)
    
    # Post-Execution: Extract cleanly from Recon-ng SQLite DB
    data = {"hosts": [], "contacts": [], "ports": []}
    
    def _read_sqlite():
        home_dir = Path.home()
        db_path = home_dir / ".recon-ng" / "workspaces" / workspace_name / "data.db"
        if not db_path.exists():
            return False
            
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Recon-ng Tables to harvest
            # Fetch Hosts
            cursor.execute("SELECT host, ip_address, region, country FROM hosts")
            for row in cursor.fetchall():
                data["hosts"].append(dict(row))
                
            # Fetch Contacts
            cursor.execute("SELECT first_name, last_name, email, title FROM contacts")
            for row in cursor.fetchall():
                data["contacts"].append(dict(row))
                
            # Fetch Ports
            cursor.execute("SELECT host, ip_address, port, protocol FROM ports")
            for row in cursor.fetchall():
                data["ports"].append(dict(row))
                
            conn.close()
            return True
        except Exception as e:
            asyncio.run_coroutine_threadsafe(send_log(f"[!] SQLite Error reading Recon-ng DB: {e}"), loop)
            return False

    success = await asyncio.to_thread(_read_sqlite)
    
    if not success:
        await send_log(f"[-] Recon-ng scan completed, but no local database found for parsing. Is recon-ng fully initialized?")
    else:
        await send_log(f"[-] Recon-ng SQLite DB connected. Extracted deep relationships.")
        
    # Clean up empty data fields and normalize for the recursive engine
    cleaned_data = {k: v for k, v in data.items() if v}
    await report_results("Recon-ng Framework", cleaned_data)
