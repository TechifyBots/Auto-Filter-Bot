import os
import re
import asyncio
import logging
import time
import platform
import shutil
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatJoinRequest
from pyrogram.filters import create
from pyrogram.enums import ParseMode
from utils import get_poster, temp, get_settings, last_online
from database.ia_filterdb import get_search_results, techifybots_get_movies, techifybots_get_series, Media, Media2, unpack_new_file_id
from database.users_chats_db import db
from info import LOG_CHANNEL, OWNER, MELCOW_PHOTO, DELETE_CHANNELS, GROUP_LINK, DELETE_TIME, ADMINS, AUTH_REQ_CHANNELS
from Script import script
import aiohttp, json
from calendar import month_name

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

media_filter = filters.document | filters.video | filters.audio
start_time=time.time()

anime_query = """
query ($search: String) {
  Page(page: 1, perPage: 10) {
    media(search: $search, type: ANIME) {
      id
      title {
        romaji
        english
      }
      format
      siteUrl
    }
  }
}
"""

anime_detail_query = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    type
    format
    status(version: 2)
    season
    seasonYear
    description(asHtml: true)
    startDate { year month day }
    endDate { year month day }
    genres
    averageScore
    episodes
    studios { edges { isMain node { name } } }
    coverImage { large }
    trailer { id site }
    siteUrl
  }
}
"""

async def fetch_json(query, variables):
    async with aiohttp.ClientSession() as session:
        r = await session.post("https://graphql.anilist.co", json={"query": query, "variables": variables})
        data = await r.read()
        return json.loads(data)

def shorten_description(desc, url="https://anilist.co"):
    if not desc:
        return f"<em>No description available.</em>"
    desc = re.sub(r"<[^>]*>", "", desc)
    if len(desc) > 700:
        return f"\n<blockquote expandable><strong>‣ ᴏᴠᴇʀᴠɪᴇᴡ :</strong> <em>{desc[:500]}....<strong><a href=\"{url}\">𝖬𝗈𝗋𝖾 𝖨𝗇𝖿𝗈</a></strong></em></blockquote>"
    return f"\n<blockquote expandable><strong>‣ ᴏᴠᴇʀᴠɪᴇᴡ :</strong> <em>{desc}</em></blockquote>"

def build_keyboard(site_url, trailer_url=None):
    buttons, row1 = [], []
    if trailer_url:
        row1.append(InlineKeyboardButton("🎬 𝖳𝗋𝖺𝗂𝗅𝖾𝗋", url=trailer_url))
    if site_url:
        row1.append(InlineKeyboardButton("🔖 𝖬𝗈𝗋𝖾 𝖨𝗇𝖿𝗈", url=site_url))
    if row1:
        buttons.append(row1)
    buttons.append([InlineKeyboardButton("❌ 𝖢𝗅𝗈𝗌𝖾", callback_data="close")])
    return InlineKeyboardMarkup(buttons)

def is_auth_req_channel(_, __, update):
    return update.chat.id in AUTH_REQ_CHANNELS

@Client.on_chat_join_request(create(is_auth_req_channel))
async def join_reqs(client, message: ChatJoinRequest):
    await db.add_join_req(message.from_user.id, message.chat.id)

@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    await db.del_join_req()    
    await message.reply("<b>⚙ sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ᴅᴇʟᴇᴛᴇᴅ</b>")

@Client.on_message(filters.private & filters.command("anime"))
async def anime_search(client, message):
    msgs = [message.id]
    if len(message.command) == 1:
        warn = await message.reply_text("⚠️ 𝖯𝗅𝖾𝖺𝗌𝖾 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖺𝗇 𝖺𝗇𝗂𝗆𝖾 𝗇𝖺𝗆𝖾 𝖺𝖿𝗍𝖾𝗋 𝗍𝗁𝖾 𝖼𝗈𝗆𝗆𝖺𝗇𝖽.\n\n𝖤𝗑𝖺𝗆𝗉𝗅𝖾: `/anime One Piece`", quote=True)
        msgs.append(warn.id)
    else:
        query = message.text.split(None, 1)[1]
        searching = await message.reply_text("𝘚𝘦𝘢𝘳𝘤𝘩𝘪𝘯𝘨...", quote=True)
        data = await fetch_json(anime_query, {"search": query})
        media_list = data.get("data", {}).get("Page", {}).get("media", [])
        if not media_list:
            await searching.edit_text("❌ 𝖭𝗈 𝗋𝖾𝗌𝗎𝗅𝗍𝗌 𝖿𝗈𝗋 𝗒𝗈𝗎𝗋 𝗊𝗎𝖾𝗋𝗒.")
            msgs.append(searching.id)
        else:
            await searching.delete()
            buttons = [[InlineKeyboardButton(text=f"{anime['title'].get('english') or anime['title'].get('romaji')} ({anime.get('format','')})", callback_data=f"anime#{anime['id']}")] for anime in media_list[:10]]
            result_msg = await message.reply_text("📺 𝖧𝖾𝗋𝖾’𝗌 𝗌𝗈𝗆𝖾 𝗋𝖾𝗅𝖺𝗍𝖾𝖽 𝗋𝖾𝗌𝗎𝗅𝗍𝗌:", reply_markup=InlineKeyboardMarkup(buttons))
            msgs.append(result_msg.id)
    await asyncio.sleep(DELETE_TIME)
    await client.delete_messages(message.chat.id, msgs)

@Client.on_callback_query(filters.regex("^anime#"))
async def anime_callback(client, query: CallbackQuery):
    await query.answer("Fetching details...")
    _, anime_id = query.data.split("#", 1)
    if not anime_id.isdigit():
        title_text = query.message.text or query.message.caption
        if title_text:
            title_text = title_text.replace("📺 𝖧𝖾𝗋𝖾’𝗌 𝗌𝗈𝗆𝖾 𝗋𝖾𝗅𝖺𝗍𝖾𝖽 𝗋𝖾𝗌𝗎𝗅𝗍𝗌:", "").strip()
        data = await fetch_json(anime_query, {"search": title_text})
        media_list = data.get("data", {}).get("Page", {}).get("media", [])
        if not media_list:
            return await query.answer("❌ 𝖭𝗈 𝗋𝖾𝗌𝗎𝗅𝗍𝗌 𝖿𝗈𝗋 𝗒𝗈𝗎𝗋 𝗊𝗎𝖾𝗋𝗒.", show_alert=True)
        anime_id = media_list[0]["id"]
    res = await fetch_json(anime_detail_query, {"id": int(anime_id)})
    res = res.get("data", {}).get("Media")
    if not res:
        title_text = query.message.text or query.message.caption
        data = await fetch_json(anime_query, {"search": title_text})
        media_list = data.get("data", {}).get("Page", {}).get("media", [])
        if media_list:
            anime_id = media_list[0]["id"]
            res = await fetch_json(anime_detail_query, {"id": int(anime_id)})
            res = res.get("data", {}).get("Media")
    if not res:
        return await query.message.edit_text("❌ Failed to fetch Anime details.")
    title_english = res["title"].get("english") or res["title"].get("romaji") or "N/A"
    title_romaji = res["title"].get("romaji") or "N/A"
    caption = f"<blockquote><b>{title_english} | {title_romaji}</b></blockquote>\n\n"
    caption += f"<b>‣ ᴛʏᴘᴇ :</b> {res.get('format', 'N/A')}\n"
    caption += f"<b>‣ sᴛᴀᴛᴜs :</b> {res.get('status', 'N/A')}\n"
    caption += f"<b>‣ ᴇᴘɪsᴏᴅᴇs :</b> {res.get('episodes', 'N/A')}\n"
    caption += f"<b>‣ sᴄᴏʀᴇ :</b> {res.get('averageScore', 'N/A')}%\n"
    caption += f"<b>‣ ᴀɪʀᴇᴅ :</b> {res.get('season', 'N/A')} {res.get('seasonYear', '')}\n"
    try:
        sd = res.get("startDate", {})
        start = f"{month_name[sd['month']]} {sd['day']}, {sd['year']}" if sd.get('year') else "-"
    except:
        start = "-"
    caption += f"<b>‣ sᴛᴀʀᴛ :</b> {start}\n"
    try:
        ed = res.get("endDate", {})
        end = f"{month_name[ed['month']]} {ed['day']}, {ed['year']}" if ed.get('year') else "-"
    except:
        end = "-"
    caption += f"<b>‣ ᴇɴᴅ :</b> {end}\n"
    studio_edges = res.get("studios", {}).get("edges", [])
    main_studio = next((e["node"]["name"] for e in studio_edges if e.get("isMain")), "N/A")
    caption += f"<b>‣ sᴛᴜᴅɪᴏ :</b> {main_studio}\n"
    caption += f"<b>‣ ɢᴇɴʀᴇs :</b> {', '.join(res.get('genres', []))}\n"
    caption += shorten_description(res.get("description", ""), res.get("siteUrl"))
    image_url = res["siteUrl"].replace("anilist.co/anime/", "img.anili.st/media/")
    trailer_url = None
    if res.get("trailer") and res["trailer"].get("site") == "youtube":
        trailer_url = f"https://youtu.be/{res['trailer']['id']}"
    buttons = build_keyboard(res["siteUrl"], trailer_url)
    try:
        await query.message.delete()
        msg = await query.message.reply_photo(photo=image_url, caption=caption, reply_markup=buttons)
    except Exception as e:
        print(f"Error sending photo: {e}")
        msg = await query.message.reply_text(caption, reply_markup=buttons)
    await asyncio.sleep(DELETE_TIME)
    await client.delete_messages(msg.chat.id, [msg.id])

@Client.on_message(filters.command("search"))
async def search_cmd(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) == 1 or not args[1].strip():
        reply = await message.reply_text("⚠️ 𝖯𝗅𝖾𝖺𝗌𝖾 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖺 𝗌𝖾𝖺𝗋𝖼𝗁 𝗊𝗎𝖾𝗋𝗒\n\n𝖤𝗑𝖺𝗆𝗉𝗅𝖾: `/search Naruto`")
    else:
        search = args[1].strip()
        _, _, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)
        if total_results == 0:
            reply = await message.reply_text(f"<b>{message.from_user.mention},\n\nɴᴏ ʀᴇsᴜʟᴛ ꜰᴏᴜɴᴅ ʏᴏᴜ ᴄᴀɴ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴏᴡɴᴇʀ.\n\n<blockquote>📝 ʀᴇǫᴜᴇsᴛ ꜰᴏʀᴍᴀᴛ:\n\n/request ꜰɪʟᴇs ɴᴀᴍᴇ | ʏᴇᴀʀ</blockquote></b>")
        else:
            reply = await message.reply_text(f"<b>{message.from_user.mention},\n\nꜰᴏᴜɴᴅ {total_results} ꜰɪʟᴇ(s) ꜰᴏʀ {search}</b>\n\n<i>‼️ ꜰɪʟᴇs ᴀʀᴇ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴛʜᴇ ᴍᴀɪɴ ɢʀᴏᴜᴘ 👇</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ", url=GROUP_LINK)]]))
    await asyncio.sleep(DELETE_TIME)
    await client.delete_messages(message.chat.id, [message.id, reply.id])

@Client.on_message(filters.command("id"))
async def id_cmd(client, message):
    chat_type = message.chat.type
    reply_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if chat_type == enums.ChatType.PRIVATE:
        text = f"<b>‣ ɪᴅ :</b> <code>{message.from_user.id}</code>"
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        text = (
            f"<b>‣ ɪᴅ :</b> <code>{message.from_user.id}</code>\n"
            f"<b>‣ ɢʀᴏᴜᴘ ɪᴅ :</b> <code>{message.chat.id}</code>"
        )
        if reply_id:
            text += f"\n<b>‣ ʀᴇᴘʟɪᴇᴅ ᴜꜱᴇʀ ɪᴅ :</b> <code>{reply_id}</code>"
    elif chat_type == enums.ChatType.CHANNEL:
        text = f"<b>‣ ᴄʜᴀɴɴᴇʟ ɪᴅ :</b> <code>{message.chat.id}</code>"
    else:
        text = "⚠️ 𝖴𝗇𝗌𝗎𝗉𝗉𝗈𝗋𝗍𝖾𝖽 𝗎𝗌𝖾𝗋 𝗍𝗒𝗉𝖾 𝗈𝗋 𝖺𝗇𝗈𝗇𝗒𝗆𝗈𝗎𝗌 𝖺𝖽𝗆𝗂𝗇."
    msg = await message.reply_text(text, quote=True)
    await asyncio.sleep(DELETE_TIME)
    await client.delete_messages(message.chat.id, [message.id, msg.id])

@Client.on_message(filters.command("info"))
async def info_handler(client, message):
    replied=message.reply_to_message
    buttons=[[InlineKeyboardButton("✗ ᴄʟᴏsᴇ ✗",callback_data="close")]]
    sent_msg=None
    user=None
    if replied:
        media=next((getattr(replied,attr,None)for attr in["photo","video","sticker","animation","document","audio"]if getattr(replied,attr,None)),None)
        if media:
            sent_msg=await message.reply_text(f"**📦 𝖬𝖾𝖽𝗂𝖺 𝖨𝗇𝖿𝗈:**\n\n🆔 𝖥𝗂𝗅𝖾 𝖨𝖣:\n`{media.file_id}`\n\n🔒 𝖴𝗇𝗂𝗊𝗎𝖾 𝖨𝖣:\n`{media.file_unique_id}`")
        elif replied.from_user:
            user=replied.from_user
        else:
            sent_msg=await message.reply("⚠️ 𝖯𝗅𝖾𝖺𝗌𝖾 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝗆𝖾𝖽𝗂𝖺 𝗈𝗋 𝖺 𝗎𝗌𝖾𝗋.")
    elif len(message.command)>1:
        try:
            user_id=int(message.command[1])
            user=await client.get_users(user_id)
        except Exception as e:
            sent_msg=await message.reply(f"❌ 𝖥𝖺𝗂𝗅𝖾𝖽 𝗍𝗈 𝗀𝖾𝗍 𝗎𝗌𝖾𝗋 𝗂𝗇𝖿𝗈: `{e}`")
    else:
        user=message.from_user
    if not sent_msg and user:
        try:
            status_text=last_online(user)
            caption=script.INFO_TXT.format(id=user.id,dc=getattr(user,"dc_id","N/A"),n=user.first_name or"N/A",u=user.username or"N/A",status=status_text)
            if getattr(user,"photo",None):
                dp=await client.download_media(user.photo.big_file_id)
                sent_msg=await message.reply_photo(photo=dp,caption=caption,reply_markup=InlineKeyboardMarkup(buttons))
                os.remove(dp)
            else:
                sent_msg=await message.reply_text(text=caption,reply_markup=InlineKeyboardMarkup(buttons))
        except Exception as e:
            sent_msg=await message.reply(f"❌ 𝖥𝖺𝗂𝗅𝖾𝖽 𝗍𝗈 𝗀𝖾𝗍 𝗎𝗌𝖾𝗋 𝗂𝗇𝖿𝗈: `{e}`")
    if sent_msg:
        await asyncio.sleep(DELETE_TIME)
        await client.delete_messages(message.chat.id,[message.id,sent_msg.id])

@Client.on_message(filters.private & filters.command("imdb"))
async def imdb_search(client, message):
    msgs = [message.id]
    if " " not in message.text:
        warn = await message.reply_text("⚠️ 𝖯𝗅𝖾𝖺𝗌𝖾 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖺 𝗆𝗈𝗏𝗂𝖾 𝗈𝗋 𝗌𝖾𝗋𝗂𝖾𝗌 𝗇𝖺𝗆𝖾 𝖺𝖿𝗍𝖾𝗋 𝗍𝗁𝖾 𝖼𝗈𝗆𝗆𝖺𝗇𝖽.\n\n𝖤𝗑𝖺𝗆𝗉𝗅𝖾: `/imdb Inception`", quote=True)
        msgs.append(warn.id)
    else:
        searching = await message.reply_text("𝘚𝘦𝘢𝘳𝘤𝘩𝘪𝘯𝘨 𝘰𝘯 𝘐𝘔𝘋𝘣...", quote=True)
        msgs.append(searching.id)
        _, title = message.text.split(None, 1)
        movies = await get_poster(title, bulk=True)
        if not movies:
            nores = await message.reply_text("❌ 𝖭𝗈 𝗋𝖾𝗌𝗎𝗅𝗍𝗌 𝖿𝗈𝗎𝗇𝖽 𝗈𝗇 𝖨𝖬𝖣𝖻.", quote=True)
            msgs.append(nores.id)
        else:
            await searching.delete()
            btn = [[InlineKeyboardButton(text=f"{movie.get('title')} - {movie.get('year')}", callback_data=f"imdb#{movie.movieID}")] for movie in movies]
            result = await message.reply_text("🎬 𝖧𝖾𝗋𝖾’𝗌 𝗐𝗁𝖺𝗍 𝗂 𝖿𝗈𝗎𝗇𝖽 𝗈𝗇 𝖨𝖬𝖣𝖻:", reply_markup=InlineKeyboardMarkup(btn))
            msgs.append(result.id)
    await asyncio.sleep(DELETE_TIME)
    await client.delete_messages(message.chat.id, msgs)

@Client.on_callback_query(filters.regex("^imdb"))
async def imdb_callback(client: Client, query: CallbackQuery):
    _, movie = query.data.split("#")
    imdb = await get_poster(query=movie, id=True)
    if not imdb:
        return await query.message.edit_text("❌ 𝖭𝗈 𝗋𝖾𝗌𝗎𝗅𝗍𝗌 𝖿𝗈𝗎𝗇𝖽.")
    btn = [[InlineKeyboardButton(text=f"{imdb.get('title')}", url=imdb["url"])]]
    caption = f"<blockquote><b><a href='{imdb['url']}'>{imdb['title']}</a></b></blockquote>\n\n<b>📆 ʏᴇᴀʀ:</b> {imdb['year']}\n<b>🌟 ʀᴀᴛɪɴɢ:</b> {imdb['rating']}/10\n<b>🎭 ɢᴇɴʀᴇꜱ:</b> {imdb.get('genres', 'N/A')}\n\n<blockquote><b>📝 ᴘʟᴏᴛ:</b> {imdb['plot']}</blockquote>"
    await query.message.delete()
    try:
        msg = await query.message.reply_photo(photo=imdb["poster"], caption=caption, reply_markup=InlineKeyboardMarkup(btn)) if imdb.get("poster") else await query.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(btn))
    except Exception:
        msg = await query.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(btn))
    await query.answer()
    await asyncio.sleep(DELETE_TIME)
    await client.delete_messages(msg.chat.id, [msg.id])
        
@Client.on_message(filters.private & filters.command("movies"))
async def movies(client, message):
    try:
        movies = await techifybots_get_movies()
        if not movies:
            sent = await message.reply("❌ 𝖭𝗈 𝖱𝖾𝖼𝖾𝗇𝗍 𝖬𝗈𝗏𝗂𝖾𝗌 𝖥𝗈𝗎𝗇𝖽", parse_mode=ParseMode.HTML)
        else:
            msg = "<b>🎬 𝖫𝖺𝗍𝖾𝗌𝗍 𝖴𝗉𝗅𝗈𝖺𝖽𝖾𝖽 𝖬𝗈𝗏𝗂𝖾𝗌 ✅</b>\n\n"
            msg += "\n".join(f"<b>{i+1}. {m}</b>" for i, m in enumerate(movies))
            sent = await message.reply(msg[:4096], parse_mode=ParseMode.HTML)
    except Exception as e:
        sent = await message.reply(f"❌ 𝖥𝖺𝗂𝗅𝖾𝖽: <code>{e}</code>", parse_mode=ParseMode.HTML)
    await asyncio.sleep(DELETE_TIME)
    await client.delete_messages(message.chat.id, [message.id, sent.id])

@Client.on_message(filters.private & filters.command("series"))
async def series(client, message):
    try:
        series_data = await techifybots_get_series()
        if not series_data:
            sent = await message.reply("❌ 𝖭𝗈 𝖱𝖾𝖼𝖾𝗇𝗍 𝖲𝖾𝗋𝗂𝖾𝗌 𝖥𝗈𝗎𝗇𝖽", parse_mode=ParseMode.HTML)
        else:
            msg = "<b>📺 𝖫𝖺𝗍𝖾𝗌𝗍 𝖴𝗉𝗅𝗈𝖺𝖽𝖾𝖽 𝖳𝖵 𝖲𝖾𝗋𝗂𝖾𝗌 ✅</b>\n\n"
            for i, (title, seasons) in enumerate(series_data.items(), 1):
                season_list = ", ".join(f"{s}" for s in seasons)
                msg += f"<b>{i}. {title} - Season {season_list}</b>\n"
            sent = await message.reply(msg[:4096], parse_mode=ParseMode.HTML)
    except Exception as e:
        sent = await message.reply(f"❌ 𝖥𝖺𝗂𝗅𝖾𝖽: <code>{e}</code>", parse_mode=ParseMode.HTML)
    await asyncio.sleep(DELETE_TIME)
    await client.delete_messages(message.chat.id, [message.id, sent.id])

@Client.on_message(filters.private & filters.command("system"))
async def send_system_info(client,message):
    import time,shutil,platform
    start=time.time()
    ping=await message.reply_text("🏓 𝖯𝗂𝗇𝗀𝗂𝗇𝗀...")
    latency=f"{(time.time()-start)*1000:.2f} ms"
    def fmt(sec):
        sec=int(sec);d,r=divmod(sec,86400);h,r=divmod(r,3600);m,s=divmod(r,60)
        return f"{d}ᴅ : {h:02d}ʜ : {m:02d}ᴍ : {s:02d}s" if d else f"{h:02d}ʜ : {m:02d}ᴍ : {s:02d}s"
    def size(kb):
        b=int(kb)*1024
        for u in['B','KB','MB','GB','TB']:
            if b<1024:return f"{b:.2f} {u}"
            b/=1024
        return f"{b:.2f} PB"
    try:
        with open('/proc/uptime')as f:sys_uptime=fmt(float(f.readline().split()[0]))
    except:sys_uptime="𝖴𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾"
    try:
        with open('/proc/meminfo')as f:mem=f.readlines();total=size(mem[0].split()[1]);avail=size(mem[2].split()[1]);used=size(int(mem[0].split()[1])-int(mem[2].split()[1]))
    except:total,used="𝖴𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾","𝖴𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾"
    try:
        td,ud,_=shutil.disk_usage("/");td=size(td//1024);ud=size(ud//1024)
    except:td,ud="𝖴𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾","𝖴𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾"
    info=(f"💻 <b>𝖲𝗒𝗌𝗍𝖾𝗆 𝖨𝗇𝖿𝗈𝗋𝗆𝖺𝗍𝗂𝗈𝗇</b>\n\n"
          f"🖥️ <b>𝖮𝖲 :</b> {platform.system()}\n"
          f"⏰ <b>𝖡𝗈𝗍 𝖴𝗉𝗍𝗂𝗆𝖾 :</b> {fmt(time.time()-start_time)}\n"
          f"🔄 <b>𝖲𝗒𝗌𝗍𝖾𝗆 𝖴𝗉𝗍𝗂𝗆𝖾 :</b> {sys_uptime}\n"
          f"💾 <b>𝖱𝖠𝖬 :</b> {used} / {total}\n"
          f"📁 <b>𝖣𝗂𝗌𝗄 :</b> {ud} / {td}\n"
          f"📶 <b>𝖫𝖺𝗍𝖾𝗇𝖼𝗒 :</b> {latency}")
    await ping.edit_text(info)
    await asyncio.sleep(DELETE_TIME)
    await client.delete_messages(message.chat.id,[message.id,ping.id])

@Client.on_message(filters.new_chat_members & filters.group)
async def save_group(bot, message):
    tb = [u.id for u in message.new_chat_members]
    buttons = [[InlineKeyboardButton('👨‍💻 𝖠𝖽𝗆𝗂𝗇', user_id=int(OWNER))]]
    if temp.ME in tb:
        if not await db.get_chat(message.chat.id):
            total=await bot.get_chat_members_count(message.chat.id)
            techifybots = message.from_user.mention if message.from_user else "Anonymous"
            await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, techifybots))       
            await db.add_chat(message.chat.id, message.chat.title)
        if message.chat.id in temp.BANNED_CHATS:
            k = await message.reply(text='<b>ᴄʜᴀᴛ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ 🐞\n\nᴍʏ ᴀᴅᴍɪɴꜱ ʜᴀꜱ ʀᴇꜱᴛʀɪᴄᴛᴇᴅ ᴍᴇ ꜰʀᴏᴍ ᴡᴏʀᴋɪɴɢ ʜᴇʀᴇ ! ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴋɴᴏᴡ ᴍᴏʀᴇ ᴀʙᴏᴜᴛ ɪᴛ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.</b>', reply_markup=InlineKeyboardMarkup(buttons))
            try:
                await k.pin()
            except:
                pass
            await bot.leave_chat(message.chat.id)
            return
        await message.reply_text(text=f"𝖳𝗁𝖺𝗇𝗄𝗒𝗈𝗎 𝖥𝗈𝗋 𝖠𝖽𝖽𝗂𝗇𝗀 𝖬𝖾 𝖨𝗇 {message.chat.title} ❣️\n\n𝖨𝖿 𝗒𝗈𝗎 𝗁𝖺𝗏𝖾 𝖺𝗇𝗒 𝗊𝗎𝖾𝗌𝗍𝗂𝗈𝗇𝗌 𝗈𝗋 𝖽𝗈𝗎𝖻𝗍𝗌 𝖺𝖻𝗈𝗎𝗍 𝗎𝗌𝗂𝗇𝗀 𝗆𝖾 𝖼𝗈𝗇𝗍𝖺𝖼𝗍 𝖠𝖽𝗆𝗂𝗇.", reply_markup=InlineKeyboardMarkup(buttons))
        try:
            await db.connect_group(message.chat.id, message.from_user.id)
        except Exception as e:
            logging.error(f"DB error connecting group: {e}")
    else:
        settings = await get_settings(message.chat.id)

        if settings.get("welcome"):
            for u in message.new_chat_members:
                if temp.MELCOW.get('welcome'):
                    try:
                        await temp.MELCOW['welcome'].delete()
                    except:
                        pass
                try:
                    temp.MELCOW['welcome'] = await message.reply_photo(
                        photo=MELCOW_PHOTO,
                        caption=script.MELCOW_ENG.format(u.mention, message.chat.title),
                        parse_mode=enums.ParseMode.HTML)
                except Exception as e:
                    print(f"Welcome photo send failed: {e}")
        if settings.get("auto_delete"):
            await asyncio.sleep(600)
            try:
                if temp.MELCOW.get('welcome'):
                    await temp.MELCOW['welcome'].delete()
                    temp.MELCOW['welcome'] = None 
            except:
                pass

@Client.on_message(filters.chat(DELETE_CHANNELS) & media_filter)
async def deletemultiplemedia(bot, message):
    for file_type in ("document", "video", "audio"):
        media = getattr(message, file_type, None)
        if media is not None:
            break
    else:
        return
    file_id, file_ref = unpack_new_file_id(media.file_id)
    if await Media.count_documents({'file_id': file_id}):
        result = await Media.collection.delete_one({
            '_id': file_id,
        })
    else:
        result = await Media2.collection.delete_one({
            '_id': file_id,
        })
    if result.deleted_count:
        logger.info('File is successfully deleted from database.')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            logger.info('File is successfully deleted from database.')
        else:
            result = await Media2.collection.delete_many({
                'file_name': file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
                })
            if result.deleted_count:
                logger.info('File is successfully deleted from database.')
            else:
                result = await Media.collection.delete_many({
                    'file_name': media.file_name,
                    'file_size': media.file_size,
                    'mime_type': media.mime_type
                })
                if result.deleted_count:
                    logger.info('File is successfully deleted from database.')
                else:
                    result = await Media2.collection.delete_many({
                        'file_name': media.file_name,
                        'file_size': media.file_size,
                        'mime_type': media.mime_type
                    })
                    if result.deleted_count:
                        logger.info('File is successfully deleted from database.')
                    else:
                        logger.info('File not found in database.')
