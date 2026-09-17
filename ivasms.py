#!/usr/bin/env python3
"""
Single-Account SMS Monitoring Bot - COOKIE VERSION (IVA)
Converted from SeleniumBase to Requests Session Mode.
"""
import os
import json
import logging
import asyncio
import re
import requests
import traceback
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.error import BadRequest

# ==================== CONFIGURATION ====================
BOT_TOKEN       = "8899248836:AAEkcaRRn5p2-Ly0P8hR2kRXqK8Q9huBWxI"
GROUP_CHAT_ID   = -1003919009698
ADMIN_IDS       = {6394277892}

BASE_URL     = "https://www.ivasms.com"
SMS_LIVE_URL = f"{BASE_URL}/portal/live/my_sms"

# আপনার আপডেট হওয়া কুকি
IVAS_SESSION = "eyJpdiI6IkdQQU9Wb0k5Yjd1cS9qZFJJQklFWnc9PSIsInZhbHVlIjoiQkRiVUxFNzJ2bVZUSEZQVHFlQnNxNkJKS1Z0Q1dFdnc4eC9CZk02VnZKdGIyVG5RRGVEY0owM3RaNjBmVzNqU2I5bGhGTHBRRXU4eGs5R2plbDBJdDVqcjBsVlhqejROT2FDNW5nTUZNZU9pVzRiSTNuM2JOelM0UFRGajN2alMiLCJtYWMiOiJkNDFlYWE3OWM4M2FjZjU3MmJkZTY3ODQzZDUwZmNjZjE4NTAzN2IwMjEyNDdkMTY3Y2Q3ZjFiNmQ1NzVlZTc5IiwidGFnIjoiIn0%3D"
XSRF_TOKEN   = "eyJpdiI6IlZnQldtU3lwakhsY3JTWFI5S1lLVXc9PSIsInZhbHVlIjoibG1IL1M5RkxDSStEczd5NEFWc3I3RzhhY2x6VVNNMzJtNmU0QS91cDZvUEtGeDJhdnBDbHE5QUFtSTBhR2FiRGpHaXBHaVZvS1Z1ajVNakhYL1N5U2M0T1dqMWVnbjUvMzN2ZkVuTm00dmZXRDg4eWlIbUdBRXQ2TFA5U1lnNlIiLCJtYWMiOiI3ODNlZDRjNWMzMWE4NzNhZTUyMGZlMzBkOGJmOGRhYjRkY2JkMDhkMjk1MzAzZDJjNDExNDZhMDg4MThjZWJlIiwidGFnIjoiIn0%3D"

DB_SEEN_SMS      = "db_seen_sms.json"
DB_STATUS        = "db_status.json"
DB_OTP_STATS     = "db_otp_stats.json"
DB_COUNTRY_MAP   = "db_country_map.json"
DB_SERVICE_META  = "db_service_meta.json"

MONITOR_INTERVAL = 2.5

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger()

global_seen    = set()
bot_active     = True
otp_counter    = {}
admin_states   = {}

# ==================== DEFAULT DATA ====================
DEFAULT_SERVICE_META = {
    "facebook":  {"emoji_id": "5323261730283863478", "placeholder": "🔵"},
    "tiktok":    {"emoji_id": "5327982530702359565", "placeholder": "🎵"},
    "whatsapp":  {"emoji_id": "5334998226636390258", "placeholder": "🟢"},
    "telegram":  {"emoji_id": "5319160079465857105", "placeholder": "🔹"},
    "instagram": {"emoji_id": "5319160079465857105", "placeholder": "📸"},
    "default":   {"emoji_id": "5346066456142429527", "placeholder": "📱"},
}

