import re
import os
from os import environ, getenv
from Script import script

id_pattern = re.compile(r'^.\d+$')

def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

SESSION = environ.get('SESSION', 'techifybots')
API_ID = int(environ.get('API_ID', ''))
API_HASH = environ.get('API_HASH', '')
BOT_TOKEN = environ.get('BOT_TOKEN', "")
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', False))
INDEX_CAPTION = bool(environ.get('INDEX_CAPTION', False))
COVER = bool(environ.get('COVER', False))
PICS = (environ.get('PICS', 'https://i.ibb.co/PzZNZHF6/IMG-20251116-113905-254.jpg https://i.ibb.co/8npWSZ5T/pic.jpg')).split()
MELCOW_PHOTO = environ.get("MELCOW_PHOTO", "https://i.ibb.co/2769f1rF/photo-2025-09-03-14-48-34-7548400762112442372.jpg")
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '1255023013').split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '').split()]
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', ''))
BIN_CHANNEL = int(environ.get('BIN_CHANNEL', ''))
PREMIUM_LOGS = int(environ.get('PREMIUM_LOGS', ''))
DELETE_CHANNELS = [int(dch) if id_pattern.search(dch) else dch for dch in environ.get('DELETE_CHANNELS', '').split()]
AUTH_CHANNELS = [int(ch) for ch in environ.get("AUTH_CHANNELS", "").split() if ch and id_pattern.match(ch)]
AUTH_REQ_CHANNELS = [int(ch) for ch in environ.get("AUTH_REQ_CHANNELS", "").split() if ch and id_pattern.match(ch)]
REQST_CHANNEL = int(ch) if (ch := environ.get("REQST_CHANNEL", "")) and id_pattern.search(ch) else None
SUPPORT_CHAT_ID = int(ch) if (ch := environ.get("SUPPORT_CHAT_ID", "")) and id_pattern.search(ch) else None

OWNER = int(os.environ.get("OWNER", "1255023013"))
CHANNEL_LINK = environ.get('CHANNEL_LINK', 'https://telegram.me/Techifybots')
GROUP_LINK = environ.get('GROUP_LINK', 'https://telegram.me/TechifySupport')

DATABASE_URI = environ.get('DATABASE_URI', "")
DATABASE_NAME = environ.get('DATABASE_NAME', "filter")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'files')
MULTIPLE_DB = is_enabled(os.environ.get('MULTIPLE_DB', "False"), False)
DATABASE_URI2 = environ.get('DATABASE_URI2', "")

UPDATE_NOTIFICATION = bool(environ.get('UPDATE_NOTIFICATION', False))
UPDATE_CHANNEL = int(environ.get('UPDATE_CHANNEL', ''))
IMAGE_FETCH = bool(environ.get('IMAGE_FETCH', True))
LINK_PREVIEW = bool(environ.get('LINK_PREVIEW', False))
ABOVE_PREVIEW = bool(environ.get('ABOVE_PREVIEW', False))
TMDB_API_KEY = environ.get('TMDB_API_KEY', '')
TMDB_POSTER = bool(environ.get('TMDB_POSTER', True))
LANDSCAPE_POSTER = bool(environ.get('LANDSCAPE_POSTER', True))

