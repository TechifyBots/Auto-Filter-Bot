import re
import asyncio
import logging
import json
import html
from calendar import month_name
import aiohttp
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.errors import MessageNotModified, MessageTooLong
from .poster import get_movie_detailsx
from info import ADMINS, UPDATE_CHANNEL, ABOVE_PREVIEW
from utils import temp

logger = logging.getLogger(__name__)
post_sessions = {}

USE_DEFAULT_BTN = True
DEFAULT_BTN_LINK = "https://telegram.me/Techifybots"
DEFAULT_WATERMARK = "<blockquote><b><i>ʙʏ - @TechifyBots</i></b></blockquote>"
LANGUAGES_FORMAT = "<b>‣ ᴀᴜᴅɪᴏ :</b> {langs}"
SUBTITLES_FORMAT = "<b>‣ sᴜʙᴛɪᴛʟᴇ :</b> {subs}"
RESOLUTIONS_FORMAT = "<b>‣ ǫᴜᴀʟɪᴛʏ :</b> {resolutions}"
OTT_FORMAT = "<b>‣ sᴛʀᴇᴀᴍɪɴɢ ᴏɴ :</b> {otts}"
RESOLUTIONS = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p (4K)", "HDRip", "HDTV", "WEBRip", "WEB-DL", "VOD", "DVDRip", "BDRip", "BluRay", "HEVC", "CAM"]
LANGUAGES = ["Hindi", "English", "Japanese", "Tamil", "Telugu", "Malayalam", "Kannada", "Marathi", "Punjabi", "Gujarati", "Bengali", "Urdu", "Korean", "Chinese", "Arabic", "French", "German", "Italian", "Portuguese", "Russian", "Spanish"]
SUBTITLES = LANGUAGES.copy()
OTT_PLATFORMS = ["Netflix", "Prime Video", "Crunchyroll", "JioHotstar", "Amazon MX Player", "Zee5", "SonyLIV", "Voot", "Aha", "Hoichoi", "ALTBalaji", "Apple TV+", "HBO Max", "Hulu", "Paramount+", "Peacock", "Discovery+", "YouTube"]

ANILIST_MEDIA_QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME) {
    title { romaji english }
    format
    status
    season
    seasonYear
    description(asHtml: true)
    genres
    averageScore
    episodes
    studios { edges { isMain node { name } } }
    coverImage { extraLarge large }
    siteUrl
  }
}
"""

TEMPLATES = {
    "classic_emoji": """<b>{title} ({year})</b>
⭐️ <b>ʀᴀᴛɪɴɢ :</b> {rating}/10
🎭 <b>ɢᴇɴʀᴇꜱ :</b> {genres}""",

    "minimalist": """<blockquote><b>{title}</b></blockquote>

<b>‣ ʏᴇᴀʀ :</b> {year}
<b>‣ ʀᴀᴛɪɴɢ :</b> {rating}
<b>‣ ɢᴇɴʀᴇꜱ :</b> {genres}""",

    "sparkle_header": """✨ <b>{title}</b> ✨

<b>🗓 ʏᴇᴀʀ :</b> {year} | <b>⭐️ ʀᴀᴛɪɴɢ :</b> {rating}/10
<b>🎭 ɢᴇɴʀᴇꜱ :</b> {genres}""",

    "markdown_style": """🎥 **{title}** ({year})

- **ʀᴀᴛɪɴɢ** : {rating} / 10 🌟
- **ɢᴇɴʀᴇꜱ** : {genres}""",

    "divider_list": """🎬 <b>{title} {year}</b>
━━━━━━━━━━━━━━━━━━
➥ <b>ʀᴀᴛɪɴɢ :</b> <code>★ {rating}/10</code>
➥ <b>ɢᴇɴʀᴇꜱ :</b> <code>{genres}</code>""",

    "dashed_box": """- - - - - - - - - - - - - - - - - -
🎥 <b>{title}</b>
- - - - - - - - - - - - - - - - - -

➛ <b>ʏᴇᴀʀ ∥</b> {year}
➛ <b>ʀᴀᴛɪɴɢ ∥</b> {rating}/10
➛ <b>ɢᴇɴʀᴇꜱ ∥</b> {genres}""",

    "chevron_details": """<b>{title}</b>

» <b>ʏᴇᴀʀ ➣</b> {year}
» <b>ʀᴀᴛɪɴɢ ➣</b> ★ {rating}/10
» <b>ɢᴇɴʀᴇꜱ ➣</b> {genres}""",

    "bullet_points": """✨ <b><u>{title} ({year})</u></b> ✨

● <b>ʀᴀᴛɪɴɢ :</b> {rating}/10
● <b>ɢᴇɴʀᴇꜱ :</b> {genres}""",

    "clean_grid": """🎬 {title} ({year})

