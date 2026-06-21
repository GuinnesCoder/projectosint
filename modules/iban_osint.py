import re

async def run_iban_osint(iban: str, send_log, report_results):
    await send_log(f"[+] Starting IBAN PARSER & VALIDATOR for: {iban}")
    
    # Clean IBAN
    iban_clean = iban.upper().replace(" ", "")
    
    if len(iban_clean) < 15 or len(iban_clean) > 34:
        await send_log("[-] IBAN: Invalid length. IBAN must be 15-34 characters.")
        return
    
    country_code = iban_clean[:2]
    check_digits = iban_clean[2:4]
    bban = iban_clean[4:]
    
    # IBAN country mapping (common ones)
    country_map = {
        "DE": "Germany", "FR": "France", "GB": "United Kingdom", "ES": "Spain",
        "IT": "Italy", "NL": "Netherlands", "BE": "Belgium", "AT": "Austria",
        "CH": "Switzerland", "PL": "Poland", "PT": "Portugal", "SE": "Sweden",
        "NO": "Norway", "DK": "Denmark", "FI": "Finland", "IE": "Ireland",
        "CZ": "Czech Republic", "RO": "Romania", "HU": "Hungary", "BG": "Bulgaria",
        "HR": "Croatia", "RU": "Russia", "UA": "Ukraine", "KZ": "Kazakhstan",
        "TR": "Turkey", "SA": "Saudi Arabia", "AE": "UAE", "IL": "Israel",
    }
    
    country_name = country_map.get(country_code, f"Unknown ({country_code})")
    
    # IBAN Checksum validation (ISO 7064 Mod 97-10)
    rearranged = bban + country_code + check_digits
    numeric_str = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric_str += ch
        else:
            numeric_str += str(ord(ch) - 55)
    
    is_valid = int(numeric_str) % 97 == 1
    
    await send_log(f"[IBAN] Country: {country_name}")
    await send_log(f"[IBAN] Check Digits: {check_digits}")
    await send_log(f"[IBAN] BBAN (Bank Account): {bban}")
    await send_log(f"[IBAN] Checksum Valid: {'YES ✓' if is_valid else 'NO ✗ — POTENTIALLY FORGED'}")
    
    if not is_valid:
        await send_log("[!] IBAN: CHECKSUM FAILED. This IBAN may be fabricated or contain a typo.")
    
    await report_results("Finance (IBAN Analysis)", {
        "iban": iban_clean,
        "country": country_name,
        "country_code": country_code,
        "check_digits": check_digits,
        "bban": bban,
        "bank_code": bban[:4] if len(bban) >= 4 else bban,
        "checksum_valid": is_valid
    })