DEFAULT_COUNTRY_MAP = {
    "KAZAKHSTAN": "5222276376161171525", "UKRAINE": "5222250679371839695",
    "TUNISIA": "5221991375016310330",    "PAKISTAN": "5224637061985742245",
    "MOZAMBIQUE": "5222470388423864826", "NIGERIA": "5224723614166691638",
    "ISRAEL": "5224720599099648709",     "IRAQ": "5221980268230882832",
    "ZIMBABWE": "5222060442385397848",   "EGYPT": "5222161185138292290",
    "BANGLADESH": "5224407289825340729", "SRI LANKA": "5224277294050192388",
    "BENIN": "5222024115552009151",      "ETHIOPIA": "5224467805914542024",
    "BELARUS": "5222398507851199882",    "LEBANON": "5222244425899455269",
    "LIBYA": "5222194286451242896",      "KENYA": "5222089648163009103",
    "SUDAN": "5224372990216514135",      "SENEGAL": "5224358988623130949",
    "ALGERIA": "5224260376174015500",    "TAJIKISTAN": "5222217865821696536",
    "MOROCCO": "5224530035695693965",    "INDONESIA": "5224405893960969756",
    "ZAMBIA": "5224646626877911277",     "SIERA LIONE": "5224660718665607511",
    "UNKNOWN": "5281027792148909351",
}

COUNTRY_MAP = {
    "1":"USA/Canada","7":"Russia/Kazakhstan","20":"Egypt","27":"South Africa","30":"Greece",
    "31":"Netherlands","32":"Belgium","33":"France","34":"Spain","36":"Hungary","39":"Italy",
    "40":"Romania","41":"Switzerland","43":"Austria","44":"United Kingdom","45":"Denmark",
    "46":"Sweden","47":"Norway","48":"Poland","49":"Germany","51":"Peru","52":"Mexico",
    "53":"Cuba","54":"Argentina","55":"Brazil","56":"Chile","57":"Colombia","58":"Venezuela",
    "60":"Malaysia","61":"Australia","62":"Indonesia","63":"Philippines","64":"New Zealand",
    "65":"Singapore","66":"Thailand","81":"Japan","82":"South Korea","84":"Vietnam",
    "86":"China","90":"Turkey","91":"India","92":"Pakistan","93":"Afghanistan","94":"Sri Lanka",
    "95":"Myanmar","98":"Iran","211":"South Sudan","212":"Morocco","213":"Algeria","216":"Tunisia",
    "218":"Libya","220":"Gambia","221":"Senegal","222":"Mauritania","223":"Mali","224":"Guinea",
    "225":"Ivory Coast","226":"Burkina Faso","227":"Niger","228":"Togo","229":"Benin","230":"Mauritius",
    "231":"Liberia","232":"Sierra Leone","233":"Ghana","234":"Nigeria","235":"Chad","236":"CAR",
    "237":"Cameroon","238":"Cape Verde","239":"Sao Tome","240":"Equatorial Guinea","241":"Gabon",
    "242":"Congo","243":"DR Congo","244":"Angola","245":"Guinea-Bissau","248":"Seychelles",
    "249":"Sudan","250":"Rwanda","251":"Ethiopia","252":"Somalia","253":"Djibouti","254":"Kenya",
    "255":"Tanzania","256":"Uganda","257":"Burundi","258":"Mozambique","260":"Zambia","261":"Madagascar",
    "262":"Reunion","263":"Zimbabwe","264":"Namibia","265":"Malawi","266":"Lesotho","267":"Botswana",
    "268":"Eswatini","269":"Comoros","291":"Eritrea","297":"Aruba","298":"Faroe Islands","299":"Greenland",
    "350":"Gibraltar","351":"Portugal","352":"Luxembourg","353":"Ireland","354":"Iceland","355":"Albania",
    "356":"Malta","357":"Cyprus","358":"Finland","359":"Bulgaria","370":"Lithuania","371":"Latvia",
    "372":"Estonia","373":"Moldova","374":"Armenia","375":"Belarus","376":"Andorra","377":"Monaco",
    "378":"San Marino","380":"Ukraine","381":"Serbia","382":"Montenegro","383":"Kosovo","385":"Croatia",
    "386":"Slovenia","387":"Bosnia","389":"North Macedonia","420":"Czech Republic","421":"Slovakia",
    "423":"Liechtenstein","501":"Belize","502":"Guatemala","503":"El Salvador","504":"Honduras",
    "505":"Nicaragua","506":"Costa Rica","507":"Panama","509":"Haiti","590":"Guadeloupe","591":"Bolivia",
    "592":"Guyana","593":"Ecuador","595":"Paraguay","597":"Suriname","598":"Uruguay","670":"East Timor",
    "673":"Brunei","674":"Nauru","675":"Papua New Guinea","676":"Tonga","677":"Solomon Islands",
    "678":"Vanuatu","679":"Fiji","680":"Palau","682":"Cook Islands","685":"Samoa","687":"New Caledonia",
    "689":"French Polynesia","691":"Micronesia","692":"Marshall Islands","850":"North Korea","852":"Hong Kong",
    "853":"Macau","855":"Cambodia","856":"Laos","880":"Bangladesh","886":"Taiwan","960":"Maldives",
    "961":"Lebanon","962":"Jordan","963":"Syria","964":"Iraq","965":"Kuwait","966":"Saudi Arabia",
    "967":"Yemen","968":"Oman","970":"Palestine","971":"UAE","972":"Israel","973":"Bahrain",
    "974":"Qatar","975":"Bhutan","976":"Mongolia","977":"Nepal","992":"Tajikistan","993":"Turkmenistan",
    "994":"Azerbaijan","995":"Georgia","996":"Kyrgyzstan","998":"Uzbekistan",
}
ALPHA_MAP = {k: v for k, v in zip(COUNTRY_MAP.keys(), [
    "US","RU","EG","ZA","GR","NL","BE","FR","ES","HU","IT","RO","CH","AT","GB","DK","SE","NO","PL","DE",
    "PE","MX","CU","AR","BR","CL","CO","VE","MY","AU","ID","PH","NZ","SG","TH","JP","KR","VN","CN","TR",
    "IN","PK","AF","LK","MM","IR","SS","MA","DZ","TN","LY","GM","SN","MR","ML","GN","CI","BF","NE","TG",
    "BJ","MU","LR","SL","GH","NG","TD","CF","CM","CV","ST","GQ","GA","CG","CD","AO","GW","SC","SD","RW",
    "ET","SO","DJ","KE","TZ","UG","BI","MZ","ZM","MG","RE","ZW","NA","MW","LS","BW","SZ","KM","ER","AW",
    "FO","GL","GI","PT","LU","IE","IS","AL","MT","CY","FI","BG","LT","LV","EE","MD","AM","BY","AD","MC",
    "SM","UA","RS","ME","XK","HR","SI","BA","MK","CZ","SK","LI","BZ","GT","SV","HN","NI","CR","PA","HT",
    "GP","BO","GY","EC","PY","SR","UY","TL","BN","NR","PG","TO","SB","VU","FJ","PW","CK","WS","NC","PF",
    "FM","MH","KP","HK","MO","KH","LA","BD","TW","MV","LB","JO","SY","IQ","KW","SA","YE","OM","PS","AE",
    "IL","BH","QA","BT","MN","NP","TJ","TM","AZ","GE","KG","UZ",
])}