🗓️ <b>ʏᴇᴀʀ ∥</b> {year}
⭐️ <b>ʀᴀᴛɪɴɢ ∥</b> {rating}/10
🎭 <b>ɢᴇɴʀᴇꜱ ∥</b> {genres}"""
}

async def anilist_get_media(title):
    async with aiohttp.ClientSession() as session:
        r = await session.post("https://graphql.anilist.co", json={"query": ANILIST_MEDIA_QUERY, "variables": {"search": title}})
        return await r.read()

def shorten_description(desc, url="https://anilist.co"):
    desc = desc.replace("<br>", "").replace("</br>", "").replace("<i>", "").replace("</i>", "")
    if len(desc) > 700:
        return f"\n\n<blockquote expandable><strong>‣ ᴏᴠᴇʀᴠɪᴇᴡ :</strong> <em>{desc[:500]}....<strong><a href=\"{url}\">𝖬𝗈𝗋𝖾 𝖨𝗇𝖿𝗈</a></strong></em></blockquote>"
    return f"\n\n<blockquote expandable><strong>‣ ᴏᴠᴇʀᴠɪᴇᴡ :</strong> <em>{desc}</em></blockquote>"

async def handle_add_get_files(s):
    m = s.get("movie_details") or {}
    title = m.get("title", "movie"); year = m.get("year", "")
    slug = f"{title} {year}".strip().replace(" ", "-")
    s["buttons"].append([InlineKeyboardButton("📥 𝖦𝖾𝗍 𝖥𝗂𝗅𝖾𝗌 📥", url=f"https://telegram.me/{temp.U_NAME}?start=getfile-{slug}")])

async def handle_edit_caption(client: Client, query: CallbackQuery, s: dict):
    r = await get_user_input(client, query, s, "📝 𝖲𝖾𝗇𝖽 𝗍𝗁𝖾 𝗇𝖾𝗐 𝖼𝖺𝗉𝗍𝗂𝗈𝗇 𝗍𝖾𝗑𝗍.")
    if r and r.text:
        s["caption"] = r.text

async def handle_set_poster(client: Client, query: CallbackQuery, s: dict):
    r = await get_user_input(client, query, s, "🖼️ 𝖲𝖾𝗇𝖽 𝖺 𝗉𝗁𝗈𝗍𝗈 𝗈𝗋 𝗂𝗆𝖺𝗀𝖾 𝖴𝖱𝖫.\n𝖴𝗌𝖾 `/reset` 𝗍𝗈 𝗋𝖾𝗌𝗍𝗈𝗋𝖾 𝗍𝗁𝖾 𝖽𝖾𝖿𝖺𝗎𝗅𝗍 𝗉𝗈𝗌𝗍𝖾𝗋.")
    if r:
        if r.photo:
            s["custom_poster"] = r.photo.file_id
            if not s["photo_mode"]:
                s["photo_mode"] = True
                await query.answer("✅ 𝖲𝗐𝗂𝗍𝖼𝗁𝖾𝖽 𝗍𝗈 𝖯𝗁𝗈𝗍𝗈 𝗆𝗈𝖽𝖾 𝖺𝗎𝗍𝗈𝗆𝖺𝗍𝗂𝖼𝖺𝗅𝗅𝗒.", show_alert=True)
        elif r.text and r.text.startswith("http"):
            s["custom_poster"] = r.text
        elif r.text and r.text == "/reset":
            s["custom_poster"] = None
    return True

async def handle_set_watermark(client, query, s):
    r = await get_user_input(client, query, s, "💧 𝖲𝖾𝗇𝖽 𝗍𝗁𝖾 𝗐𝖺𝗍𝖾𝗋𝗆𝖺𝗋𝗄 𝗍𝖾𝗑𝗍.\n• `/reset` 𝗍𝗈 𝗋𝖾𝗆𝗈𝗏𝖾\n• `/default` 𝗍𝗈 𝗎𝗌𝖾 𝗍𝗁𝖾 𝖽𝖾𝖿𝖺𝗎𝗅𝗍 𝗐𝖺𝗍𝖾𝗋𝗆𝖺𝗋𝗄")
    if r and r.text:
        if r.text == "/reset":
            s["watermark"] = ""
        elif r.text == "/default":
            s["watermark"] = DEFAULT_WATERMARK
        else:
            s["watermark"] = r.text

async def handle_format_lang(client, query, s):
    r = await get_user_input(client, query, s, "🗣️ 𝖲𝖾𝗇𝖽 𝗍𝗁𝖾 𝖿𝗈𝗋𝗆𝖺𝗍 𝖿𝗈𝗋 𝖺𝗎𝖽𝗂𝗈. 𝖴𝗌𝖾 `{langs}`.\n`/reset` 𝗍𝗈 𝗋𝖾𝗌𝗍𝗈𝗋𝖾 𝖽𝖾𝖿𝖺𝗎𝗅𝗍.\n\n𝖢𝗎𝗋𝗋𝖾𝗇𝗍: " + s["lang_format"])
    if r and r.text:
        s["lang_format"] = LANGUAGES_FORMAT if r.text == "/reset" else r.text

async def handle_format_sub(client, query, s):
    r = await get_user_input(client, query, s, "📄 𝖲𝖾𝗇𝖽 𝗍𝗁𝖾 𝖿𝗈𝗋𝗆𝖺𝗍 𝖿𝗈𝗋 𝗌𝗎𝖻𝗍𝗂𝗍𝗅𝖾𝗌. 𝖴𝗌𝖾 `{subs}`.\n`/reset` 𝗍𝗈 𝗋𝖾𝗌𝗍𝗈𝗋𝖾 𝖽𝖾𝖿𝖺𝗎𝗅𝗍.\n\n𝖢𝗎𝗋𝗋𝖾𝗇𝗍: " + s["sub_format"])
    if r and r.text:
        s["sub_format"] = SUBTITLES_FORMAT if r.text == "/reset" else r.text

async def handle_format_res(client, query, s):
    r = await get_user_input(client, query, s, "📺 𝖲𝖾𝗇𝖽 𝗍𝗁𝖾 𝖿𝗈𝗋𝗆𝖺𝗍 𝖿𝗈𝗋 𝗊𝗎𝖺𝗅𝗂𝗍𝗂𝖾𝗌. 𝖴𝗌𝖾 `{resolutions}`.\n`/reset` 𝗍𝗈 𝗋𝖾𝗌𝗍𝗈𝗋𝖾 𝖽𝖾𝖿𝖺𝗎𝗅𝗍.\n\n𝖢𝗎𝗋𝗋𝖾𝗇𝗍: " + s["res_format"])
    if r and r.text:
        s["res_format"] = RESOLUTIONS_FORMAT if r.text == "/reset" else r.text

async def handle_format_ott(client, query, s):
    r = await get_user_input(client, query, s, "🌐 𝖲𝖾𝗇𝖽 𝗍𝗁𝖾 𝖿𝗈𝗋𝗆𝖺𝗍 𝖿𝗈𝗋 𝖮𝖳𝖳. 𝖴𝗌𝖾 `{otts}`.\n`/reset` 𝗍𝗈 𝗋𝖾𝗌𝗍𝗈𝗋𝖾 𝖽𝖾𝖿𝖺𝗎𝗅𝗍.\n\n𝖢𝗎𝗋𝗋𝖾𝗇𝗍: " + s["ott_format"])
    if r and r.text:
        s["ott_format"] = OTT_FORMAT if r.text == "/reset" else r.text

async def handle_templates_menu(query, s):
    buttons = []
    for name in TEMPLATES:
        text = f"✅ {name}" if s.get("active_template") == name else name
        buttons.append([InlineKeyboardButton(text, callback_data=f"post:select_template:{query.from_user.id}:{name}")])
    buttons.append([InlineKeyboardButton("🔙 𝖡𝖺𝖼𝗄", callback_data=f"post:back:{query.from_user.id}")])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))

async def handle_select_template(s, template_name):
    s["active_template"] = template_name
    s["caption"] = None

async def handle_remove_buttons_menu(query, s):
    buttons = []
    for i, row in enumerate(s["buttons"]):
        for j, btn in enumerate(row):
            buttons.append([InlineKeyboardButton(f"❌ {btn.text}", callback_data=f"post:remove_button:{query.from_user.id}:{i}:{j}")])
    if not buttons:
        buttons.append([InlineKeyboardButton("🚫 𝖭𝗈 𝖻𝗎𝗍𝗍𝗈𝗇𝗌 𝗍𝗈 𝗋𝖾𝗆𝗈𝗏𝖾", callback_data="noop")])
    buttons.append([InlineKeyboardButton("🔙 𝖡𝖺𝖼𝗄", callback_data=f"post:back:{query.from_user.id}")])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))

async def handle_edit_buttons(client: Client, query: CallbackQuery, s: dict):
    r = await get_user_input(client, query, s, "🪄 𝖲𝖾𝗇𝖽 𝗒𝗈𝗎𝗋 𝖻𝗎𝗍𝗍𝗈𝗇 𝗅𝖺𝗒𝗈𝗎𝗍.\n\n💡 𝖥𝗈𝗋 𝗌𝖺𝗆𝖾 𝗋𝗈𝗐:\n`Text - URL | Text2 - URL2`\n\n💡 𝖥𝗈𝗋 𝖺 𝗇𝖾𝗐 𝗋𝗈𝗐:\n`Text3 - URL3`")
    if r and r.text:
        rows = []
        for row in r.text.strip().split('\n'):
            btns = [InlineKeyboardButton(text.strip(), url=url.strip()) for chunk in row.split('|') if ' - ' in chunk for text, url in [chunk.split(' - ', 1)]]
            if btns: rows.append(btns)

async def show_selection_menu(query: CallbackQuery, session_id: int, menu_type: str):
    s = post_sessions[session_id]
    if menu_type == "languages":
        items, selected, action_prefix, fmt = (LANGUAGES, s["custom_languages"], "select_lang", "format_lang")
    elif menu_type == "subtitles":
        items, selected, action_prefix, fmt = (SUBTITLES, s["custom_subtitles"], "select_sub", "format_sub")
    elif menu_type == "resolutions":
        items, selected, action_prefix, fmt = (RESOLUTIONS, s["custom_resolutions"], "select_res", "format_res")
    elif menu_type == "otts":
        items, selected, action_prefix, fmt = (OTT_PLATFORMS, s["custom_otts"], "select_ott", "format_ott")
    else:
        return
    btns = [InlineKeyboardButton(("✅ " + i) if i in selected else i, callback_data=f"post:{action_prefix}:{session_id}:{i}") for i in items]
    kb = [btns[i:i+3] for i in range(0, len(btns), 3)]
    kb.append([InlineKeyboardButton("⚙️ 𝖢𝗁𝖺𝗇𝗀𝖾 𝖥𝗈𝗋𝗆𝖺𝗍", callback_data=f"post:{fmt}:{session_id}")])
    kb.append([InlineKeyboardButton("✅ 𝖣𝗈𝗇𝖾", callback_data=f"post:back:{session_id}")])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(kb))

async def get_user_input(client, query, s, prompt_text):
    ask = await query.message.reply_text(prompt_text, reply_to_message_id=s.get("original_message_id"))
    try:
        r = await client.listen(chat_id=query.message.chat.id, user_id=query.from_user.id, timeout=300)
        await ask.delete()
        if r:
            await r.delete()
            return r
    except asyncio.TimeoutError:
        await ask.edit("Timeout (5 minutes). Operation cancelled.")
        await asyncio.sleep(5)
        await ask.delete()
    return None

async def handle_buttons_menu(query, sid):
    kb = [
        [InlineKeyboardButton("➕ 𝖠𝖽𝖽/𝖤𝖽𝗂𝗍 𝖫𝖺𝗒𝗈𝗎𝗍", callback_data=f"post:edit_buttons:{sid}")],
        [InlineKeyboardButton("📥 𝖠𝖽𝖽 '𝖦𝖾𝗍 𝖥𝗂𝗅𝖾𝗌' 𝖡𝗎𝗍𝗍𝗈𝗇", callback_data=f"post:add_get_files:{sid}")],
        [InlineKeyboardButton("🗑️ 𝖱𝖾𝗆𝗈𝗏𝖾 𝖺 𝖡𝗎𝗍𝗍𝗈𝗇", callback_data=f"post:remove_buttons_menu:{sid}")],
        [InlineKeyboardButton("🔙 𝖡𝖺𝖼𝗄", callback_data=f"post:back:{sid}")]
    ]
    await query.edit_message_reply_markup(InlineKeyboardMarkup(kb))

async def handle_remove_button(s, extra):
    try:
        row_i, col_i = int(extra[0]), int(extra[1])
        s["buttons"][row_i].pop(col_i)
        if not s["buttons"][row_i]:
            s["buttons"].pop(row_i)
    except (IndexError, ValueError):
        logger.warning("⚠️ 𝖳𝗋𝗂𝖾𝖽 𝗍𝗈 𝗋𝖾𝗆𝗈𝗏𝖾 𝖺 𝖻𝗎𝗍𝗍𝗈𝗇 𝗍𝗁𝖺𝗍 𝖽𝗈𝖾𝗌 𝗇𝗈𝗍 𝖾𝗑𝗂𝗌𝗍.")

async def handle_toggle_preview(query: CallbackQuery, s: dict):
    if s.get("custom_poster") and not s["custom_poster"].startswith("http"):
        await query.answer("⚠️ 𝖢𝖺𝗇𝗇𝗈𝗍 𝗌𝗐𝗂𝗍𝖼𝗁 𝗍𝗈 𝖳𝖾𝗑𝗍 𝗆𝗈𝖽𝖾 𝗐𝗁𝗂𝗅𝖾 𝗎𝗌𝗂𝗇𝗀 𝖺𝗇 𝗎𝗉𝗅𝗈𝖺𝖽𝖾𝖽 𝗉𝗁𝗈𝗍𝗈.", show_alert=True)
        return False
    s["photo_mode"] = not s["photo_mode"]
    return True

async def handle_toggle_poster(s):
    s["use_landscape"] = not s["use_landscape"]
    if s.get("is_anipost"):
        s["custom_poster"] = None
    return True

async def handle_cancel(client: Client, query: CallbackQuery, sid: int, _=None):
    s = post_sessions.pop(sid, None)
    if s and s.get("last_preview_message_id"):
        await client.delete_messages(query.message.chat.id, s["last_preview_message_id"])
    await query.message.reply_to_message.reply_text("❌ 𝖯𝗈𝗌𝗍 𝖼𝗋𝖾𝖺𝗍𝗂𝗈𝗇 𝖼𝖺𝗇𝖼𝖾𝗅𝗅𝖾𝖽.")

async def finalize_and_post(client: Client, query: CallbackQuery, sid: int, _=None):
    s = post_sessions.pop(sid, None)
    if not s:
        logger.warning(f"Finalize called for an expired or invalid session_id: {sid}")
        return
    await client.delete_messages(query.message.chat.id, s["last_preview_message_id"])
    status = await query.message.reply_to_message.reply_text("⏳ <i>𝖥𝗂𝗇𝖺𝗅𝗂𝗓𝗂𝗇𝗀 𝖺𝗇𝖽 𝗉𝗈𝗌𝗍𝗂𝗇𝗀...</i>")
    text, _, poster = await build_final_post_content(s, sid)
    kb = InlineKeyboardMarkup(s["buttons"]) if s["buttons"] else None
    if not text:
        logger.error(f"Failed to fetch details for '{s['movie_name']}' during finalization.")
        return await status.edit("⚠️ 𝖢𝗈𝗎𝗅𝖽 𝗇𝗈𝗍 𝖿𝖾𝗍𝖼𝗁 𝖽𝖾𝗍𝖺𝗂𝗅𝗌 𝗍𝗈 𝗉𝗈𝗌𝗍. 𝖠𝖻𝗈𝗋𝗍𝗂𝗇𝗀.")
    mode = "Photo" if s["photo_mode"] and poster else "Text"
    logger.info(f"Finalizing post for '{s['movie_name']}'. Mode: {mode}")
    try:
        if mode == "Photo":
            await client.send_photo(chat_id=UPDATE_CHANNEL, photo=poster, caption=text, reply_markup=kb)
        else:
            t = f"<a href='{poster}'>&#8205;</a>{text}" if poster else text
            await client.send_message(chat_id=UPDATE_CHANNEL, text=t, reply_markup=kb, disable_web_page_preview=False, invert_media=ABOVE_PREVIEW)
        await status.edit("✅ 𝖯𝗈𝗌𝗍𝖾𝖽 𝗌𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒.")
    except MessageTooLong:
        await status.edit("⚠️ <b>𝖯𝗈𝗌𝗍 𝖥𝖺𝗂𝗅𝖾𝖽</b>\n\n𝖢𝖺𝗉𝗍𝗂𝗈𝗇 𝖾𝗑𝖼𝖾𝖾𝖽𝗌 4096 𝖼𝗁𝖺𝗋𝖺𝖼𝗍𝖾𝗋𝗌. 𝖯𝗅𝖾𝖺𝗌𝖾 𝗌𝗁𝗈𝗋𝗍𝖾𝗇 𝖺𝗇𝖽 𝗍𝗋𝗒 𝖺𝗀𝖺𝗂𝗇.")
    except Exception as e:
        await status.edit(f"❌ 𝖥𝖺𝗂𝗅𝖾𝖽 𝗍𝗈 𝗉𝗈𝗌𝗍 𝗍𝗈 𝗎𝗉𝖽𝖺𝗍𝖾 𝖼𝗁𝖺𝗇𝗇𝖾𝗅.\n<b>𝖤𝗋𝗋𝗈𝗋:</b> <code>{e}</code>")
        logger.error("Unexpected error while posting.", exc_info=True)

def build_keyboard(session: dict, session_id: int):
    rows = []
    if session.get("buttons"):
        rows.extend(session["buttons"])
    rows.append([
        InlineKeyboardButton("✏️ 𝖡𝗎𝗍𝗍𝗈𝗇𝗌", callback_data=f"post:buttons_menu:{session_id}"),
        InlineKeyboardButton("📝 𝖢𝖺𝗉𝗍𝗂𝗈𝗇", callback_data=f"post:edit_caption:{session_id}"),
        InlineKeyboardButton("🖼️ 𝖯𝗈𝗌𝗍𝖾𝗋", callback_data=f"post:set_poster:{session_id}")
    ])
    if not session.get("is_anipost"):
        rows.append([
            InlineKeyboardButton("✨ 𝖳𝖾𝗆𝗉𝗅𝖺𝗍𝖾𝗌", callback_data=f"post:templates:{session_id}"),
            InlineKeyboardButton("💧 𝖶𝖺𝗍𝖾𝗋𝗆𝖺𝗋𝗄", callback_data=f"post:set_watermark:{session_id}"),
            InlineKeyboardButton("📺 𝖰𝗎𝖺𝗅𝗂𝗍𝗂𝖾𝗌", callback_data=f"post:resolutions:{session_id}")
        ])
    else:
        rows.append([
            InlineKeyboardButton("💧 𝖶𝖺𝗍𝖾𝗋𝗆𝖺𝗋𝗄", callback_data=f"post:set_watermark:{session_id}"),
            InlineKeyboardButton("📺 𝖰𝗎𝖺𝗅𝗂𝗍𝗂𝖾𝗌", callback_data=f"post:resolutions:{session_id}")
        ])
    rows.append([
        InlineKeyboardButton("🗣️ 𝖠𝗎𝖽𝗂𝗈", callback_data=f"post:languages:{session_id}"),
        InlineKeyboardButton("📄 𝖲𝗎𝖻𝗍𝗂𝗍𝗅𝖾𝗌", callback_data=f"post:subtitles:{session_id}"),
        InlineKeyboardButton("🌐 𝖮𝖳𝖳", callback_data=f"post:otts:{session_id}")
    ])
    rows.append([
        InlineKeyboardButton(f"𝖬𝗈𝖽𝖾: {'𝖯𝗁𝗈𝗍𝗈' if session['photo_mode'] else '𝖳𝖾𝗑𝗍'}", callback_data=f"post:toggle_preview:{session_id}"),
        InlineKeyboardButton(f"𝖯𝗈𝗌𝗍𝖾𝗋: {'𝖫𝖺𝗇𝖽𝗌𝖼𝖺𝗉𝖾' if session['use_landscape'] else '𝖯𝗈𝗋𝗍𝗋𝖺𝗂𝗍'}", callback_data=f"post:toggle_poster:{session_id}")
    ])
    rows.append([
        InlineKeyboardButton("✅ 𝖯𝗈𝗌𝗍", callback_data=f"post:finalize:{session_id}"),
        InlineKeyboardButton("❌ 𝖢𝖺𝗇𝖼𝖾𝗅", callback_data=f"post:cancel:{session_id}")
    ])
    return InlineKeyboardMarkup(rows)

async def start_post_session(client: Client, message: Message, user_id: int, movie_name: str):
    movie_details = await get_movie_detailsx(movie_name)
    if not movie_details:
        return await message.reply_text("⚠️ 𝖮𝗈𝗉𝗌! 𝖨 𝖼𝗈𝗎𝗅𝖽𝗇’𝗍 𝖿𝖾𝗍𝖼𝗁 𝗍𝗁𝖾 𝖽𝖾𝗍𝖺𝗂𝗅𝗌.")
    if user_id in post_sessions and post_sessions[user_id].get("last_preview_message_id"):
        try:
            await client.delete_messages(message.chat.id, post_sessions[user_id]["last_preview_message_id"])
        except Exception:
            pass
    post_sessions[user_id] = {
        "movie_name": movie_name,
        "caption": None,
        "buttons": [],
        "photo_mode": True,
        "use_landscape": True if movie_details.get("backdrop_url") else False,
        "custom_languages": [],
        "custom_subtitles": [],
        "custom_resolutions": [],
        "custom_otts": [],
        "last_preview_message_id": None,
        "original_message_id": message.id,
        "custom_poster": None,
        "watermark": DEFAULT_WATERMARK,
        "lang_format": LANGUAGES_FORMAT,
        "sub_format": SUBTITLES_FORMAT,
        "ott_format": OTT_FORMAT,
        "res_format": RESOLUTIONS_FORMAT,
        "active_template": "minimalist",
        "movie_details": movie_details,
        "is_anipost": False
    }
    if USE_DEFAULT_BTN:
        post_sessions[user_id]["buttons"].append([InlineKeyboardButton("👀 ᴡᴀᴛᴄʜ ɴᴏᴡ", url=DEFAULT_BTN_LINK)])
    await update_post_preview(client, user_id, message.chat.id, force_resend=True)

async def start_anipost_session(client: Client, message: Message, user_id: int, anime_name: str):
    query = anime_name
    data = await anilist_get_media(query)
    try:
        res = json.loads(data)["data"].get("Media", None)
    except:
        res = None
    if not res:
        return await message.reply_text("⚠️ 𝖮𝗈𝗉𝗌! 𝖨 𝖼𝗈𝗎𝗅𝖽𝗇’𝗍 𝖿𝖾𝗍𝖼𝗁 𝗍𝗁𝖾 𝖽𝖾𝗍𝖺𝗂𝗅𝗌.")
    title_eng = res["title"].get("english") or "N/A"
    title_romaji = res["title"].get("romaji") or "N/A"
    final_title = f"{title_eng} | {title_romaji}"
    studio_edges = (res.get("studios") or {}).get("edges", []) or []
    main_studio = next((e.get("node", {}).get("name") for e in studio_edges if e.get("isMain")), "N/A")
    score = res.get("averageScore")
    rating10 = f"{(score/10):.1f}" if isinstance(score, (int, float)) else "N/A"
    anime_details = {
        "title": final_title,
        "english": title_eng,
        "format": res.get("format", "N/A"),
        "status": res.get("status", "N/A"),
        "season": res.get("season", "N/A"),
        "seasonYear": res.get("seasonYear", "N/A"),
        "episodes": res.get("episodes", "N/A"),
        "score": score if score is not None else "N/A",
        "rating10": rating10,
        "genres": ", ".join(res.get("genres", []) or []),
        "studio": main_studio,
        "plot": res.get("description", ""),
        "poster_portrait": res.get("coverImage", {}).get("extraLarge") or res.get("coverImage", {}).get("large"),
        "poster_landscape": (res.get("siteUrl") or "").replace("anilist.co/anime/", "img.anili.st/media/"),
        "siteUrl": res.get("siteUrl")
    }
    if user_id in post_sessions and post_sessions[user_id].get("last_preview_message_id"):
        try:
            await client.delete_messages(message.chat.id, post_sessions[user_id]["last_preview_message_id"])
        except:
            pass
    post_sessions[user_id] = {
        "movie_name": anime_name,
        "caption": None,
        "buttons": [],
        "photo_mode": True,
        "use_landscape": True,
        "custom_languages": [],
        "custom_subtitles": [],
        "custom_resolutions": [],
        "custom_otts": [],
        "last_preview_message_id": None,
        "original_message_id": message.id,
        "watermark": DEFAULT_WATERMARK,
        "lang_format": LANGUAGES_FORMAT,
        "sub_format": SUBTITLES_FORMAT,
        "ott_format": OTT_FORMAT,
        "res_format": RESOLUTIONS_FORMAT,
        "active_template": None,
        "movie_details": anime_details,
        "custom_poster": anime_details["poster_landscape"],
        "is_anipost": True
    }
    if USE_DEFAULT_BTN:
        post_sessions[user_id]["buttons"].append([InlineKeyboardButton("👀 ᴡᴀᴛᴄʜ ɴᴏᴡ", url=DEFAULT_BTN_LINK)])
    await update_post_preview(client, user_id, message.chat.id, force_resend=True)

async def build_final_post_content(session: dict, session_id: int):
    m = session.get("movie_details") or {}
    if not m:
        return None, None, None
    if not session.get("caption"):
        if session.get("is_anipost"):
            session["caption"] = (
                f"<blockquote><b>{m.get('title')}</b></blockquote>\n\n"
                f"<b>‣ ᴛʏᴘᴇ :</b> {m.get('format')}\n"
                f"<b>‣ sᴛᴀᴛᴜs :</b> {m.get('status')}\n"
                f"<b>‣ ᴇᴘɪsᴏᴅᴇs :</b> {m.get('episodes')}\n"
                f"<b>‣ ʀᴀᴛɪɴɢ :</b> {m.get('rating10')}/10\n"
                f"<b>‣ ᴀɪʀᴇᴅ :</b> {m.get('season')} {m.get('seasonYear')}\n"
                f"<b>‣ sᴛᴜᴅɪᴏ :</b> {m.get('studio')}\n"
                f"<b>‣ ɢᴇɴʀᴇs :</b> {m.get('genres')}"
            )
        else:
            session["caption"] = TEMPLATES[session["active_template"]].format(
                title=m.get("title", "N/A"),
                year=m.get("year", "N/A"),
                rating=m.get("rating", "N/A"),
                genres=", ".join(m.get("genres", []) or []),
            )
    final_caption = session["caption"]
    plot_text = m.get("plot", "N/A")
    if session.get("custom_languages"):
        final_caption += "\n" + session["lang_format"].format(langs=', '.join(session['custom_languages']))
    if session.get("custom_subtitles"):
        final_caption += "\n" + session["sub_format"].format(subs=', '.join(session['custom_subtitles']))
    if session.get("custom_resolutions"):
        final_caption += "\n" + session["res_format"].format(resolutions=' | '.join(session['custom_resolutions']))
    if session.get("custom_otts"):
        final_caption += "\n" + session["ott_format"].format(otts=', '.join(session['custom_otts']))
    if not session.get("custom_caption"):
        if session.get("is_anipost"):
            final_caption += shorten_description(plot_text, m.get("siteUrl"))
        else:
            final_caption += f"\n\n<blockquote expandable><b>Plot :</b> <em>{plot_text}</em></blockquote>"
    if session.get("watermark"):
        final_caption += f"\n\n{session['watermark']}"
    if session.get("is_anipost"):
        if session.get("use_landscape"):
            poster = session.get("custom_poster") or m.get("poster_landscape")
        else:
            poster = session.get("custom_poster") or m.get("poster_portrait")
    else:
        poster = session.get("custom_poster") or (m.get("backdrop_url") if session.get("use_landscape") else m.get("poster_url"))
    kb = build_keyboard(session, session_id)
    return final_caption, kb, poster

async def update_post_preview(client: Client, session_id: int, chat_id: int, force_resend: bool = False):
    session = post_sessions.get(session_id)
    if not session:
        return
    is_new = not session.get("last_preview_message_id")
    if is_new or force_resend:
        if not is_new:
            try:
                await client.delete_messages(chat_id, session["last_preview_message_id"])
            except Exception:
                pass
        status_msg = await client.send_message(
            chat_id, "<i>𝖥𝖾𝗍𝖼𝗁𝗂𝗇𝗀 𝖽𝖾𝗍𝖺𝗂𝗅𝗌...</i>",
            reply_to_message_id=session["original_message_id"]
        )
        session["last_preview_message_id"] = status_msg.id
    final_caption, keyboard, poster_to_use = await build_final_post_content(session, session_id)
    if not final_caption:
        return await client.edit_message_text(chat_id, session["last_preview_message_id"], "⚠️ 𝖮𝗈𝗉𝗌! 𝖨 𝖼𝗈𝗎𝗅𝖽𝗇’𝗍 𝖿𝖾𝗍𝖼𝗁 𝗍𝗁𝖾 𝖽𝖾𝗍𝖺𝗂𝗅𝗌.")
    try:
        if session["photo_mode"] and poster_to_use:
            if force_resend:
                await client.delete_messages(chat_id, session["last_preview_message_id"])
                sent = await client.send_photo(chat_id, photo=poster_to_use, caption=final_caption, reply_markup=keyboard, reply_to_message_id=session["original_message_id"])
                session["last_preview_message_id"] = sent.id
            else:
                await client.edit_message_caption(chat_id, session["last_preview_message_id"], caption=final_caption, reply_markup=keyboard)
        else:
            text_content = f"<a href='{poster_to_use}'>&#8205;</a>{final_caption}" if poster_to_use else final_caption
            await client.edit_message_text(chat_id, session["last_preview_message_id"], text_content, reply_markup=keyboard, disable_web_page_preview=False, invert_media=ABOVE_PREVIEW)
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f"Error updating preview: {e}", exc_info=True)

@Client.on_message(filters.command("post") & filters.user(ADMINS), group=-4)
async def post_command(client: Client, message: Message):
    if len(message.command) == 1:
        return await message.reply_text("⚠️ 𝖯𝗅𝖾𝖺𝗌𝖾 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖺 𝗇𝖺𝗆𝖾.\n\n<b>𝖤𝗑𝖺𝗆𝗉𝗅𝖾:</b> `/post Inception`")
    movie_name = " ".join(message.command[1:])
    user_id = message.from_user.id
    await start_post_session(client, message, user_id, movie_name)

@Client.on_message(filters.command("anipost") & filters.user(ADMINS), group=-4)
async def anipost_command(client: Client, message: Message):
    if len(message.command) == 1:
        return await message.reply_text("⚠️ 𝖯𝗅𝖾𝖺𝗌𝖾 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖺 𝗇𝖺𝗆𝖾.\n\n<b>𝖤𝗑𝖺𝗆𝗉𝗅𝖾:</b> `/anipost One Piece`")
    search = message.text.split(None, 1)
    anime_name = search[1]
    user_id = message.from_user.id
    await start_anipost_session(client, message, user_id, anime_name)

@Client.on_callback_query(filters.regex(r"^post:"), group=-4)
async def post_callbacks(client: Client, query: CallbackQuery):
    d = query.data.split(":")
    action = d[1]; sid = int(d[2])
    extra = d[3:] if len(d) > 3 else []
    if query.from_user.id != sid:
        return await query.answer("𝖳𝗁𝗂𝗌 𝗂𝗌 𝗇𝗈𝗍 𝖿𝗈𝗋 𝗒𝗈𝗎!", show_alert=True)
    s = post_sessions.get(sid)
    if not s:
        await query.answer("𝖲𝖾𝗌𝗌𝗂𝗈𝗇 𝖾𝗑𝗉𝗂𝗋𝖾𝖽 𝗈𝗋 𝖼𝖺𝗇𝖼𝖾𝗅𝗅𝖾𝖽.", show_alert=True)
        return await query.message.delete()
    force = False
    if action == "back":
        await query.answer()
    elif action in ["languages", "subtitles", "resolutions", "templates", "buttons_menu", "remove_buttons_menu", "otts"]:
        await query.answer()
        if action == "languages":
            await show_selection_menu(query, sid, "languages")
        elif action == "subtitles":
            await show_selection_menu(query, sid, "subtitles")
        elif action == "resolutions":
            await show_selection_menu(query, sid, "resolutions")
        elif action == "otts":
            await show_selection_menu(query, sid, "otts")
        elif action == "templates":
            await handle_templates_menu(query, s)
        elif action == "buttons_menu":
            await handle_buttons_menu(query, sid)
        elif action == "remove_buttons_menu":
            await handle_remove_buttons_menu(query, s)
        return
    elif action in ["select_lang", "select_sub", "select_res", "select_ott"]:
        await query.answer()
        item = extra[0]
        if action == "select_lang":
            lst = s["custom_languages"]
        elif action == "select_sub":
            lst = s["custom_subtitles"]
        elif action == "select_res":
            lst = s["custom_resolutions"]
        else:
            lst = s["custom_otts"]
        if item in lst:
            lst.remove(item)
        else:
            lst.append(item)
        which = "languages" if action == "select_lang" else ("subtitles" if action == "select_sub" else ("resolutions" if action == "select_res" else "otts"))
        await show_selection_menu(query, sid, which)
        return
    else:
        if action == "edit_buttons":
            await handle_edit_buttons(client, query, s)
        elif action == "add_get_files":
            await handle_add_get_files(s)
            await query.answer("✅ '𝖦𝖾𝗍 𝖥𝗂𝗅𝖾𝗌' 𝖻𝗎𝗍𝗍𝗈𝗇 𝖺𝖽𝖽𝖾𝖽!")
        elif action == "edit_caption":
            await handle_edit_caption(client, query, s)
        elif action == "set_poster":
            force = await handle_set_poster(client, query, s)
        elif action == "remove_button":
            await handle_remove_button(s, extra)
            await handle_remove_buttons_menu(query, s); return
        elif action == "select_template":
            await handle_select_template(s, extra[0])
            await update_post_preview(client, sid, query.message.chat.id)
            await handle_templates_menu(query, s); return
        elif action == "toggle_preview":
            force = await handle_toggle_preview(query, s)
        elif action == "toggle_poster":
            force = await handle_toggle_poster(s)
        elif action == "set_watermark":
            await handle_set_watermark(client, query, s)
        elif action == "format_lang":
            await handle_format_lang(client, query, s)
        elif action == "format_sub":
            await handle_format_sub(client, query, s)
        elif action == "format_res":
            await handle_format_res(client, query, s)
        elif action == "format_ott":
            await handle_format_ott(client, query, s)
        elif action == "finalize":
            return await finalize_and_post(client, query, sid)
        elif action == "cancel":
            return await handle_cancel(client, query, sid)
    await update_post_preview(client, sid, query.message.chat.id, force_resend=force)
