from datetime import timedelta, datetime
import pytz
import string
import random
import hashlib
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from info import ADMINS, PREMIUM_LOGS
from utils import get_seconds, temp

# --- Helpers ---

def hash_code(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()

def generate_code(length=12):
    letters_and_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))

# --- Commands ---

@Client.on_message(filters.command("add_redeem") & filters.user(ADMINS))
async def add_redeem_code(client, message):
    if len(message.command) != 3:
        return await message.reply_text("<b>♻ ᴜsᴀɢᴇ:\n\n➩ <code>/add_redeem 1day 5</code>\n➩ <code>/add_redeem 1month 2</code></b>")

    duration, count = message.command[1], message.command[2]
    try:
        count = int(count)
    except ValueError:
        return await message.reply_text("⚠ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ ᴏꜰ ᴄᴏᴅᴇs.")

    seconds = await get_seconds(duration)
    if not seconds:
        return await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ꜰᴏʀᴍᴀᴛ.")

    codes = []
    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    for _ in range(count):
        token = generate_code()
        await db.codes.insert_one({
            "code_hash": hash_code(token),
            "duration": duration,
            "used": False,
            "created_at": now,
            "original_code": token
        })
        codes.append(token)

    codes_text = "\n".join(f"➔ <code>/redeem {c}</code>" for c in codes)
    reply_text = (f"<b>🎉 <u>ɢɪꜰᴛ ᴄᴏᴅᴇs ɢᴇɴᴇʀᴀᴛᴇᴅ ✅</u></b>\n\n🔑 ᴄᴏᴅᴇs: {count}\n\n{codes_text}\n\n⏳ ᴅᴜʀᴀᴛɪᴏɴ: <b>{duration}</b>\n\n🌟 ᴛᴀᴘ ᴄᴏᴅᴇ ᴛᴏ ᴄᴏᴘʏ & sᴇɴᴅ ᴛᴏ ʙᴏᴛ\n\n🚀 ᴇɴᴊᴏʏ ᴘʀᴇᴍɪᴜᴍ 🔥")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔑 ʀᴇᴅᴇᴇᴍ ɴᴏᴡ 🔥", url=f"https://telegram.me/{temp.U_NAME}")]])
    await message.reply_text(reply_text, reply_markup=keyboard)

@Client.on_message(filters.command("redeem"))
async def redeem_code(client, message):
    if len(message.command) != 2:
        return await message.reply_text("⚠ ᴜsᴀɢᴇ: /redeem code")
    code, user_id = message.command[1], message.from_user.id
    entry = await db.codes.find_one({"code_hash": hash_code(code)})
    if not entry:
        return await message.reply_text("🚫 ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ᴄᴏᴅᴇ.")
    if entry["used"]:
        return await message.reply_text("🚫 ᴛʜɪs ᴄᴏᴅᴇ ʜᴀs ᴀʟʀᴇᴀᴅʏ ʙᴇᴇɴ ʀᴇᴅᴇᴇᴍᴇᴅ.")
    seconds = await get_seconds(entry["duration"])
    if not seconds:
        return await message.reply_text("🚫 ɪɴᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ᴄᴏᴅᴇ.")
    data = await db.get_user(user_id)
    now_utc = datetime.now(pytz.utc)
    expiry_time = now_utc + timedelta(seconds=seconds)
    if data and data.get("expiry_time"):
        current_expiry = data["expiry_time"].replace(tzinfo=pytz.utc)
        if current_expiry > now_utc:
            expiry_str = current_expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y ᴀᴛ %I:%M:%S %p")
            return await message.reply_text(f"🚫 ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ.\n\n⏱️ ᴇxᴘɪʀᴇs ᴏɴ: {expiry_str}")
    await db.update_user({"id": user_id, "expiry_time": expiry_time})
    await db.codes.update_one({"_id": entry["_id"]}, {"$set": {"used": True, "user_id": user_id}})
    exp_str = expiry_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y ᴀᴛ %I:%M:%S %p")
    await message.reply_text(f"🎉 <b>ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ 🚀</b>\n\n👤 ᴜsᴇʀ ɪᴅ: <code>{user_id}</code>\n⏳ ᴅᴜʀᴀᴛɪᴏɴ: {entry['duration']}\n⏱️ ᴇxᴘɪʀᴇs ᴏɴ: {exp_str}")
    user = await client.get_users(user_id)
    log_msg = (f"#Redeem_Premium 🔓\n\n👤 {user.mention}\n⚡ ɪᴅ: <code>{user_id}</code>\n⏳ ᴅᴜʀᴀᴛɪᴏɴ: {entry['duration']}\n⏱️ ᴇxᴘɪʀᴇs ᴏɴ: {exp_str}")
    await client.send_message(PREMIUM_LOGS, log_msg)

@Client.on_message(filters.command("clearcodes") & filters.user(ADMINS))
async def clear_codes(c, m):
    res = await db.codes.delete_many({})
    await m.reply(f"✅ ᴅᴇʟᴇᴛᴇᴅ {res.deleted_count} ᴄᴏᴅᴇs." if res.deleted_count else "⚠ ɴᴏ ᴄᴏᴅᴇs ꜰᴏᴜɴᴅ.")

@Client.on_message(filters.command("allcodes") & filters.user(ADMINS))
async def all_codes(c, m):
    codes = await db.codes.find({}).to_list(None)
    if not codes:
        return await m.reply("⚠ ɴᴏ ᴄᴏᴅᴇs ᴀᴠᴀɪʟᴀʙʟᴇ.")

    text = "📝 **ᴀʟʟ ɢᴇɴᴇʀᴀᴛᴇᴅ ᴄᴏᴅᴇs:**\n\n"
    for x in codes:
        user_text = "ɴᴏᴛ ʀᴇᴅᴇᴇᴍᴇᴅ"
        if x.get("user_id"):
            try:
                u = await c.get_users(x["user_id"])
                user_text = f"[{u.first_name}](tg://user?id={u.id})"
            except:
                user_text = f"UID {x['user_id']}"
        text += (f"🔑 `{x.get('original_code','?')}` | ⌛ {x.get('duration','?')} | {'✅' if x.get('used') else '⭕'}\nʙʏ: {user_text} (ID: {x.get('user_id','-')}) | ⏱️ {x['created_at'].astimezone(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y ᴀᴛ %I:%M %p')}\n\n")
    for chunk in [text[i:i+4096] for i in range(0, len(text), 4096)]:
        await m.reply(chunk)
