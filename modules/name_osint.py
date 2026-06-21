import aiohttp
import asyncio

async def run_name_demographics(query: str, send_log, report_results):
    await send_log(f"[+] Starting NAME DEMOGRAPHICS AI inference for: {query}")
    
    parts = query.split()
    if len(parts) == 0: return
    
    # Typically first name defines demographics
    first_name = parts[1] if len(parts) >= 2 and parts[0].endswith(("вич", "вна")) == False else parts[0]
    # Simple heuristic for russian names (Фамилия Имя Отчество -> Имя is 2nd word)
    if len(parts) >= 2 and (parts[0].endswith("ов") or parts[0].endswith("ова") or parts[0].endswith("ин") or parts[0].endswith("ина")):
        first_name = parts[1]

    gender_url = f"https://api.genderize.io/?name={first_name}"
    nation_url = f"https://api.nationalize.io/?name={first_name}"

    try:
        async with aiohttp.ClientSession() as session:
            g_task = session.get(gender_url, timeout=5)
            n_task = session.get(nation_url, timeout=5)
            
            g_res, n_res = await asyncio.gather(g_task, n_task, return_exceptions=True)
            
            results = {"parsed_name": query}
            
            if not isinstance(g_res, Exception) and g_res.status == 200:
                g_data = await g_res.json()
                gender = g_data.get("gender")
                prob = g_data.get("probability", 0) * 100
                if gender:
                    await send_log(f"[DEMOGRAPHICS] Predicted Gender: {gender.upper()} (Confidence: {prob:.1f}%)")
                    results["gender"] = gender
                    results["gender_confidence"] = prob

            if not isinstance(n_res, Exception) and n_res.status == 200:
                n_data = await n_res.json()
                countries = n_data.get("country", [])
                if countries:
                    best_country = countries[0].get("country_id")
                    c_prob = countries[0].get("probability", 0) * 100
                    await send_log(f"[DEMOGRAPHICS] Predicted Nationality: {best_country} (Confidence: {c_prob:.1f}%)")
                    results["nationality"] = best_country
                    results["nation_confidence"] = c_prob
                    
            if "gender" in results or "nationality" in results:
                await report_results("Identity (Demographics)", results)
            else:
                await send_log("[-] DEMOGRAPHICS: Name inference inconclusive.")
                
    except Exception as e:
        await send_log(f"[!] DEMOGRAPHICS Exception: {str(e)}")
