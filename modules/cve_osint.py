import aiohttp
import re

async def run_cve_osint(query: str, send_log, report_results):
    # Check if query matches CVE format CVE-YYYY-NNNNN
    if not re.match(r"^CVE-\d{4}-\d{4,}$", query.upper()):
        return

    await send_log(f"[+] Starting NVD VULNERABILITY SCANNER for: {query.upper()}")
    
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={query.upper()}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=12) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('vulnerabilities', [])
                    if results:
                        cve_data = results[0].get('cve', {})
                        
                        desc_list = cve_data.get('descriptions', [])
                        desc = desc_list[0].get('value', 'No description') if desc_list else 'No description'
                        
                        metrics = cve_data.get('metrics', {})
                        cvss_data = None
                        if 'cvssMetricV31' in metrics:
                            cvss_data = metrics['cvssMetricV31'][0].get('cvssData', {})
                        elif 'cvssMetricV30' in metrics:
                            cvss_data = metrics['cvssMetricV30'][0].get('cvssData', {})
                            
                        if cvss_data:
                            score = cvss_data.get('baseScore')
                            severity = cvss_data.get('baseSeverity')
                            await send_log(f"[!] VULNERABILITY: {severity} (Score: {score}/10.0)")
                        
                        await send_log(f"[CVE] {desc[:100]}...")
                        
                        await report_results("Cyber Threat (NVD CVE)", {
                            "cve_id": query.upper(),
                            "description": desc,
                            "cvss_score": score if cvss_data else "Unknown",
                            "severity": severity if cvss_data else "Unknown",
                            "published": cve_data.get("published")
                        })
                    else:
                        await send_log(f"[-] CVE: No such vulnerability found in NIST database.")
    except Exception as e:
        await send_log(f"[!] CVE Exception: {str(e)}")
