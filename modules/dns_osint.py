import aiohttp
import asyncio

async def run_dns_osint(domain: str, send_log, report_results):
    await send_log(f"[+] Starting DNS & WHOIS Recon for: {domain}")
    
    dns_url = f"https://networkcalc.com/api/dns/lookup/{domain}"
    whois_url = f"https://networkcalc.com/api/whois/{domain}"
    
    try:
        async with aiohttp.ClientSession() as session:
            d_task = session.get(dns_url, timeout=10)
            w_task = session.get(whois_url, timeout=10)
            
            d_res, w_res = await asyncio.gather(d_task, w_task, return_exceptions=True)
            
            results = {"domain": domain}
            
            if not isinstance(d_res, Exception) and d_res.status == 200:
                d_data = await d_res.json()
                records = d_data.get('records', {})
                a_records = [x.get('address') for x in records.get('A', [])]
                mx_records = [x.get('exchange') for x in records.get('MX', [])]
                
                if a_records:
                    await send_log(f"[DNS] Resolves to IPs: {', '.join(a_records)}")
                    results['a_records'] = a_records
                if mx_records:
                    await send_log(f"[DNS] Mail Servers (MX): {', '.join(mx_records)}")
                    results['mx_records'] = mx_records
                    
            if not isinstance(w_res, Exception) and w_res.status == 200:
                w_data = await w_res.json()
                whois = w_data.get('whois', {})
                reg = whois.get('registrar')
                created = whois.get('creation_date')
                
                if reg:
                    await send_log(f"[WHOIS] Registrar: {reg}")
                    results['registrar'] = reg
                if created:
                    await send_log(f"[WHOIS] Creation Date: {created}")
                    results['creation_date'] = created
                    
            if len(results) > 1:
                await report_results("Infrastructure (DNS & WHOIS)", results)
            else:
                await send_log("[-] DNS/WHOIS: No records extracted.")
                
    except Exception as e:
        await send_log(f"[!] DNS OSINT Exception: {str(e)}")
