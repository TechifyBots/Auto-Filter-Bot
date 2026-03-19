import asyncio
import datetime
import logging
import os
import time
import psutil
from pyrogram import Client, filters, StopPropagation, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from pyrogram.errors import PeerIdInvalid, ChatAdminRequired, FloodWait
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
from info import ADMINS, MULTIPLE_DB, OWNER
from database.users_chats_db import db
from database.ia_filterdb import Media, Media2, db as db_stats, db2 as db2_stats, client, client2
from utils import get_size, temp, get_settings, get_readable_time, users_broadcast, groups_broadcast, clear_junk, junk_group
from Script import script
from bot import botStartTime
from utils import temp

lock = asyncio.Lock()

async def banned_users(_, client, message: Message):
    return (
        message.from_user is not None or not message.sender_chat
    ) and message.from_user.id in temp.BANNED_USERS

banned_user = filters.create(banned_users)

async def disabled_chat(_, client, message: Message):
    return message.chat.id in temp.BANNED_CHATS
disabled_group=filters.create(disabled_chat)

@Client.on_message(filters.private & banned_user & filters.incoming, group=-1)
async def ban_reply(bot, message):
    ban = await db.get_ban_status(message.from_user.id)
    await message.reply(f'Sorry Dude, You are Banned to use Me. \nBan Reason : {ban["ban_reason"]}')
    raise StopPropagation

@Client.on_message(filters.group & disabled_group & filters.incoming, group=-1)
async def grp_bd(bot, message):
    tb = await db.get_chat(message.chat.id)
    k = await message.reply(
        text=f"<b>ᴄʜᴀᴛ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ 🐞\n\nᴍʏ ᴀᴅᴍɪɴꜱ ʜᴀꜱ ʀᴇꜱᴛʀɪᴄᴛᴇᴅ ᴍᴇ ꜰʀᴏᴍ ᴡᴏʀᴋɪɴɢ ʜᴇʀᴇ ! ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴋɴᴏᴡ ᴍᴏʀᴇ ᴀʙᴏᴜᴛ ɪᴛ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.\nʀᴇᴀsᴏɴ:</b> {tb['reason']}.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 ᴀᴅᴍɪɴ", user_id=int(OWNER))]]))
    try:
        await k.pin()
    except:
        pass
    await bot.leave_chat(message.chat.id)
    raise StopPropagation