# ==================== DATA PERSISTENCE ====================
def load_databases():
    global global_seen, bot_active, otp_counter, DEFAULT_COUNTRY_MAP, DEFAULT_SERVICE_META
    if os.path.exists(DB_SEEN_SMS):
        try:
            with open(DB_SEEN_SMS) as f: global_seen = set(json.load(f))
        except: pass
    if os.path.exists(DB_STATUS):
        try:
            with open(DB_STATUS) as f: bot_active = json.load(f).get("active", True)
        except: pass
    if os.path.exists(DB_OTP_STATS):
        try:
            with open(DB_OTP_STATS) as f: otp_counter.update(json.load(f))
        except: pass
    if os.path.exists(DB_COUNTRY_MAP):
        try:
            with open(DB_COUNTRY_MAP) as f: DEFAULT_COUNTRY_MAP.update(json.load(f))
        except: pass
    if os.path.exists(DB_SERVICE_META):
        try:
            with open(DB_SERVICE_META) as f: DEFAULT_SERVICE_META.update(json.load(f))
        except: pass

def save_databases():
    with open(DB_SEEN_SMS,     "w") as f: json.dump(list(global_seen), f)
    with open(DB_STATUS,       "w") as f: json.dump({"active": bot_active}, f)
    with open(DB_OTP_STATS,    "w") as f: json.dump(otp_counter, f, indent=2)
    with open(DB_COUNTRY_MAP,  "w") as f: json.dump(DEFAULT_COUNTRY_MAP, f, indent=2)
    with open(DB_SERVICE_META, "w") as f: json.dump(DEFAULT_SERVICE_META, f, indent=2)

