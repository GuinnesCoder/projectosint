import aiohttp

async def run_eth_osint(address: str, send_log, report_results):
    await send_log(f"[+] Starting ETHEREUM Blockchain recon for: {address}")
    
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest"
    tx_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "1":
                        balance_wei = int(data.get("result", 0))
                        balance_eth = balance_wei / 1e18
                        
                        await send_log(f"[ETH] Wallet Balance: {balance_eth:.6f} ETH")
                        if balance_eth > 0:
                            await send_log(f"[!] ETH: TARGET HAS ACTIVE FUNDS!")
                        
                        result = {
                            "address": address,
                            "balance_eth": balance_eth,
                            "balance_wei": balance_wei
                        }
                        
                        # Try to get recent txs
                        async with session.get(tx_url, timeout=10) as tx_resp:
                            if tx_resp.status == 200:
                                tx_data = await tx_resp.json()
                                txs = tx_data.get("result", [])
                                if isinstance(txs, list) and len(txs) > 0:
                                    result["total_recent_txs"] = len(txs)
                                    last_tx = txs[0]
                                    result["last_tx_to"] = last_tx.get("to")
                                    result["last_tx_value_eth"] = int(last_tx.get("value", 0)) / 1e18
                                    await send_log(f"[ETH] Last tx to: {last_tx.get('to')}")
                        
                        await report_results("Finance (ETH Blockchain)", result)
                    else:
                        await send_log(f"[-] ETH: Invalid address or no data found.")
                else:
                    await send_log(f"[-] ETH Error: Etherscan returned {response.status}")
    except Exception as e:
        await send_log(f"[!] ETH Exception: {str(e)}")