IS_VERIFY = is_enabled('IS_VERIFY', False)
LOG_API_CHANNEL = int(environ.get('LOG_API_CHANNEL', ''))
VERIFY_IMG = environ.get("VERIFY_IMG", "https://i.ibb.co/xqNtSMpS/photo-2025-09-18-15-24-38-7551450511015149572.jpg")
TUTORIAL = environ.get("TUTORIAL", "https://t.me/TechifyBots")
TUTORIAL_2 = environ.get("TUTORIAL_2", "https://t.me/TechifyBots")
TUTORIAL_3 = environ.get("TUTORIAL_3", "https://t.me/TechifyBots")
SHORTENER_API = environ.get("SHORTENER_API", "a7ac9b3012c67d7491414cf272d82593c75f6cbb")
SHORTENER_WEBSITE = environ.get("SHORTENER_WEBSITE", "omegalinks.in")
SHORTENER_API2 = environ.get("SHORTENER_API2", "a7ac9b3012c67d7491414cf272d82593c75f6cbb")
SHORTENER_WEBSITE2 = environ.get("SHORTENER_WEBSITE2", "omegalinks.in")
SHORTENER_API3 = environ.get("SHORTENER_API3", "a7ac9b3012c67d7491414cf272d82593c75f6cbb")
SHORTENER_WEBSITE3 = environ.get("SHORTENER_WEBSITE3", "omegalinks.in")
TWO_VERIFY_GAP = int(environ.get('TWO_VERIFY_GAP', "1200"))
THREE_VERIFY_GAP = int(environ.get('THREE_VERIFY_GAP', "54000"))

FAST_MODE = is_enabled(environ.get('FAST_MODE', "False"), False)
MAX_BTN = is_enabled((environ.get('MAX_BTN', "True")), True)
MAX_BTNS = environ.get("MAX_BTNS", "5")
MSG_ALRT = environ.get('MSG_ALRT', '𝖲𝗁𝖺𝗋𝖾 & 𝖲𝗎𝗉𝗉𝗈𝗋𝗍 𝖬𝖾 ♥️')
DELETE_TIME = int(environ.get("DELETE_TIME", "300"))
FILE_CAPTION = environ.get("FILE_CAPTION", f"{script.CAPTION}")
IMDB_TEMPLATE = environ.get("IMDB_TEMPLATE", f"{script.IMDB_TEMPLATE_TXT}")
MAX_LIST_ELM = int(environ.get("MAX_LIST_ELM") or 10) or None # Maximum number of elements in a list (default: 10, set 0 for no limit)
NO_RESULTS_MSG = bool(environ.get("NO_RESULTS_MSG", True))
P_TTI_SHOW_OFF = is_enabled((environ.get('P_TTI_SHOW_OFF', "False")), False)
IMDB = is_enabled((environ.get('IMDB', "False")), False)
TMDB_ON_SEARCH = is_enabled((environ.get('TMDB_ON_SEARCH', "False")), False)
AUTO_FILTER = is_enabled((environ.get('AUTO_FILTER', "True")), True)
AUTO_DELETE = is_enabled((environ.get('AUTO_DELETE', "True")), True)
LONG_IMDB_DESCRIPTION = is_enabled(environ.get("LONG_IMDB_DESCRIPTION", "False"), False)
SPELL_CHECK_REPLY = is_enabled(environ.get("SPELL_CHECK_REPLY", "True"), True)
MELCOW_NEW_USERS = is_enabled((environ.get('MELCOW_NEW_USERS', "False")), False)
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)
PM_SEARCH = bool(environ.get('PM_SEARCH', False))
EMOJI_MODE = bool(environ.get('EMOJI_MODE', True))
BUTTON_MODE = is_enabled((environ.get('BUTTON_MODE', "False")), False)
STREAM_MODE = bool(environ.get('STREAM_MODE', True))
PREMIUM_STREAM_MODE = bool(environ.get('PREMIUM_STREAM_MODE', False))

