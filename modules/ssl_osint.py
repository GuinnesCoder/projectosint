import ssl
import socket
from datetime import datetime
import asyncio

async def run_ssl_osint(domain: str, send_log, report_results):
    await send_log(f"[+] Starting SSL Certificate monitor for: {domain}")
    
    def _get_cert():
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                return ssock.getpeercert()

    try:
        cert = await asyncio.to_thread(_get_cert)
        
        # Parse Dates
        not_after = cert.get('notAfter')
        if not_after:
            expire_dt = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            days_left = (expire_dt - datetime.utcnow()).days
            
            await send_log(f"[SSL] Domain SSL certificate expires in {days_left} days.")
            if days_left < 30:
                await send_log("[!] SSL: Certificate is close to expiration. Domain might be abandoned.")
                
            issuer = dict(x[0] for x in cert.get('issuer', []))
            
            await report_results("Security (SSL/TLS)", {
                "domain": domain,
                "days_until_expiration": days_left,
                "expiration_date": str(expire_dt),
                "issuer_org": issuer.get("organizationName", "Unknown")
            })
    except Exception as e:
        await send_log(f"[-] SSL monitor failed (Domain might not have HTTPS): {str(e)}")
