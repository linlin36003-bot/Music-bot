import os
import asyncio
import logging

from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, Update
from pytgcalls.types.stream import StreamAudioEnded

# ================== CONFIG ==================
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# ================== LOGGING ==================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] %(message)s",
)
logger = logging.getLogger("MusicBot")

# ================== CLIENTS ==================
bot = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("MusicUser", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call = PyTgCalls(user)

# ================== IN-MEMORY STORAGE ==================
queue = {}
current = {}
active = set()
user_lang = {}

# ================== LANGUAGE STRINGS ==================
STRINGS = {
    "en": {
        "start": "🎵 **Music Bot Started**\n\nUse /help to see all commands.",
        "help": (
            "**🎧 Music Bot Commands**\n\n"
            "▸ /start - Start the bot\n"
            "▸ /help - Show this menu\n"
            "▸ /play <song name or URL> - Play music in VC\n"
            "▸ /pause - Pause current song\n"
            "▸ /resume - Resume current song\n"
            "▸ /skip - Skip to next song\n"
            "▸ /stop - Stop music and leave VC\n"
            "▸ /queue - Show current queue\n"
            "▸ /song - Show currently playing\n"
            "▸ /lang <en|mm> - Change bot language\n"
            "▸ /broadcast <message> - (Owner only) Broadcast\n"
        ),
        "playing": "▶️ **Now Playing**\n\n🎶 {title}",
        "added": "➕ **Added to Queue**\n\n🎶 {title}\n📋 Position: {pos}",
        "paused": "⏸️ Music paused.",
        "resumed": "▶️ Music resumed.",
        "skipped": "⏭️ Skipped current song.",
        "stopped": "⏹️ Music stopped. Left voice chat.",
        "no_playing": "❌ Nothing is playing right now.",
        "no_queue": "📭 Queue is empty.",
        "queue_list": "📋 **Queue ({count})**\n\n{items}",
        "song_info": "🎶 **Now Playing**\n\n{title}",
        "not_in_vc": "❌ I'm not in a voice chat.",
        "join_vc_first": "❌ Join a voice chat first, then use this command.",
        "lang_set": "✅ Language changed to **English**.",
        "invalid_lang": "❌ Invalid language. Use `/lang en` or `/lang mm`.",
        "owner_only": "🚫 This command is for the bot owner only.",
        "processing": "⏳ Processing...",
        "error": "❌ Error: {err}",
        "broadcast_done": "✅ Broadcast sent to {ok} chats ({fail} failed).",
        "broadcast_start": "📢 Broadcasting...",
        "skip_end": "⏭️ Queue ended. Leaving voice chat.",
        "no_active": "❌ No active voice chat.",
    },
    "mm": {
        "start": "🎵 **သီချင်း Bot စတင်ပါပြီ**\n\nCommand အားလုံးကြည့်ရန် /help ကိုနှိပ်ပါ။",
        "help": (
            "**🎧 သီချင်း Bot Command များ**\n\n"
            "▸ /start - Bot စတင်ရန်\n"
            "▸ /help - Command များကြည့်ရန်\n"
            "▸ /play <သီချင်းနာမည် သို့မဟုတ် URL> - VC တွင်ဖွင့်ရန်\n"
            "▸ /pause - သီချင်းခေတ္တရပ်ရန်\n"
            "▸ /resume - ပြန်ဖွင့်ရန်\n"
            "▸ /skip - နောက်သီချင်းသို့ကျော်ရန်\n"
            "▸ /stop - သီချင်းရပ်ပြီး VC မှထွက်ရန်\n"
            "▸ /queue - တန်းစီထားသည့်သီချင်းများကြည့်ရန်\n"
            "▸ /song - လက်ရှိဖွင့်နေသည့်သီချင်းကြည့်ရန်\n"
            "▸ /lang <en|mm> - ဘာသာစကားပြောင်းရန်\n"
            "▸ /broadcast <message> - (Owner သာ) အသုံးပြုနိုင်သည်\n"
        ),
        "playing": "▶️ **ဖွင့်နေသည်**\n\n🎶 {title}",
        "added": "➕ **တန်းစီထည့်ပြီး**\n\n🎶 {title}\n📋 နေရာ: {pos}",
        "paused": "⏸️ သီချင်းခေတ္တရပ်ထားပါသည်။",
        "resumed": "▶️ သီချင်းပြန်ဖွင့်ပါပြီ။",
        "skipped": "⏭️ နောက်သီချင်းသို့ကျော်လိုက်ပါပြီ။",
        "stopped": "⏹️ သီချင်းရပ်ပြီး VC မှထွက်လိုက်ပါပြီ။",
        "no_playing": "❌ လက်ရှိဖွင့်နေသည့်သီချင်းမရှိပါ။",
        "no_queue": "📭 တန်းစီထားသည့်သီချင်းမရှိပါ။",
        "queue_list": "📋 **တန်းစီထားသည် ({count})**\n\n{items}",
        "song_info": "🎶 **လက်ရှိဖွင့်နေသည်**\n\n{title}",
        "not_in_vc": "❌ VC တွင်မရှိပါ။",
        "join_vc_first": "❌ ဦးစွာ Voice Chat ထဲဝင်ပါ၊ ပြီးမှ command သုံးပါ။",
        "lang_set": "✅ ဘာသာစကားကို **မြန်မာ** သို့ပြောင်းပြီးပါပြီ။",
        "invalid_lang": "❌ ဘာသာစကားမမှန်ပါ။ `/lang en` သို့မဟုတ် `/lang mm` သုံးပါ။",
        "owner_only": "🚫 ဤ command ကို Bot Owner သာသုံးနိုင်ပါသည်။",
        "processing": "⏳ ဆောင်ရွက်နေသည်...",
        "error": "❌ အမှား: {err}",
        "broadcast_done": "✅ Broadcast ပို့ပြီး ({ok} အောင်မြင်၊ {fail} မအောင်မြင်)။",
        "broadcast_start": "📢 Broadcast ပို့နေသည်...",
        "skip_end": "⏭️ တန်းစီသီချင်းကုန်သွားပါပြီ။ VC မှထွက်လိုက်ပါသည်။",
        "no_active": "❌ Active VC မရှိပါ။",
    },
}


def t(user_id: int, key: str, **kwargs) -> str:
    lang = user_lang.get(user_id, "en")
    text = STRINGS.get(lang, STRINGS["en"]).get(key, key)
    return text.format(**kwargs) if kwargs else text


# ================== HELPERS ==================
async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


async def get_youtube_info(query: str):
    import yt_dlp

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch1",
        "noplaylist": True,
    }
    loop = asyncio.get_event_loop()

    def _extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            return info.get("title", "Unknown"), info.get("url")

    return await loop.run_in_executor(None, _extract)