# ==================== COOKIE SCRAPER ====================
class IVACookieFetcher:
    def __init__(self):
        self.session = requests.Session()
        cookie_header = f"ivas_sms_session={IVAS_SESSION}; XSRF-TOKEN={XSRF_TOKEN}"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Cookie': cookie_header,
            'Referer': SMS_LIVE_URL,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })

    def fetch_sms(self):
        try:
            res = self.session.get(SMS_LIVE_URL, timeout=15)
            if "login" in res.url.lower():
                return [], "EXPIRED"

            soup = BeautifulSoup(res.text, 'html.parser')
            results = []
            rows = soup.find_all('tr')

            for row in rows:
                tds = row.find_all('td')
                if len(tds) < 3:
                    continue

                if "Message content" in row.get_text():
                    continue

                recipient = tds[0].text.strip().replace('\n', ' ')
                sender    = tds[1].text.strip() if len(tds) > 1 else 'Unknown'
                message   = tds[-1].text.strip().replace('\n', ' ')

                if recipient:
                    results.append({
                        'recipient': recipient,
                        'sender': sender,
                        'message': message,
                        'sid_service': sender
                    })

            return results, "OK"
        except Exception as e:
            return [], str(e)

# ==================== CORE MONITOR ENGINE ====================
async def monitor_account(bot):
    fetcher = IVACookieFetcher()
    logger.info("✅ Cookie Monitor initialized & ready.")

    while True:
        try:
            if not bot_active:
                await asyncio.sleep(5)
                continue

            new_sms_list, status = await asyncio.to_thread(fetcher.fetch_sms)

            if status == "EXPIRED":
                logger.warning("⚠️ Cookie Expired!")
                await asyncio.sleep(60)
                continue

            for sms in new_sms_list:
                uid = f"{sms['recipient']}_{sms['sender']}_{sms['message']}"
                if uid not in global_seen:
                    global_seen.add(uid)
                    save_databases()
                    otp_counter["TOTAL"] = otp_counter.get("TOTAL", 0) + 1
                    logger.info(f"📤 New OTP: {sms['recipient']} - {sms['sender']}")
                    
                    asyncio.create_task(deliver_sms(
                        bot, GROUP_CHAT_ID,
                        sms["recipient"], sms["sender"],
                        sms["message"], sms.get("sid_service", "")
                    ))

        except Exception as e:
            logger.error(f"Monitor loop error: {e}\n{traceback.format_exc()}")

        await asyncio.sleep(MONITOR_INTERVAL)

