import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from youtubesearchpython import VideosSearch
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped

# 🔥 FAKE VALUES (TUMHARE BOLE HUA)
API_ID = 36032857
API_HASH = "1335484542da44312a4e861ad7e41e32"
BOT_TOKEN = "8483486360:AAEyV4U9D2nq1GC1QK1unuy-SpQImJMpdLE"

OWNER = "@ahamsharma578"
SESSION_FILE = "session.txt"

bot = Client("indu_vc_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user = None
vc = None
queues = {}

def save_session(s):
    with open(SESSION_FILE, "w") as f:
        f.write(s)

def load_session():
    return open(SESSION_FILE).read().strip() if os.path.exists(SESSION_FILE) else None

def yt(query):
    vs = VideosSearch(query, limit=1).result()["result"][0]
    return {
        "title": vs["title"],
        "url": vs["link"],
        "thumb": vs["thumbnails"][0]["url"]
    }

async def start_assistant():
    global user, vc
    s = load_session()
    if not s:
        return None
    user = Client("assistant_user", session_string=s, api_id=API_ID, api_hash=API_HASH)
    await user.start()
    vc = PyTgCalls(user)
    await vc.start()
    return user

@bot.on_message(filters.private & filters.command("start"))
async def start_cmd(_, m):
    await m.reply_text(
        "🎧 **Indu VC Music Bot Ready!**\n"
        f"👑 Owner: {OWNER}\n\n"
        "Send `/string <session>` to add assistant.\n"
        "Then use `/play song` in group.\n\n"
        "🤖 Bot by **@ahamsharma578**"
    )

@bot.on_message(filters.private & filters.command("string"))
async def string_cmd(_, m):
    if m.from_user.username != OWNER.replace("@", ""):
        return await m.reply("❌ Only owner can add session.")

    if len(m.text.split()) < 2:
        return await m.reply("Usage: `/string SESSION_STRING`")

    save_session(m.text.split(None, 1)[1])
    await m.reply("✅ Session saved!")

    if await start_assistant():
        await m.reply("Assistant started successfully!")

@bot.on_message(filters.group & filters.command("play"))
async def play_cmd(_, m):
    if len(m.command) < 2:
        return await m.reply("Use: `/play song name`")

    if not user:
        await start_assistant()

    query = m.text.split(None, 1)[1]
    info = yt(query)
    url = info["url"]

    q = queues.setdefault(m.chat.id, [])
    q.append(url)

    if len(q) > 1:
        return await m.reply(f"➕ Added to queue: {info['title']}")

    await vc.join_group_call(m.chat.id, AudioPiped(url))

    await m.reply_photo(
        info["thumb"],
        caption=f"▶️ **Playing:** {info['title']}\n🎧 Requested by {m.from_user.mention}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏸ Pause", "pause"),
             InlineKeyboardButton("▶️ Resume", "resume")],
            [InlineKeyboardButton("⏭ Skip", "skip"),
             InlineKeyboardButton("⛔ Stop", "stop")]
        ])
    )

@bot.on_callback_query()
async def cb_handler(_, q):
    chat = q.message.chat.id
    if not vc:
        return

    if q.data == "pause":
        await vc.pause_stream(chat)
        return await q.answer("⏸ Paused")

    if q.data == "resume":
        await vc.resume_stream(chat)
        return await q.answer("▶️ Resumed")

    if q.data == "skip":
        if len(queues.get(chat, [])) <= 1:
            return await q.answer("❌ Queue empty")
        queues[chat].pop(0)
        await vc.change_stream(chat, AudioPiped(queues[chat][0]))
        return await q.answer("⏭ Skipped")

    if q.data == "stop":
        queues[chat] = []
        await vc.leave_group_call(chat)
        return await q.answer("⛔ Stopped")

async def run():
    await bot.start()
    if load_session():
        await start_assistant()
    print("Bot started successfully!")
    await asyncio.get_event_loop().create_future()

asyncio.run(run())