LANGUAGES = {"ᴛᴀᴍɪʟ":"tam","ᴛᴇʟᴜɢᴜ":"tel","ᴇɴɢʟɪsʜ":"eng","ʜɪɴᴅɪ":"hin","ᴊᴀᴘᴀɴᴇsᴇ":"jap"}
QUALITIES = ["360P", "480P", "720P", "1080P", "2160p"]
SEASON_COUNT = 12
SEASONS = [f"S{str(i).zfill(2)}" for i in range(1, SEASON_COUNT + 1)]
REACTIONS = ["🤝", "😇", "🤗", "😍", "👍", "🎅", "😐", "🥰", "🤩", "😱", "🤣", "😘", "👏", "😛", "😈", "🎉", "⚡️", "🫡", "🤓", "😎", "🏆", "🔥", "🤭", "🌚", "🆒", "👻", "😁"]
STAR_PREMIUM_PLANS = {10: "7day", 20: "15day", 40: "1month", 55: "45day", 75: "60day"}
BAD_WORDS = {"PrivateMovieZ", "toonworld4all", "themoviesboss", "1tamilmv", "tamilblasters", "1tamilblasters", "skymovieshd", "extraflix", "hdm2", "moviesmod", "hdhub4u", "mkvcinemas", "primefix", "join", "www", "villa", "tg", "original"}

IS_FILE_LIMIT = bool(environ.get('IS_FILE_LIMIT', True)) 
FILES_LIMIT = int(environ.get("FILES_LIMIT", "48"))
QUALITY_LIMIT = bool(environ.get('QUALITY_LIMIT', False)) 
FREE_QUALITIES = ["360p", "480p"]

PORT = int(environ.get("PORT", "8080"))
NO_PORT = bool(environ.get('NO_PORT', False))
APP_NAME = None
if 'DYNO' in environ:
    ON_HEROKU = True
    APP_NAME = environ.get('APP_NAME')
else:
    ON_HEROKU = False
BIND_ADRESS = str(getenv('WEB_SERVER_BIND_ADDRESS', 'alyafilterbot.onrender.com'))
FQDN = str(getenv('FQDN', BIND_ADRESS)) if not ON_HEROKU or getenv('FQDN') else APP_NAME+'.herokuapp.com'
URL = "https://{}/".format(FQDN) if ON_HEROKU or NO_PORT else "https://{}/".format(FQDN, PORT)
SLEEP_THRESHOLD = int(environ.get('SLEEP_THRESHOLD', '60'))
MULTI_CLIENT = False
PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))
if 'DYNO' in environ:
    ON_HEROKU = True
    APP_NAME = str(getenv('APP_NAME'))
else:
    ON_HEROKU = False
HAS_SSL = bool(getenv('HAS_SSL', True))
if HAS_SSL:
    URL = "https://{}/".format(FQDN)
else:
    URL = "http://{}/".format(FQDN)

if MULTIPLE_DB == False:
    DATABASE_URI = DATABASE_URI
    DATABASE_URI2 = DATABASE_URI
else:
    DATABASE_URI = DATABASE_URI
    DATABASE_URI2 = DATABASE_URI2

LOG_STR = "Current Customized Configurations are:-\n"
LOG_STR += ("IMDB Results are enabled, Bot will be showing imdb details for your queries.\n" if IMDB else "IMDB Results are disabled.\n")
LOG_STR += ("P_TTI_SHOW_OFF found, Users will be redirected to send /start to Bot PM instead of sending file directly.\n" if P_TTI_SHOW_OFF else "P_TTI_SHOW_OFF is disabled, files will be sent in PM instead of starting the bot.\n")
LOG_STR += ("BUTTON_MODE is found, filename and file size will be shown in a single button instead of two separate buttons.\n" if BUTTON_MODE else "BUTTON_MODE is disabled, filename and file size will be shown as different buttons.\n")
LOG_STR += (f"FILE_CAPTION enabled with value {FILE_CAPTION}, your files will be sent along with this customized caption.\n" if FILE_CAPTION else "No FILE_CAPTION Found, Default captions of file will be used.\n")
LOG_STR += ("Long IMDB storyline enabled." if LONG_IMDB_DESCRIPTION else "LONG_IMDB_DESCRIPTION is disabled, Plot will be shorter.\n")
LOG_STR += ("Spell Check Mode is enabled, bot will be suggesting related movies if movie name is misspelled.\n" if SPELL_CHECK_REPLY else "Spell Check Mode is disabled.\n")