async def play_next(chat_id: int):
    if chat_id not in queue or not queue[chat_id]:
        current.pop(chat_id, None)
        try:
            await call.leave_group_call(chat_id)
        except Exception:
            pass
        if chat_id in active:
            active.discard(chat_id)
        return

    title, url = queue[chat_id].pop(0)
    current[chat_id] = (title, url)

    try:
        await call.play(chat_id, MediaStream(url, AudioQuality.HIGH))
        if chat_id not in active:
            active.add(chat_id)
    except Exception as e:
        logger.error(f"Play error: {e}")
        await play_next(chat_id)


# ================== STREAM ENDED HANDLER ==================
@call.on_update()
async def stream_handler(client, update: Update):
    if isinstance(update, StreamAudioEnded):
        chat_id = update.chat_id
        await play_next(chat_id)


# ================== COMMANDS ==================
@bot.on_message(filters.command("start") & filters.private)
async def cmd_start(client, message: Message):
    user_lang.setdefault(message.from_user.id, "en")
    await message.reply_text(t(message.from_user.id, "start"))


@bot.on_message(filters.command("help"))
async def cmd_help(client, message: Message):
    await message.reply_text(t(message.from_user.id, "help"))


@bot.on_message(filters.command("lang"))
async def cmd_lang(client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or args[1].lower() not in ("en", "mm"):
        await message.reply_text(t(message.from_user.id, "invalid_lang"))
        return
    user_lang[message.from_user.id] = args[1].lower()
    await message.reply_text(t(message.from_user.id, "lang_set"))


@bot.on_message(filters.command("play") & filters.group)
async def cmd_play(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /play <song name or URL>")
        return

    query = message.text.split(maxsplit=1)[1]
    chat_id = message.chat.id
    status = await message.reply_text(t(message.from_user.id, "processing"))

    try:
        title, url = await get_youtube_info(query)
    except Exception as e:
        await status.edit_text(t(message.from_user.id, "error", err=str(e)))
        return

    if chat_id in current:
        queue.setdefault(chat_id, []).append((title, url))
        pos = len(queue[chat_id])
        await status.edit_text(t(message.from_user.id, "added", title=title, pos=pos))
    else:
        current[chat_id] = (title, url)
        try:
            await call.play(chat_id, MediaStream(url, AudioQuality.HIGH))
            active.add(chat_id)
            await status.edit_text(t(message.from_user.id, "playing", title=title))
        except Exception as e:
            await status.edit_text(t(message.from_user.id, "error", err=str(e)))


@bot.on_message(filters.command("pause") & filters.group)
async def cmd_pause(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in active:
        await message.reply_text(t(message.from_user.id, "not_in_vc"))
        return
    try:
        await call.pause_stream(chat_id)
        await message.reply_text(t(message.from_user.id, "paused"))
    except Exception as e:
        await message.reply_text(t(message.from_user.id, "error", err=str(e)))


@bot.on_message(filters.command("resume") & filters.group)
async def cmd_resume(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in active:
        await message.reply_text(t(message.from_user.id, "not_in_vc"))
        return
    try:
        await call.resume_stream(chat_id)
        await message.reply_text(t(message.from_user.id, "resumed"))
    except Exception as e:
        await message.reply_text(t(message.from_user.id, "error", err=str(e)))


@bot.on_message(filters.command("skip") & filters.group)
async def cmd_skip(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in active:
        await message.reply_text(t(message.from_user.id, "not_in_vc"))
        return
    await message.reply_text(t(message.from_user.id, "skipped"))
    await play_next(chat_id)


@bot.on_message(filters.command("stop") & filters.group)
async def cmd_stop(client, message: Message):
    chat_id = message.chat.id
    try:
        await call.leave_group_call(chat_id)
    except Exception:
        pass
    active.discard(chat_id)
    queue.pop(chat_id, None)
    current.pop(chat_id, None)
    await message.reply_text(t(message.from_user.id, "stopped"))


@bot.on_message(filters.command("song") & filters.group)
async def cmd_song(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in current:
        await message.reply_text(t(message.from_user.id, "no_playing"))
        return
    title, _ = current[chat_id]
    await message.reply_text(t(message.from_user.id, "song_info", title=title))


@bot.on_message(filters.command("queue") & filters.group)
async def cmd_queue(client, message: Message):
    chat_id = message.chat.id
    q = queue.get(chat_id, [])
    if not q:
        await message.reply_text(t(message.from_user.id, "no_queue"))
        return
    items = "\n".join(f"{i+1}. {t[0]}" for i, t in enumerate(q[:20]))
    await message.reply_text(t(message.from_user.id, "queue_list", count=len(q), items=items))


# ================== BROADCAST (OWNER ONLY) ==================
@bot.on_message(filters.command("broadcast") & filters.private)
async def cmd_broadcast(client, message: Message):
    user_id = message.from_user.id

    if user_id != OWNER_ID:
        await message.reply_text(t(user_id, "owner_only"))
        return

    if len(message.command) < 2:
        await message.reply_text("Usage: /broadcast <message>")
        return

    text = message.text.split(maxsplit=1)[1]
    status = await message.reply_text(t(user_id, "broadcast_start"))

    ok, fail = 0, 0
    async for dialog in client.get_dialogs():
        try:
            await client.send_message(dialog.chat.id, text)
            ok += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    await status.edit_text(t(user_id, "broadcast_done", ok=ok, fail=fail))


# ================== STARTUP ==================
async def main():
    if not API_ID or not API_HASH or not BOT_TOKEN or not SESSION_STRING:
        raise SystemExit("❌ Missing required env vars: API_ID, API_HASH, BOT_TOKEN, SESSION_STRING")

    print("🚀 Starting user client...")
    await user.start()
    print("🚀 Starting bot client...")
    await bot.start()
    print("🚀 Starting PyTgCalls...")
    await call.start()
    print("✅ Bot is running!")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("👋 Bot stopped.")ge.reply_text(t(message.from_user.id, "error", err=str(e)))


@bot.on_message(filters.command("skip") & filters.group)
async def cmd_skip(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in active:
        await message.reply_text(t(message.from_user.id, "not_in_vc"))
        return
    await message.reply_text(t(message.from_user.id, "skipped"))
    await play_next(chat_id)


@bot.on_message(filters.command("stop") & filters.group)
async def cmd_stop(client, message: Message):
    chat_id = message.chat.id
    try:
        await call.leave_group_call(chat_id)
    except Exception:
        pass
    active.discard(chat_id)
    queue.pop(chat_id, None)
    current.pop(chat_id, None)
    await message.reply_text(t(message.from_user.id, "stopped"))


@bot.on_message(filters.command("song") & filters.group)
async def cmd_song(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in current:
        await message.reply_text(t(message.from_user.id, "no_playing"))
        return
    title, _ = current[chat_id]
    await message.reply_text(t(message.from_user.id, "song_info", title=title))


@bot.on_message(filters.command("queue") & filters.group)
async def cmd_queue(client, message: Message):
    chat_id = message.chat.id
    q = queue.get(chat_id, [])
    if not q:
        await message.reply_text(t(message.from_user.id, "no_queue"))
        return
    items = "\n".join(f"{i+1}. {t[0]}" for i, t in enumerate(q[:20]))
    await message.reply_text(t(message.from_user.id, "queue_list", count=len(q), items=items))


# ================== BROADCAST (OWNER ONLY) ==================
@bot.on_message(filters.command("broadcast") & filters.private)
async def cmd_broadcast(client, message: Message):
    user_id = message.from_user.id

    if user_id != OWNER_ID:
        await message.reply_text(t(user_id, "owner_only"))
        return

    if len(message.command) < 2:
        await message.reply_text("Usage: /broadcast <message>")
        return

    text = message.text.split(maxsplit=1)[1]
    status = await message.reply_text(t(user_id, "broadcast_start"))

    ok, fail = 0, 0
    async for dialog in client.get_dialogs():
        try:
            await client.send_message(dialog.chat.id, text)
            ok += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    await status.edit_text(t(user_id, "broadcast_done", ok=ok, fail=fail))


# ================== STARTUP ==================
async def main():
    if not API_ID or not API_HASH or not BOT_TOKEN or not SESSION_STRING:
        raise SystemExit("❌ Missing required env vars: API_ID, API_HASH, BOT_TOKEN, SESSION_STRING")

    print("🚀 Starting user client...")
    await user.start()
    print("🚀 Starting bot client...")
    await bot.start()
    print("🚀 Starting PyTgCalls...")
    await call.start()
    print("✅ Bot is running!")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("👋 Bot stopped.")
PYEOF