@Client.on_message(filters.command('ban') & filters.user(ADMINS))
async def ban_a_user(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a user id / username')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try:
        chat = int(chat)
    except:
        pass
    try:
        k = await bot.get_users(chat)
    except PeerIdInvalid:
        return await message.reply("This is an invalid user, make sure I have met him before.")
    except IndexError:
        return await message.reply("This might be a channel, make sure its a user.")
    except Exception as e:
        return await message.reply(f'Error - {e}')
    else:
        jar = await db.get_ban_status(k.id)
        if jar['is_banned']:
            return await message.reply(f"{k.mention} is already banned\nReason: {jar['ban_reason']}")
        await db.ban_user(k.id, reason)
        temp.BANNED_USERS.append(k.id)
        await message.reply(f"Successfully banned {k.mention}")
    
@Client.on_message(filters.command('unban') & filters.user(ADMINS))
async def unban_a_user(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a user id / username')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try:
        chat = int(chat)
    except:
        pass
    try:
        k = await bot.get_users(chat)
    except PeerIdInvalid:
        return await message.reply("This is an invalid user, make sure ia have met him before.")
    except IndexError:
        return await message.reply("Thismight be a channel, make sure its a user.")
    except Exception as e:
        return await message.reply(f'Error - {e}')
    else:
        jar = await db.get_ban_status(k.id)
        if not jar['is_banned']:
            return await message.reply(f"{k.mention} is not yet banned.")
        await db.remove_ban(k.id)
        temp.BANNED_USERS.remove(k.id)
        await message.reply(f"Successfully unbanned {k.mention}")

@Client.on_message(filters.command('banned') & filters.user(ADMINS))
async def get_banned(client, message):
    banned_users, _ = await db.get_banned()
    if not banned_users:
        await message.reply_text("No banned users found.")
        return
    text = ""
    for user_id in banned_users:
        try:
            user = await client.get_users(user_id)
            text += f"{user.mention} (`{user.id}`)\n"
        except Exception:
            text += f"Undefined (`{user_id}`)\n"
    if len(text) > 4096:
        with open('banned_users.txt', 'w') as f:
            f.write(text)
        await message.reply_document('banned_users.txt')
        os.remove('banned_users.txt')
    else:
        await message.reply_text(text)

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.private)
async def broadcast_users(bot, message):
    if not message.reply_to_message:
        return await message.reply("<b>Reply to a message to broadcast.</b>", parse_mode=enums.ParseMode.HTML)
    if lock.locked():
        return await message.reply("⚠️ Another broadcast is in progress. Please wait...")
    ask = await message.reply("𝖣𝗈 𝗒𝗈𝗎 𝗐𝖺𝗇𝗍 𝗍𝗈 𝗉𝗂𝗇 𝗍𝗁𝗂𝗌 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗂𝗇 𝗎𝗌𝖾𝗋𝗌?", reply_markup=ReplyKeyboardMarkup([["Yes", "No"]], one_time_keyboard=True, resize_keyboard=True))
    try:
        techifybots_user_response = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id, timeout=60)
    except asyncio.TimeoutError:
        await ask.delete()
        return await message.reply("❌ Timed out. Broadcast cancelled.")
    await ask.delete()
    if techifybots_user_response.text not in ("Yes", "No"):
        return await message.reply("❌ Invalid input. Broadcast cancelled.")
    is_pin = techifybots_user_response.text == "Yes"
    b_msg = message.reply_to_message
    users = [user async for user in await db.get_all_users()]
    total_users = len(users)
    techifybots_status_msg = await message.reply_text("📤 <b>Broadcasting your message...</b>")
    success = blocked = deleted = failed = 0
    start_time = time.time()
    cancelled = False
    async def send(user):
        try:
            _, result = await users_broadcast(int(user["id"]), b_msg, is_pin)
            return result
        except Exception as e:
            logging.exception(f"Error sending broadcast to {user['id']}")
            return "Error"
    async with lock:
        for i in range(0, total_users, 100):
            if temp.B_USERS_CANCEL:
                temp.B_USERS_CANCEL = False
                cancelled = True
                break
            batch = users[i:i + 100]
            results = await asyncio.gather(*[send(user) for user in batch])
            for res in results:
                if res == "Success":
                    success += 1
                elif res == "Blocked":
                    blocked += 1
                elif res == "Deleted":
                    deleted += 1
                elif res == "Error":
                    failed += 1
            done = i + len(batch)
            elapsed = get_readable_time(time.time() - start_time)
            await techifybots_status_msg.edit(
                f"📣 <b>Broadcast Progress....:</b>\n\n"
                f"👥 Total: <code>{total_users}</code>\n"
                f"✅ Done: <code>{done}</code>\n"
                f"📬 Success: <code>{success}</code>\n"
                f"⛔ Blocked: <code>{blocked}</code>\n"
                f"🗑️ Deleted: <code>{deleted}</code>\n"
                f"⏱️ Time: {elapsed}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ CANCEL", callback_data="broadcast_cancel#users")]]))
            await asyncio.sleep(0.1)
    elapsed = get_readable_time(time.time() - start_time)
    final_status = (
        f"{'❌ <b>Broadcast Cancelled.</b>' if cancelled else '✅ <b>Broadcast Completed.</b>'}\n\n"
        f"🕒 Time: {elapsed}\n"
        f"👥 Total: <code>{total_users}</code>\n"
        f"📬 Success: <code>{success}</code>\n"
        f"⛔ Blocked: <code>{blocked}</code>\n"
        f"🗑️ Deleted: <code>{deleted}</code>\n"
        f"❌ Failed: <code>{failed}</code>"
    )
    await techifybots_status_msg.edit(final_status)

