import aiohttp

async def run_hash_osint(query: str, send_log, report_results):
    await send_log(f"[+] Starting CRYPTO Hash Reverser for: {query}")
    
    if len(query) == 32:
        url = f"https://www.nitrxgen.net/md5db/{query}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        cracked = await response.text()
                        if cracked:
                            await send_log(f"[!] HASH REVERSED (MD5): {cracked}")
                            await report_results("Decryption (Hash)", {
                                "original_hash": query,
                                "hash_type": "MD5",
                                "decrypted_text": cracked
                            })
                        else:
                            await send_log("[-] HASH: Database missed. Hash not reversed.")
        except Exception as e:
            await send_log(f"[!] HASH REVERSER Exception: {str(e)}")
    else:
        await send_log("[-] HASH: Currently only MD5 hashes (32 chars) are supported for reversal.")
