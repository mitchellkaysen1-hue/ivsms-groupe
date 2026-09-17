#!/usr/bin/env python3
"""
IVA SMS Forwarder Bot - API / Dynamic JSON Version
"""
import os
import json
import logging
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== CONFIGURATION ====================
BOT_TOKEN     = "8899248836:AAEkcaRRn5p2-Ly0P8hR2kRXqK8Q9huBWxI"
GROUP_CHAT_ID = -1003919009698

BASE_URL     = "https://www.ivasms.com"
SMS_LIVE_URL = f"{BASE_URL}/portal/live/my_sms"

# আপনার কুকি
IVAS_SESSION = "eyJpdiI6IkdQQU9Wb0k5Yjd1cS9qZFJJQklFWnc9PSIsInZhbHVlIjoiQkRiVUxFNzJ2bVZUSEZQVHFlQnNxNkJKS1Z0Q1dFdnc4eC9CZk02VnZKdGIyVG5RRGVEY0owM3RaNjBmVzNqU2I5bGhGTHBRRXU4eGs5R2plbDBJdDVqcjBsVlhqejROT2FDNW5nTUZNZU9pVzRiSTNuM2JOelM0UFRGajN2alMiLCJtYWMiOiJkNDFlYWE3OWM4M2FjZjU3MmJkZTY3ODQzZDUwZmNjZjE4NTAzN2IwMjEyNDdkMTY3Y2Q3ZjFiNmQ1NzVlZTc5IiwidGFnIjoiIn0%3D"
XSRF_TOKEN   = "eyJpdiI6IlZnQldtU3lwakhsY3JTWFI5S1lLVXc9PSIsInZhbHVlIjoibG1IL1M5RkxDSStEczd5NEFWc3I3RzhhY2x6VVNNMzJtNmU0QS91cDZvUEtGeDJhdnBDbHE5QUFtSTBhR2FiRGpHaXBHaVZvS1Z1ajVNakhYL1N5U2M0T1dqMWVnbjUvMzN2ZkVuTm00dmZXRDg4eWlIbUdBRXQ2TFA5U1lnNlIiLCJtYWMiOiI3ODNlZDRjNWMzMWE4NzNhZTUyMGZlMzBkOGJmOGRhYjRkY2JkMDhkMjk1MzAzZDJjNDExNDZhMDg4MThjZWJlIiwidGFnIjoiIn0%3D"

DB_SEEN_SMS = "db_seen_sms.json"
MONITOR_INTERVAL = 3.0

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger()

global_seen = set()

def load_seen():
    global global_seen
    if os.path.exists(DB_SEEN_SMS):
        try:
            with open(DB_SEEN_SMS, "r") as f:
                global_seen = set(json.load(f))
        except Exception:
            pass

def save_seen():
    try:
        with open(DB_SEEN_SMS, "w") as f:
            json.dump(list(global_seen), f)
    except Exception as e:
        logger.error(f"DB Save Error: {e}")

class IVACookieSession:
    def __init__(self):
        self.session = requests.Session()
        cookie_header = f"ivas_sms_session={IVAS_SESSION}; XSRF-TOKEN={XSRF_TOKEN}"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Cookie': cookie_header,
            'Referer': SMS_LIVE_URL,
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        })

    def fetch_sms(self):
        try:
            res = self.session.get(SMS_LIVE_URL, timeout=15)
            
            if "login" in res.url.lower():
                logger.error("❌ Cookie expired!")
                return [], "EXPIRED"

            results = []

            # ১. সরাসরি JSON রেসপন্স ফিল্টারিং
            try:
                data = res.json()
                items = data if isinstance(data, list) else data.get('data', [])
                for item in items:
                    msg = str(item.get('message', item.get('content', '')))
                    number = str(item.get('number', item.get('phone', '')))
                    sid = str(item.get('sid', item.get('service', '')))
                    
                    if msg:
                        full_info = f"{number} | {sid} | {msg}".strip(" |")
                        uid = str(hash(full_info))
                        results.append({'id': uid, 'full_text': full_info})
            except Exception:
                pass

            # ২. ব্যাকআপ HTML/Table টেক্সট ফিল্টারিং
            if not results:
                soup = BeautifulSoup(res.text, 'html.parser')
                rows = soup.find_all(['tr', 'div', 'li'])
                for row in rows:
                    text = row.get_text(separator=" ", strip=True)
                    # আসল SMS এর টেক্সট কি-ওয়ার্ড ফিল্টার
                    if any(key in text.lower() for key in ['passe', 'code', 'mot de', 'confirmation', 'betwinner', 'facebook']):
                        if "message content" not in text.lower():
                            uid = str(hash(text))
                            results.append({'id': uid, 'full_text': text})

            return results, "OK"
        except Exception as e:
            return [], str(e)

async def monitor_account_task(app: Application):
    iva_session = IVACookieSession()

    while True:
        try:
            new_sms_list, status = await asyncio.to_thread(iva_session.fetch_sms)
            
            if status == "EXPIRED":
                try:
                    await app.bot.send_message(
                        chat_id=GROUP_CHAT_ID,
                        text="⚠️ <b>IVASMS Session Cookie Expired!</b>\nPlease update cookies in code.",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
                await asyncio.sleep(60)
                continue

            for sms in new_sms_list:
                if sms['id'] not in global_seen:
                    global_seen.add(sms['id'])
                    save_seen()
                    logger.info("📩 New SMS Found! Forwarding...")
                    
                    text = (
                        f"🎯 <b>SMS RECEIVED IN YOUR NUMBER!</b>\n\n"
                        f"💬 <code>{sms['full_text']}</code>"
                    )
                    
                    try:
                        await app.bot.send_message(
                            chat_id=GROUP_CHAT_ID,
                            text=text,
                            parse_mode="HTML"
                        )
                    except Exception as send_err:
                        logger.error(f"Telegram Send Error: {send_err}")

        except Exception as e:
            logger.error(f"Monitor Loop Error: {e}")

        await asyncio.sleep(MONITOR_INTERVAL)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ IVA SMS Bot Active!")

async def post_init(application: Application):
    asyncio.create_task(monitor_account_task(application))

if __name__ == "__main__":
    load_seen()
    
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start_cmd))

    logger.info("🚀 IVA Forwarder Bot Starting...")
    app.run_polling(close_loop=True)
