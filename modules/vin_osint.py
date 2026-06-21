import aiohttp

async def run_vin_osint(vin: str, send_log, report_results):
    await send_log(f"[+] Starting AUTO RECON / VIN Decoder for: {vin}")
    
    # NHTSA Public API
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('Results', [])
                    
                    vehicle_info = {}
                    for item in results:
                        val = item.get('Value')
                        var_id = item.get('VariableId')
                        
                        # 26: Make, 28: Model, 29: Year, 31: Plant, 39: Vehicle Type, 143: ErrorCode
                        if var_id == 143 and val and "0" not in val and "Successful" not in val:
                            await send_log(f"[-] VIN: Invalid or non-standard VIN code. Decode failed.")
                            return

                        if val and str(val).strip() and val != "Not Applicable":
                            if var_id == 26: vehicle_info["Make"] = val
                            elif var_id == 28: vehicle_info["Model"] = val
                            elif var_id == 29: vehicle_info["Year"] = val
                            elif var_id == 31: vehicle_info["Plant City"] = val
                            elif var_id == 39: vehicle_info["Vehicle Type"] = val
                    
                    if "Make" in vehicle_info:
                        year = vehicle_info.get("Year", "Unknown Year")
                        make = vehicle_info.get("Make", "Unknown Make")
                        model = vehicle_info.get("Model", "Unknown Model")
                        
                        await send_log(f"[VIN] Vehicle Identified: {year} {make} {model}")
                        if "Plant City" in vehicle_info:
                            await send_log(f"[VIN] Assembled in: {vehicle_info.get('Plant City')}")
                            
                        await report_results("Auto Recon (VIN)", vehicle_info)
                    else:
                        await send_log("[-] VIN: No manufacturer data found for this code.")
                else:
                    await send_log(f"[-] VIN Error: Auto Database returned {response.status}")
    except Exception as e:
        await send_log(f"[!] VIN Exception: {str(e)}")
