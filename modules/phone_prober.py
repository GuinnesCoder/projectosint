import os
import phonenumbers
import aiohttp
from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType

async def run_phone_prober(phone: str, send_log, report_results):
    await send_log(f"[+] Starting DEEP PHONE PROBER for: {phone}")
    
    results = {}
    try:
        parsed_number = phonenumbers.parse(phone, None)
        is_valid = phonenumbers.is_valid_number(parsed_number)
        results["is_valid"] = is_valid
        
        if is_valid:
            e164 = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            international = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            national = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
            rfc3966 = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.RFC3966)
            
            await send_log(f"[PHONE] Target validated: {e164}")
            
            # --- 1. IDENTITY RESOLUTION (FIO) ---
            await send_log("[+] Initializing Identity Resolution (FIO Extraction)...")
            extracted_fio = None
            
            # 1.a Truecaller API Integration
            truecaller_token = os.getenv("TRUECALLER_TOKEN")
            if truecaller_token:
                try:
                    await send_log("[TRUECALLER] Token found, querying global caller ID database...")
                    headers = {
                        "Authorization": f"Bearer {truecaller_token}",
                        "User-Agent": "Truecaller/11.75.5 (Android;10)"
                    }
                    url = f"https://search5-noneu.truecaller.com/v2/search?q={e164}&countryCode=RU&type=4&locAddr=&placement=SEARCHRESULTS,HISTORY,DETAILS&isOops=false"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=8) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get("data") and len(data["data"]) > 0:
                                    profile = data["data"][0]
                                    name = profile.get("name", "")
                                    if name:
                                        extracted_fio = name
                                        await send_log(f"[!] TRUECALLER IDENTITY MATCH: {extracted_fio}")
                except Exception as ex:
                    await send_log(f"[-] Truecaller query failed: {str(ex)}")
            else:
                await send_log("[-] TRUECALLER_TOKEN not found in .env. Skipping caller ID FIO extraction.")

            # 1.b GetContact / SBP Fast Payment System Mock (If Truecaller failed)
            if not extracted_fio:
                sbp_token = os.getenv("SBP_TOKEN")
                if sbp_token:
                    await send_log("[SBP] Querying Fast Payment network for Bank account holder name...")
                    # Implementation for banking API goes here (requires specific auth certs)
                    await send_log("[-] SBP Query incomplete: requires MTLS banking certificates.")
                else:
                    await send_log("[-] Identity resolution restricted. For exact FIO (Иванов И.И), add TRUECALLER_TOKEN to .env")

            # --- 2. TELECOM & GEO EXTRACTION ---
            num_type = number_type(parsed_number)
            type_mapping = {
                PhoneNumberType.MOBILE: "Mobile / Cellular",
                PhoneNumberType.FIXED_LINE: "Fixed Line / Landline",
                PhoneNumberType.VOIP: "VoIP (Virtual Number)"
            }
            line_type = type_mapping.get(num_type, "Virtual/Other")
            await send_log(f"[PHONE] Line Type: {line_type}")
            
            if num_type == PhoneNumberType.VOIP:
                await send_log(f"[!] WARNING: Number is VoIP. Identity is likely shielded/virtual.")
            # 3. Geography & Telecom (Global Fallbacks)
            country = geocoder.description_for_number(parsed_number, "en")
            provider = carrier.name_for_number(parsed_number, "en")
            tz_list = list(timezone.time_zones_for_number(parsed_number))
            
            precise_region, precise_operator = country, provider
            
            if e164.startswith("+7"):
                try:
                    num_clean = e164.replace("+", "")
                    url = f"https://num.voxlink.ru/get/?num={num_clean}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get("region"):
                                    precise_region = data["region"]
                                    await send_log(f"[PHONE] Precise Region Extracted: {precise_region}")
                                if data.get("operator"):
                                    precise_operator = data["operator"]
                                    await send_log(f"[PHONE] Exact Carrier Extracted: {precise_operator}")
                except Exception:
                    pass
            
            # --- 3.5 LOCAL TIME AWARENESS ---
            # Extremely useful for investigators to know if the target is awake
            import datetime
            try:
                import pytz
                local_time_str = "Unknown"
                if tz_list and tz_list[0] != "unknown":
                    target_tz = pytz.timezone(tz_list[0])
                    now_target = datetime.datetime.now(target_tz)
                    local_time_str = now_target.strftime('%Y-%m-%d %H:%M:%S (%z)')
                    
                    hour = now_target.hour
                    if hour >= 23 or hour < 7:
                        await send_log(f"[!] Target is likely ALSEEP. Local time: {local_time_str}")
                    else:
                        await send_log(f"[PHONE] Target Local Time: {local_time_str}")
            except ImportError:
                local_time_str = "pytz module not installed"
                
            # 4. OSINT Messenger Fast-Links
            messenger_links = {
                "WhatsApp": f"https://wa.me/{e164.strip('+')}",
                "Telegram": f"https://t.me/{e164.strip('+')}",
                "Viber": f"viber://chat?number={e164.strip('+')}"
            }
            
            # 5. OSINT Social Recovery Links
            # Used by investigators to click and see masked names (e.g., И*** И****) or masked emails
            recovery_links = {
                "VK_Restore": f"https://vk.com/restore?login={e164}",
                "Mail_ru": f"https://account.mail.ru/recovery?email={e164}",
                "Instagram": f"https://www.instagram.com/accounts/password/reset/?username={e164}",
                "Twitter": f"https://twitter.com/account/begin_password_reset" # X doesn't allow pre-fill easily but good to have
            }
            await send_log(f"[PHONE] Generated Social Media Account Recovery links (for masked identity revealing).")
            
            results = {
                "is_valid": is_valid,
                "e164_format": e164,
                "national_format": national,
                "line_type": line_type,
                "carrier": precise_operator or "Unknown",
                "region": precise_region or "Unknown",
                "country": country or "Unknown",
                "timezones": tz_list,
                "local_time": local_time_str,
                "messenger_links": messenger_links,
                "recovery_links": recovery_links
            }
            
            if extracted_fio:
                results["fio_identity"] = extracted_fio
            
            # Trigger generic dorking for mentions across the web
            await send_log(f"[+] Sending national format {national} to Dorking Engine for leak analysis...")
            
        else:
            await send_log(f"[-] PHONE: Number format invalid or impossible.")
            
    except Exception as e:
        await send_log(f"[!] Phone prober exception: {str(e)}")
        results["error"] = str(e)
        
    await send_log(f"[-] PHONE PROBER completed.")
    await report_results("Phone Intel & Recon", results)