@Client.on_message(filters.command("grp_broadcast") & filters.user(ADMINS) & filters.private)
async def broadcast_group(bot, message):
    if not message.reply_to_message:
        return await message.reply("<b>Reply to a message to group broadcast.</b>", parse_mode=enums.ParseMode.HTML)
    ask = await message.reply("𝖣𝗈 𝗒𝗈𝗎 𝗐𝖺𝗇𝗍 𝗍𝗈 𝗉𝗂𝗇 𝗍𝗁𝗂𝗌 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗂𝗇 𝗀𝗋𝗈𝗎𝗉𝗌?", reply_markup=ReplyKeyboardMarkup([["Yes", "No"]], one_time_keyboard=True, resize_keyboard=True))
    try:
        techifybots_user_response = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id, timeout=60)
    except asyncio.TimeoutError:
        await ask.delete()
        return await message.reply("❌ Timed out. Broadcast cancelled.")
    await ask.delete()
    if techifybots_user_response.text not in ("Yes", "No"):
        return await message.reply("❌ Invalid input. Broadcast cancelled.")
    is_pin = techifybots_user_response.text == "Yes"
    b_msg = message.reply_to_message
    chats = await db.get_all_chats()
    total_chats = await db.total_chat_count()
    techifybots_status_msg = await message.reply_text("📤 <b>Broadcasting your message to groups...</b>")
    start_time = time.time()
    done = success = failed = 0
    cancelled = False
    async with lock:
        async for chat in chats:
            time_taken = get_readable_time(time.time() - start_time)
            if temp.B_GROUPS_CANCEL:
                temp.B_GROUPS_CANCEL = False
                cancelled = True
                break
            try:
                sts = await groups_broadcast(int(chat['id']), b_msg, is_pin)
            except Exception as e:
                logging.exception(f"Error broadcasting to group {chat['id']}")
                sts = 'Error'
            if sts == "Success":
                success += 1
            else:
                failed += 1
            done += 1
            if done % 10 == 0:
                await techifybots_status_msg.edit(
                    f"📣 <b>Group broadcast progress:</b>\n\n"
                    f"👥 Total Groups: <code>{total_chats}</code>\n"
                    f"✅ Completed: <code>{done} / {total_chats}</code>\n"
                    f"📬 Success: <code>{success}</code>\n"
                    f"❌ Failed: <code>{failed}</code>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ CANCEL", callback_data="broadcast_cancel#groups")]]))
    time_taken = get_readable_time(time.time() - start_time)
    final_status = (
        f"{'❌ <b>Groups broadcast cancelled!</b>' if cancelled else '✅ <b>Group broadcast completed.</b>'}\n"
        f"⏱️ Completed in {time_taken}\n\n"
        f"👥 Total Groups: <code>{total_chats}</code>\n"
        f"✅ Completed: <code>{done} / {total_chats}</code>\n"
        f"📬 Success: <code>{success}</code>\n"
        f"❌ Failed: <code>{failed}</code>"
    )
    try:
        await techifybots_status_msg.edit(final_status)
    except MessageTooLong:
        with open("reason.txt", "w+") as outfile:
            outfile.write(str(failed))
        await message.reply_document("reason.txt", caption=final_status)
        os.remove("reason.txt")

@Client.on_callback_query(filters.regex(r'^broadcast_cancel'))
async def broadcast_cancel(bot, query):
    _, target = query.data.split("#", 1)
    if target == 'users':
        temp.B_USERS_CANCEL = True
        await query.message.edit("🛑 ᴛʀʏɪɴɢ ᴛᴏ ᴄᴀɴᴄᴇʟ ᴜꜱᴇʀꜱ ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...")
    elif target == 'groups':
        temp.B_GROUPS_CANCEL = True
        await query.message.edit("🛑 ᴛʀʏɪɴɢ ᴛᴏ ᴄᴀɴᴄᴇʟ ɢʀᴏᴜᴘꜱ ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...")

