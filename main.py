import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import json
import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import database
import models
from modules.maigret_wrapper import run_maigret
from modules.holehe_wrapper import run_holehe
from modules.phone_prober import run_phone_prober
from modules.ip_geolocation import run_ip_geolocation
from modules.intelx_wrapper import run_intelx
from modules.wigle_wrapper import run_wigle
from modules.ru_courts import run_ru_courts
from modules.ru_taxes import run_ru_taxes
from modules.ru_bailiffs import run_ru_bailiffs
from modules.tg_osint import run_tg_osint
from modules.abuseipdb_wrapper import run_abuseipdb
from modules.censys_wrapper import run_censys
from modules.greynoise_wrapper import run_greynoise
from modules.shodan_wrapper import run_shodan
from modules.steam_osint import run_steam_osint
from modules.dorking_engine import run_dorking
from modules.name_osint import run_name_demographics
from modules.cert_osint import run_cert_osint
from modules.dns_osint import run_dns_osint
from modules.wayback_osint import run_wayback_osint
from modules.crypto_osint import run_crypto_osint
from modules.vin_osint import run_vin_osint
from modules.mac_osint import run_mac_osint
from modules.gravatar_osint import run_gravatar_osint
from modules.github_osint import run_github_osint
from modules.reddit_osint import run_reddit_osint
from modules.hash_osint import run_hash_osint
from modules.ssl_osint import run_ssl_osint
from modules.cve_osint import run_cve_osint
from modules.twitch_osint import run_twitch_osint
from modules.onion_osint import run_onion_osint
from modules.reverse_geo import run_reverse_geo
from modules.malware_osint import run_malware_osint
from modules.eth_osint import run_eth_osint
from modules.bin_osint import run_bin_osint
from modules.bgp_osint import run_bgp_osint
from modules.npm_osint import run_npm_osint
from modules.chess_osint import run_chess_osint
from modules.pastebin_osint import run_pastebin_osint
from modules.tor_node_osint import run_tor_node_osint
from modules.fns_osint import run_fns_osint
from modules.iban_osint import run_iban_osint
from modules.exploit_osint import run_exploit_osint
from modules.s3_osint import run_s3_osint
from modules.gitlab_osint import run_gitlab_osint
from modules.dockerhub_osint import run_dockerhub_osint
from modules.reconng_wrapper import run_reconng
from modules.lampyre_wrapper import run_lampyre

# Load environment variables
load_dotenv()

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="OSINT Cyber Tool")

# Static and Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Basic Regex for Auto-Detection
IP_REGEX = r"^\d{1,3}(\.\d{1,3}){3}$"
PHONE_REGEX = r"^\+?[1-9]\d{1,14}$"
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
TG_ID_REGEX = r"^\d{5,15}$"

def detect_input_type(query: str):
    query = query.strip()
    if re.match(IP_REGEX, query):
        return "ip"
    elif re.match(EMAIL_REGEX, query):
        return "email"
    elif re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", query):
        return "mac"
    elif re.match(r"^(1|3)[a-km-zA-HJ-NP-Z1-9]{25,34}$", query) or re.match(r"^bc1[a-zA-HJ-NP-Z0-9]{25,39}$", query):
        return "btc"
    elif re.match(r"^0x[0-9a-fA-F]{40}$", query):
        return "eth"
    elif re.match(r"^[A-HJ-NPR-Z0-9]{17}$", query.upper()):
        return "vin"
    elif re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$", query):
        return "domain"
    elif re.match(r"\.onion$", query):
        return "onion"
    elif re.match(r"^CVE-\d{4}-\d{4,}$", query.upper()):
        return "cve"
    elif re.match(r"^[a-fA-F0-9]{32}$", query) or re.match(r"^[a-fA-F0-9]{40}$", query) or re.match(r"^[a-fA-F0-9]{64}$", query):
        return "hash"
    elif re.match(r"^AS\d{3,7}$", query.upper()):
        return "asn"
    elif re.match(r"^-?\d{1,3}\.\d+,\s*-?\d{1,3}\.\d+$", query):
        return "coords"
    elif re.match(r"^\d{4}\s?\d{4}\s?\d{4}\s?\d{4}$", query):
        return "card"
    elif re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{4,}$", query.upper().replace(" ", "")) and len(query.replace(" ", "")) >= 15:
        return "iban"
    elif re.match(r"^\d{10}$", query) or re.match(r"^\d{12}$", query) or re.match(r"^\d{13}$", query):
        return "inn"
    elif re.match(r"^[A-Za-z\u0410-\u042f\u0430-\u044f\u0401\u0451]+(\s[A-Za-z\u0410-\u042f\u0430-\u044f\u0401\u0451]+){1,2}$", query):
        return "fio"
    elif re.match(TG_ID_REGEX, query):
        return "tg_id"
    elif re.match(PHONE_REGEX, query):
        return "phone"
    else:
        return "username"

