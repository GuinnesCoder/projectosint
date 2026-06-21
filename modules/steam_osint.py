import aiohttp
import xml.etree.ElementTree as ET
import re

async def run_steam_osint(query: str, send_log, report_results):
    await send_log(f"[+] Starting STEAM OSINT scan for: {query}")
    
    # Check if query is a 17-digit SteamID64 or customized ID
    if re.match(r"^\d{17}$", query):
        url = f"https://steamcommunity.com/profiles/{query}/?xml=1"
    else:
        url = f"https://steamcommunity.com/id/{query}/?xml=1"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    xml_data = await response.text()
                    
                    if "<error>" in xml_data:
                        # Sometimes valid users have private profiles returning specific XML, but <error> means not found
                        error_match = re.search(r"<error><!\[CDATA\[(.*?)\]\]></error>", xml_data)
                        if error_match:
                            err_text = error_match.group(1)
                            await send_log(f"[-] STEAM: {err_text}")
                        else:
                            await send_log(f"[-] STEAM: Profile not found.")
                        return

                    root = ET.fromstring(xml_data)
                    
                    # Extract Data
                    steam_id64 = root.findtext('steamID64')
                    steam_login = root.findtext('steamID')
                    avatar_url = root.findtext('avatarFull')
                    vac_banned = root.findtext('vacBanned')
                    trade_ban = root.findtext('tradeBanState')
                    member_since = root.findtext('memberSince')
                    real_name = root.findtext('realname', 'Not Provided')
                    location = root.findtext('location', 'Not Provided')
                    
                    if not steam_id64:
                        await send_log("[-] STEAM: Profile is private or not fully resolved.")
                        return

                    await send_log(f"[STEAM] Exact Match Found!")
                    await send_log(f"[STEAM] SteamID64: {steam_id64}")
                    await send_log(f"[STEAM] Current Nickname: {steam_login}")
                    if real_name != 'Not Provided':
                        await send_log(f"[STEAM] Real Name: {real_name}")
                        
                    if vac_banned == "1":
                        await send_log(f"[!] STEAM: CRITICAL - TARGET HAS A VAC BAN!")
                        
                    await report_results("Gaming (Steam Profile)", {
                        "steamID64": steam_id64,
                        "nickname": steam_login,
                        "real_name": real_name,
                        "location": location,
                        "member_since": member_since,
                        "vac_banned": vac_banned == "1",
                        "trade_banned": trade_ban != "None",
                        "avatar": avatar_url
                    })
                else:
                    await send_log(f"[-] STEAM Error: Community API returned {response.status}")
    except Exception as e:
        await send_log(f"[!] STEAM Exception: {type(e).__name__} - {str(e)}")
