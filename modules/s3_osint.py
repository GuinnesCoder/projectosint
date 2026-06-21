import aiohttp

async def run_s3_osint(keyword: str, send_log, report_results):
    await send_log(f"[+] Starting CLOUD BUCKET HUNTER (S3) for: {keyword}")
    
    # Common S3-style bucket URL patterns
    bucket_urls = [
        f"https://{keyword}.s3.amazonaws.com",
        f"https://s3.amazonaws.com/{keyword}",
        f"https://{keyword}.s3-us-west-1.amazonaws.com",
        f"https://{keyword}.storage.googleapis.com",
        f"https://storage.googleapis.com/{keyword}",
    ]
    
    found_buckets = []
    
    try:
        async with aiohttp.ClientSession() as session:
            for bucket_url in bucket_urls:
                try:
                    async with session.get(bucket_url, timeout=5) as response:
                        if response.status == 200:
                            body = await response.text()
                            # Public S3 bucket listing returns XML with <ListBucketResult>
                            if "<ListBucketResult" in body or "<Contents>" in body:
                                await send_log(f"[!] S3: OPEN PUBLIC BUCKET FOUND: {bucket_url}")
                                
                                # Count number of <Key> entries (files)
                                import re
                                keys = re.findall(r"<Key>(.*?)</Key>", body)
                                await send_log(f"[S3] Files exposed: {len(keys)}")
                                if keys:
                                    for k in keys[:5]:
                                        await send_log(f"[S3]   → {k}")
                                
                                found_buckets.append({
                                    "url": bucket_url,
                                    "files_count": len(keys),
                                    "sample_files": keys[:10]
                                })
                            elif response.status == 403:
                                # Bucket exists but is protected
                                await send_log(f"[S3] Bucket exists but is PROTECTED: {bucket_url}")
                                found_buckets.append({
                                    "url": bucket_url,
                                    "status": "protected"
                                })
                except Exception:
                    continue
        
        if found_buckets:
            await report_results("Cloud Recon (S3 Buckets)", {
                "keyword": keyword,
                "buckets_found": len(found_buckets),
                "details": found_buckets
            })
        else:
            await send_log("[-] S3: No open cloud buckets found for this keyword.")
    except Exception as e:
        await send_log(f"[!] S3 Exception: {str(e)}")