@app.get("/", response_class=HTMLResponse)
async def get_ui(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        req = json.loads(data)
        original_query = req.get("query", "").strip()
        
        if not original_query:
            await websocket.send_text(json.dumps({"type": "log", "msg": "[!] Error: Empty query received."}))
            return
            
        inputType = detect_input_type(original_query)
        await websocket.send_text(json.dumps({"type": "log", "msg": f"[*] Initiated SYSTEM SCAN for Target: [ {original_query} ]"}))
        await websocket.send_text(json.dumps({"type": "log", "msg": f"[*] Heuristics classification algorithms decided Type: {inputType.upper()}"}))
        
        # We will collect final results for the Dossier PDF
        dossier_results = {}
        
        async def send_log(msg: str):
            try:
                await websocket.send_text(json.dumps({"type": "log", "msg": msg}))
            except Exception:
                pass
            
        # --- RECURSIVE CORRELATION ENGINE ---
        entity_queue = asyncio.Queue()
        processed_entities = set([original_query])
        await entity_queue.put({"type": inputType, "value": original_query})
        
        # Noise filter — well-known platforms/infra that are NOT investigation targets
        NOISE_DOMAINS = {
            "google.com", "microsoft.com", "apple.com", "amazon.com", "cloudflare.com",
            "firefox.com", "mozilla.com", "office365.com", "outlook.com", "live.com",
            "github.com", "gitlab.com", "stackoverflow.com", "reddit.com",
            "facebook.com", "instagram.com", "twitter.com", "x.com", "tiktok.com",
            "youtube.com", "twitch.tv", "discord.com", "telegram.org",
            "yahoo.com", "yandex.ru", "mail.ru", "vk.com", "ok.ru",
            "linkedin.com", "pinterest.com", "tumblr.com", "wordpress.com",
            "spotify.com", "netflix.com", "steam.com", "steampowered.com",
            "amazonaws.com", "azure.com", "googleusercontent.com",
            "1e100.net", "akamai.com", "fastly.com", "cloudfront.net",
            "gravatar.com", "chess.com", "npmjs.com", "dockerhub.com",
            "duckduckgo.com", "bing.com", "wikipedia.org",
        }
        # Keys whose values should never be auto-correlated (infra/meta fields)
        SKIP_KEYS = {
            "avatar_url", "avatar", "profile_url", "snapshot_url", "icon_img",
            "issuer_org", "registrar", "vendor_name", "organization",
            "isp", "org", "country", "city", "region", "timezone", "postcode",
            "country_code", "country_name", "description", "full_address",
            "creation_date", "expiration_date", "network", "type", "brand",
            "bank", "status", "severity", "file_type", "malware_family",
            "hash_type", "tags", "bio", "company", "location", "website",
            "display_name", "real_name", "gender", "nationality",
            "closest_snapshot_time", "check_digits", "bban", "bank_code",
        }
        
        def is_noise(value: str, det_type: str, key: str = "") -> bool:
            """Returns True if this entity is infrastructure noise, not a real lead."""
            if key.lower() in SKIP_KEYS:
                return True
            if det_type == "domain" and value.lower() in NOISE_DOMAINS:
                return True
            if det_type == "domain":
                # Skip domains that are subdomains of known infra
                for nd in NOISE_DOMAINS:
                    if value.lower().endswith("." + nd):
                        return True
            if det_type == "email":
                # Skip non-personal emails (noreply, checkout, system)
                local_part = value.split("@")[0].lower()
                if any(x in local_part for x in ["noreply", "checkout", "admin", "system", "support", "info", "postmaster"]):
                    return True
                # Skip emails @known-platforms (not personal leads)
                email_domain = value.split("@")[1].lower() if "@" in value else ""
                if email_domain in NOISE_DOMAINS:
                    return True
            if det_type == "tg_id":
                # Zip codes and short numbers are NOT telegram IDs
                # Only treat as TG_ID if it's 7+ digits (real TG IDs are 7-11 digits)
                if len(value) < 7:
                    return True
            if det_type == "ip":
                # Skip well-known cloud/CDN IP ranges
                for prefix in ["13.107.", "20.119.", "40.112.", "35.190.", "142.251.", "172.217.",
                               "216.58.", "104.16.", "104.17.", "151.101.", "52.84.", "54.230."]:
                    if value.startswith(prefix):
                        return True
            return False
        
        # Entity Extractor — auto-discovers new leads from module output
        async def extract_and_queue(data_block, parent_key=""):
            if isinstance(data_block, dict):
                for k, v in data_block.items():
                    if isinstance(v, str):
                        if "http" in v or "<" in v or len(v) < 5 or len(v) > 100:
                            continue
                        det_type = detect_input_type(v)
                        if det_type in ["email", "ip", "btc", "eth", "mac", "domain", "phone"]:
                            if v not in processed_entities and not is_noise(v, det_type, k):
                                processed_entities.add(v)
                                await send_log(f"[+] \U0001f9ec RECURSIVE ENGINE: Auto-Correlated new {det_type.upper()} -> {v}")
                                await entity_queue.put({"type": det_type, "value": v})
                    elif isinstance(v, (dict, list)):
                        await extract_and_queue(v, parent_key=k)
            elif isinstance(data_block, list):
                for item in data_block:
                    if isinstance(item, (dict, list)):
                        await extract_and_queue(item, parent_key=parent_key)
                    elif isinstance(item, str) and 5 <= len(item) <= 100:
                        det_type = detect_input_type(item)
                        if det_type in ["email", "ip", "btc", "eth", "mac", "domain", "phone"]:
                            if item not in processed_entities and not is_noise(item, det_type, parent_key):
                                processed_entities.add(item)
                                await send_log(f"[+] \U0001f9ec RECURSIVE ENGINE: Auto-Correlated new {det_type.upper()} -> {item}")
                                await entity_queue.put({"type": det_type, "value": item})

        async def report_results(module_name: str, results: dict):
            key = module_name
            if key in dossier_results:
                key = f"{module_name} ({len(dossier_results)})"
            dossier_results[key] = results
            try:
                await websocket.send_text(json.dumps({"type": "card", "module": module_name, "data": results}))
            except Exception:
                pass
            await extract_and_queue(results)

        # === MAIN RECURSIVE WORKER LOOP ===
        cycle_count = 1
        while not entity_queue.empty() and cycle_count <= 5:
            tasks = []
            q_size = entity_queue.qsize()
            await send_log(f"\n[==== RECURSIVE DEPTH CYCLE {cycle_count} | Processing {q_size} entities ====]")
            
            for _ in range(q_size):
                ent = await entity_queue.get()
                e_type = ent["type"]
                e_val = ent["value"]
                
                await send_log(f"[*] Attaching interceptors to {e_type.upper()}: {e_val}")
                
                if e_type == "ip":
                    tasks.append(run_reconng(e_val, send_log, report_results))
                    tasks.append(run_ip_geolocation(e_val, send_log, report_results))
                    tasks.append(run_wigle(e_val, send_log, report_results))
                    tasks.append(run_abuseipdb(e_val, send_log, report_results))
                    tasks.append(run_censys(e_val, send_log, report_results))
                    tasks.append(run_greynoise(e_val, send_log, report_results))
                    tasks.append(run_shodan(e_val, send_log, report_results))
                    tasks.append(run_tor_node_osint(e_val, send_log, report_results))
                elif e_type == "domain":
                    tasks.append(run_reconng(e_val, send_log, report_results))
                    tasks.append(run_cert_osint(e_val, send_log, report_results))
                    tasks.append(run_dns_osint(e_val, send_log, report_results))
                    tasks.append(run_wayback_osint(e_val, send_log, report_results))
                    tasks.append(run_ssl_osint(e_val, send_log, report_results))
                elif e_type == "onion":
                    tasks.append(run_onion_osint(e_val, send_log, report_results))
                elif e_type == "btc":
                    tasks.append(run_crypto_osint(e_val, send_log, report_results))
                elif e_type == "eth":
                    tasks.append(run_eth_osint(e_val, send_log, report_results))
                elif e_type == "vin":
                    tasks.append(run_vin_osint(e_val.upper(), send_log, report_results))
                elif e_type == "mac":
                    tasks.append(run_mac_osint(e_val, send_log, report_results))
                    tasks.append(run_wigle(e_val, send_log, report_results))
                elif e_type == "fio":
                    tasks.append(run_name_demographics(e_val, send_log, report_results))
                    tasks.append(run_intelx(e_val, send_log, report_results))
                    tasks.append(run_dorking(e_val, send_log, report_results))
                    tasks.append(run_ru_courts(e_val, send_log, report_results))
                elif e_type == "phone":
                    tasks.append(run_lampyre(e_val, send_log, report_results))
                    tasks.append(run_phone_prober(e_val, send_log, report_results))
                    tasks.append(run_dorking(e_val, send_log, report_results))
                    tasks.append(run_intelx(e_val, send_log, report_results))
                    tasks.append(run_tg_osint(e_val, send_log, report_results))
                    if e_val.startswith("+7") or e_val.startswith("89"):
                        tasks.append(run_ru_bailiffs(e_val, send_log, report_results))
                elif e_type == "tg_id":
                    tasks.append(run_tg_osint(e_val, send_log, report_results))
                    tasks.append(run_intelx(e_val, send_log, report_results))
                elif e_type == "email":
                    tasks.append(run_lampyre(e_val, send_log, report_results))
                    tasks.append(run_holehe(e_val, send_log, report_results))
                    tasks.append(run_intelx(e_val, send_log, report_results))
                    tasks.append(run_dorking(e_val, send_log, report_results))
                    tasks.append(run_gravatar_osint(e_val, send_log, report_results))
                elif e_type == "username":
                    tasks.append(run_lampyre(e_val, send_log, report_results))
                    tasks.append(run_maigret(e_val, send_log, report_results))
                    tasks.append(run_steam_osint(e_val, send_log, report_results))
                    tasks.append(run_dorking(e_val, send_log, report_results))
                    tasks.append(run_github_osint(e_val, send_log, report_results))
                    tasks.append(run_gitlab_osint(e_val, send_log, report_results))
                    tasks.append(run_reddit_osint(e_val, send_log, report_results))
                    tasks.append(run_twitch_osint(e_val, send_log, report_results))
                    tasks.append(run_npm_osint(e_val, send_log, report_results))
                    tasks.append(run_chess_osint(e_val, send_log, report_results))
                    tasks.append(run_dockerhub_osint(e_val, send_log, report_results))
                    tasks.append(run_pastebin_osint(e_val, send_log, report_results))
                    tasks.append(run_s3_osint(e_val, send_log, report_results))
                    tasks.append(run_intelx(e_val, send_log, report_results))
                    tasks.append(run_ru_courts(e_val, send_log, report_results))
                    tasks.append(run_ru_taxes(e_val, send_log, report_results))
                    tasks.append(run_ru_bailiffs(e_val, send_log, report_results))
                elif e_type == "cve":
                    tasks.append(run_cve_osint(e_val, send_log, report_results))
                    tasks.append(run_exploit_osint(e_val, send_log, report_results))
                elif e_type == "hash":
                    tasks.append(run_hash_osint(e_val, send_log, report_results))
                    tasks.append(run_malware_osint(e_val, send_log, report_results))
                    tasks.append(run_intelx(e_val, send_log, report_results))
                elif e_type == "asn":
                    tasks.append(run_bgp_osint(e_val, send_log, report_results))
                elif e_type == "coords":
                    tasks.append(run_reverse_geo(e_val, send_log, report_results))
                elif e_type == "card":
                    cleaned = e_val.replace(" ", "")
                    tasks.append(run_bin_osint(cleaned[:6], send_log, report_results))
                elif e_type == "iban":
                    tasks.append(run_iban_osint(e_val, send_log, report_results))
                elif e_type == "inn":
                    tasks.append(run_fns_osint(e_val, send_log, report_results))
                    tasks.append(run_dorking(e_val, send_log, report_results))
            
            # Execute all tasks for this cycle concurrently
            if tasks:
                await send_log(f"[*] Dispatching {len(tasks)} concurrent interceptors for Cycle {cycle_count}...")
                await asyncio.gather(*tasks, return_exceptions=True)
            
            cycle_count += 1
            
        if not entity_queue.empty():
            await send_log("[!] Recursive limits reached (Depth 5). Stopping cascade to prevent infinite loops.")

        # Save to database
        db_dossier = models.SearchDossier(
            query_type=detect_input_type(original_query),
            query_value=original_query,
            results_json=json.dumps(dossier_results)
        )
        db.add(db_dossier)
        db.commit()
        
        await send_log(f"[*] SCAN COMPLETE. Entity mapping finalized. Total modules fired: {len(dossier_results)}")
        await websocket.send_text(json.dumps({"type": "complete", "dossier": dossier_results, "query": original_query, "query_type": detect_input_type(original_query)}))
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"CRITICAL ERROR:\n{tb}")
        try:
            await websocket.send_text(json.dumps({"type": "log", "msg": f"[ERROR] Critical system failure: {repr(e)}"}))
        except Exception:
            pass