# ==================== SMS DELIVERY ====================
async def deliver_sms(bot, chat_id, recipient, sender, message, sid_service=""):
    try:
        # Extract OTP Code / Password
        otp_match = re.search(r'\b\d{4,8}\b', message)
        if otp_match:
            otp = otp_match.group(0)
        else:
            match_pass = re.search(r'Pass\s*:?\s*(\S+)', message, re.IGNORECASE)
            otp = match_pass.group(1) if match_pass else "N/A"

        digits = re.sub(r'\D', '', str(recipient))
        c_name, a2, flag = "Global", "XX", "🌐"
        for length in range(1, 4):
            cc = digits[:length]
            if cc in COUNTRY_MAP:
                c_name = COUNTRY_MAP[cc]
                a2     = ALPHA_MAP.get(cc, "XX")
                flag   = ''.join(chr(0x1F1E6 + ord(ch) - ord('A')) for ch in a2)
                break

        svc_raw        = sender.strip()
        svc_key_lookup = svc_raw.lower()
        matched_svc_key = "default"
        if svc_key_lookup in DEFAULT_SERVICE_META:
            matched_svc_key = svc_key_lookup
        else:
            for key in DEFAULT_SERVICE_META:
                if key != "default" and key in svc_key_lookup:
                    matched_svc_key = key
                    break
        service_name = svc_raw if svc_raw else matched_svc_key.upper()

        if len(digits) >= 9:
            masked = f"{digits[:5]}****{digits[-4:]}"
        elif len(digits) >= 6:
            masked = f"{digits[:2]}****{digits[-2:]}"
        else:
            masked = f"****{digits}"

        text = (
            f"RCV JIR\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"{flag} ᴄᴏᴜɴᴛʀʏ: {c_name}\n"
            f"☎️ ɴᴜᴍʙᴇʀ: <code>{masked}</code>\n"
            f"🛠️ sᴇʀᴠɪᴄᴇ: {service_name.upper()}\n"
            f"💬 ᴍᴇssᴀɢᴇ: <code>{message}</code>\n"
            f"🔑 sʏsᴛᴇᴍ ᴄᴏᴅᴇ: <code>{otp}</code>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        )

        keyboard = {
            "inline_keyboard": [[
                {"text": "𝐎𝐓𝐏", "copy_text": {"text": str(otp)}},
                {"text": "𝐁𝐎𝐓 𝐋𝐈𝐍𝐊", "url": "https://t.me/fortestonly99_bot"}
            ]]
        }

        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        logger.info(f"✅ OTP sent successfully for {recipient}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to deliver OTP: {e}\n{traceback.format_exc()}")
        return False

# ==================== ADMIN PANEL ====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access Denied.")
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Add Country Emoji", callback_data="add_country")],
        [InlineKeyboardButton("🛠️ Add Service Emoji", callback_data="add_service")],
    ])
    await update.message.reply_text(
        "✨ <b>IVA SMS Admin Control Panel</b>", reply_markup=kb, parse_mode="HTML"
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    user_id = query.from_user.id
    if user_id not in ADMIN_IDS:
        try: await query.answer("Access Denied!", show_alert=True)
        except BadRequest: pass
        return
    await query.answer()
    if query.data == "add_country":
        admin_states[user_id] = "waiting_country"
        await query.edit_message_text(
            "Send the country name or dial code with custom emoji ID:\n<code>BANGLADESH:5224407289825340729</code>",
            parse_mode="HTML"
        )
    elif query.data == "add_service":
        admin_states[user_id] = "waiting_service"
        await query.edit_message_text(
            "Send the service name with custom emoji ID:\n<code>whatsapp:5334998226636390258</code>",
            parse_mode="HTML"
        )

async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS or user_id not in admin_states:
        return
    state = admin_states[user_id]
    txt   = update.message.text.strip()
    if ":" not in txt:
        await update.message.reply_text("Invalid format. Use <code>NAME:EMOJI_ID</code>.", parse_mode="HTML")
        return
    name, emoji_id = txt.split(":", 1)
    name, emoji_id = name.strip(), emoji_id.strip()

    if state == "waiting_country":
        DEFAULT_COUNTRY_MAP[name.upper()] = emoji_id
        save_databases()
        del admin_states[user_id]
        await update.message.reply_text(f"✅ <b>{name.upper()}</b> linked.", parse_mode="HTML")
    elif state == "waiting_service":
        DEFAULT_SERVICE_META[name.lower()] = {"emoji_id": emoji_id, "placeholder": "📱"}
        save_databases()
        del admin_states[user_id]
        await update.message.reply_text(f"✅ <b>{name.lower()}</b> linked.", parse_mode="HTML")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    try:
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text="🧪 Test message active!")
        await update.message.reply_text("✅ Test message sent.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")

async def post_init(application: Application):
    asyncio.create_task(monitor_account(application.bot))

# ==================== MAIN ENTRY ====================
if __name__ == "__main__":
    load_databases()

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", admin_panel))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_message_handler))

    logger.info("🚀 IVA Cookie SMS Bot started successfully.")
    app.run_polling(close_loop=True)
