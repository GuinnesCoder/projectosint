import aiohttp

async def run_crypto_osint(btc_address: str, send_log, report_results):
    await send_log(f"[+] Starting BLOCKCHAIN financial recon for: {btc_address}")
    
    url = f"https://blockchain.info/rawaddr/{btc_address}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Balances in satoshis (1 BTC = 100,000,000 satoshis)
                    final_balance = data.get('final_balance', 0) / 100000000
                    total_received = data.get('total_received', 0) / 100000000
                    total_txs = data.get('n_tx', 0)
                    
                    await send_log(f"[CRYPTO] Wallet mapped to Blockchain DB.")
                    await send_log(f"[CRYPTO] Total Transactions: {total_txs}")
                    await send_log(f"[CRYPTO] Total Received: {total_received:.4f} BTC")
                    await send_log(f"[CRYPTO] Current Balance: {final_balance:.4f} BTC")
                    
                    if final_balance > 0:
                        await send_log(f"[!] CRYPTO: TARGET HAS ACTIVE FUNDS!")
                        
                    await report_results("Finance (BTC Blockchain)", {
                        "address": btc_address,
                        "transactions_count": total_txs,
                        "total_received_btc": total_received,
                        "current_balance_btc": final_balance
                    })
                elif response.status == 404:
                    await send_log(f"[-] CRYPTO: Wallet not found on BTC blockchain.")
                else:
                    await send_log(f"[-] CRYPTO Error: Blockchain.info returned {response.status}")
    except Exception as e:
        await send_log(f"[!] CRYPTO Exception: {str(e)}")