@Client.on_message(filters.command("clear_junk") & filters.user(ADMINS))
async def remove_junkuser__db(bot, message):
    users = await db.get_all_users()
    b_msg = message 
    sts = await message.reply_text('ɪɴ ᴘʀᴏɢʀᴇss...')   
    start_time = time.time()
    total_users = await db.total_users_count()
    blocked = 0
    deleted = 0
    failed = 0
    done = 0
    async for user in users:
        pti, sh = await clear_junk(int(user['id']), b_msg)
        if pti == False:
            if sh == "Blocked":
                blocked+=1
            elif sh == "Deleted":
                deleted += 1
            elif sh == "Error":
                failed += 1
        done += 1
        if not done % 50:
            await sts.edit(f"In Progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nBlocked: {blocked}\nDeleted: {deleted}")    
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.delete()
    await bot.send_message(message.chat.id, f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nBlocked: {blocked}\nDeleted: {deleted}")

@Client.on_message(filters.command("junk_group") & filters.user(ADMINS))
async def junk_clear_group(bot, message):
    groups = await db.get_all_chats()
    if not groups:
        grp = await message.reply_text("❌ Nᴏ ɢʀᴏᴜᴘs ғᴏᴜɴᴅ ғᴏʀ ᴄʟᴇᴀʀ Jᴜɴᴋ ɢʀᴏᴜᴘs.")
        await asyncio.sleep(60)
        await grp.delete()
        return
    b_msg = message
    sts = await message.reply_text(text='..............')
    start_time = time.time()
    total_groups = await db.total_chat_count()
    done = 0
    failed = ""
    deleted = 0
    async for group in groups:
        pti, sh, ex = await junk_group(int(group['id']), b_msg)        
        if pti == False:
            if sh == "deleted":
                deleted+=1 
                failed += ex 
                try:
                    await bot.leave_chat(int(group['id']))
                except Exception as e:
                    print(f"{e} > {group['id']}")  
        done += 1
        if not done % 50:
            await sts.edit(f"in progress:\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nDeleted: {deleted}")    
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.delete()
    try:
        await bot.send_message(message.chat.id, f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nDeleted: {deleted}\n\nFiled Reson:- {failed}")    
    except MessageTooLong:
        with open('junk.txt', 'w+') as outfile:
            outfile.write(failed)
        await message.reply_document('junk.txt', caption=f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nDeleted: {deleted}")
        os.remove("junk.txt")
               
@Client.on_message(filters.command('leave') & filters.user(ADMINS))
async def leave_a_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        chat = chat
    try:
        await bot.send_message(
            chat_id=chat,
            text='<b>ʜᴇʟʟᴏ ꜰʀɪᴇɴᴅꜱ, \nᴍʏ ᴀᴅᴍɪɴ ʜᴀꜱ ᴛᴏʟᴅ ᴍᴇ ᴛᴏ ʟᴇᴀᴠᴇ ꜰʀᴏᴍ ɢʀᴏᴜᴘ, ꜱᴏ ɪ ʜᴀᴠᴇ ᴛᴏ ɢᴏ ! \nɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴅᴅ ᴍᴇ ᴀɢᴀɪɴ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.</b>',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 ᴀᴅᴍɪɴ", user_id=int(OWNER))]]))
        await bot.leave_chat(chat)
        await message.reply(f"left the chat `{chat}`")
    except Exception as e:
        await message.reply(f'Error - {e}')

@Client.on_message(filters.command('disable') & filters.user(ADMINS))
async def disable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    cha_t = await db.get_chat(int(chat_))
    if not cha_t:
        return await message.reply("Chat Not Found In DB")
    if cha_t['is_disabled']:
        return await message.reply(f"This chat is already disabled:\nReason-<code> {cha_t['reason']} </code>")
    await db.disable_chat(int(chat_), reason)
    temp.BANNED_CHATS.append(int(chat_))
    await message.reply('Chat Successfully Disabled')
    try:
        await bot.send_message(
            chat_id=chat_, 
            text=f'<b>ʜᴇʟʟᴏ ꜰʀɪᴇɴᴅꜱ, \nᴍʏ ᴀᴅᴍɪɴ ʜᴀꜱ ᴛᴏʟᴅ ᴍᴇ ᴛᴏ ʟᴇᴀᴠᴇ ꜰʀᴏᴍ ɢʀᴏᴜᴘ, ꜱᴏ ɪ ʜᴀᴠᴇ ᴛᴏ ɢᴏ ! \nɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴅᴅ ᴍᴇ ᴀɢᴀɪɴ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.</b>\n𝖱𝖾𝖺𝗌𝗈𝗇: <code>{reason}</code>',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 ᴀᴅᴍɪɴ", user_id=int(OWNER))]]))
        await bot.leave_chat(chat_)
    except Exception as e:
        await message.reply(f"Error - {e}")

@Client.on_message(filters.command('enable') & filters.user(ADMINS))
async def re_enable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    sts = await db.get_chat(int(chat))
    if not sts:
        return await message.reply("Chat Not Found In DB !")
    if not sts.get('is_disabled'):
        return await message.reply('This chat is not yet disabled.')
    await db.re_enable_chat(int(chat_))
    temp.BANNED_CHATS.remove(int(chat_))
    await message.reply("Chat Successfully re-enabled")

@Client.on_message(filters.command('stats') & filters.user(ADMINS))
async def get_stats(bot, message):
    try:
        msg = await message.reply('ᴀᴄᴄᴇꜱꜱɪɴɢ ꜱᴛᴀᴛᴜꜱ ᴅᴇᴛᴀɪʟꜱ...')
        total_users = await db.total_users_count()
        totl_chats = await db.total_chat_count()
        premium = await db.all_premium_users()
        file1 = await Media.count_documents()
        DB_SIZE = 512 * 1024 * 1024
        dbstats = await db_stats.command("dbStats")
        current_db_size = dbstats['storageSize'] + dbstats['indexSize']
        dbs = await client.list_database_names()
        db_size = 0
        for db_name in dbs:
            if db_name in ["admin", "local"]:
                continue
            stats = await client[db_name].command("dbStats")
            db_size += stats['storageSize'] + stats['indexSize']
        free = DB_SIZE - db_size
        uptime = get_readable_time(time.time() - botStartTime)
        ram = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent()
        if MULTIPLE_DB == False:
            await msg.edit(script.STATUS_TXT.format(
                total_users, totl_chats, premium, file1, get_size(current_db_size), get_size(db_size), get_size(free), uptime, ram, cpu))                                               
            return
        file2 = await Media2.count_documents()
        db2stats = await db2_stats.command("dbStats")
        current_db2_size = db2stats['storageSize'] + db2stats['indexSize']
        dbs2 = await client2.list_database_names()
        db2_size = 0
        for db_name in dbs2:
            if db_name in ["admin", "local"]:
                continue
            stats = await client2[db_name].command("dbStats")
            db2_size += stats['storageSize'] + stats['indexSize']
        free2 = DB_SIZE - db2_size
        await msg.edit(script.MULTI_STATUS_TXT.format(
            total_users, totl_chats, premium, file1, get_size(current_db_size), get_size(db_size), get_size(free),
            file2, get_size(current_db2_size), get_size(db2_size), get_size(free2),
            uptime, ram, cpu, (int(file1) + int(file2))
            ))
    except Exception as e:
       print(f"Error In stats :- {e}")

@Client.on_message(filters.command('invite') & filters.user(ADMINS))
async def gen_invite(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    try:
        link = await bot.create_chat_invite_link(chat)
    except ChatAdminRequired:
        return await message.reply("Invite Link Generation Failed, I am Not Having Sufficient Rights")
    except Exception as e:
        return await message.reply(f'Error {e}')
    await message.reply(f'Here is your Invite Link {link.invite_link}')
    
@Client.on_message(filters.command('users') & filters.user(ADMINS))
async def list_users(bot, message):
    techifybots = await message.reply('Getting List Of Users')
    users = await db.get_all_users()
    out = "Users Saved In DB Are:\n\n"
    async for user in users:
        out += f"• <a href=tg://user?id={user['id']}>{user['name']}</a>"
        if user['ban_status']['is_banned']:
            out += '( Banned User )'
        out += '\n'
    try:
        await techifybots.edit_text(out)
    except MessageTooLong:
        with open('users.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('users.txt', caption="List Of Users")

@Client.on_message(filters.command('chats') & filters.user(ADMINS))
async def list_chats(bot, message):
    techifybots = await message.reply('Getting List Of chats')
    chats = await db.get_all_chats()
    out = "Chats Saved In DB Are:\n\n"
    async for chat in chats:
        out += f"• {chat['title']} `{chat['id']}`"
        if chat['chat_status']['is_disabled']:
            out += '( Disabled Chat )'
        out += '\n'
    try:
        await techifybots.edit_text(out)
    except MessageTooLong:
        with open('chats.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('chats.txt', caption="List Of Chats")

@Client.on_message(filters.command('clean_groups') & filters.user(ADMINS))
async def clean_groups_handler(client, message):
    msg = await message.reply('Cleaning groups... This may take a while.', quote=True)
    deleted_count = 0
    total_groups = await db.total_chat_count()
    processed = 0
    batch_size = 100
    chats = await db.get_all_chats()
    async for chat in chats:
        try:
            processed += 1
            chat_id = chat['id']
            try:
                await client.get_chat_member(chat_id, client.me.id)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await client.get_chat_member(chat_id, client.me.id)
                except (UserNotParticipant, PeerIdInvalid, ChannelInvalid):
                    await db.delete_chat(chat_id)
                    deleted_count += 1
                except Exception:
                    pass
            except (UserNotParticipant, PeerIdInvalid, ChannelInvalid):
                await db.delete_chat(chat_id)
                deleted_count += 1
            except Exception as e:
                print(f'Error checking chat {chat_id}: {e}')
                pass
            if processed % batch_size == 0:
                try:
                    await msg.edit(f'Progress: {processed}/{total_groups}\nDeleted: {deleted_count}')
                    await asyncio.sleep(2)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    await msg.edit(f'Progress: {processed}/{total_groups}\nDeleted: {deleted_count}')
        except Exception as e:
            print(f'Error in clean_groups loop: {e}')
    await msg.edit(f'**Clean Groups Complete**\n\nTotal Processed: {processed}\nDeleted: {deleted_count}')
