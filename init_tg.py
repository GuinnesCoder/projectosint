from telethon.sync import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv('TG_API_ID')
api_hash = os.getenv('TG_API_HASH')

if not api_id or not api_hash:
    print("[-] TG_API_ID или TG_API_HASH не найдены в .env файле.")
    print("[-] Чтобы их получить, зарегистрируйте приложение на https://my.telegram.org")
    exit(1)

print(f"[+] Подключение к Telegram API (API_ID: {api_id})...")
print("[!] При первом входе потребуется ввести номер телефона и код из Telegram.")

# Создаем файл сессии osint_session.session
with TelegramClient('osint_session', int(api_id), api_hash) as client:
    me = client.get_me()
    print("[+] Отлично! Успешная авторизация в MTProto.")
    print(f"[+] Аккаунт: {me.first_name} (ID: {me.id})")
    print("[+] Теперь веб-приложение сможет выполнять парсинг.")
