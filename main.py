import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped

# FAKE VALUES (jaise tune bola tha)
API_ID = int("36032857")
API_HASH = "1335484542da44312a4e861ad7e41e32"
BOT_TOKEN = "8483486360:AAEyV4U9D2nq1GC1QK1unuy-SpQImJMpdLE"

OWNER_USERNAME = "ahamsharma578"
SESSION_FILE = "session.txt"

bot = Client("vc_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = None
vc = None
queue = {}

def save_session(s):
    with open(SESSION_FILE, "w") as f:
        f.write(s)

def load_session():
    if os.path.exists(SESSION_FILE):
        return open(SESSION_FILE).read().strip()
    return None

def yt_search(query):
    result = VideosSearch(query, limit=1).result()["result"][0]
    return {
        "title": result["title"],
        "url": result["link"],
        "thumb": result["thumbnails"][0]["url"]
    }

async def start_user():
    global user, vc
    s = load_session()
    if not s:
        return None

    user = Client("assistant", session_string=s, api_id=API_ID, api_hash=API_HASH)
    await user.start()

    vc = PyTgCalls(user)
    await vc.start()
    return True

# ---------- START COMMAND ----------
@bot.on_message(filters.private & filters.command("start"))
async def start(_, m):
    await m.reply(
        "🎵 **Premium VC Music Bot** 🔥\n\n"
        f"👑 Owner: @{OWNER_USERNAME}\n"
        "⚙️ Add session string using:\n`/string SESSION`\n\n"
        "🎶 Then use `/play song name` in groups!"
    )

# ---------- SAVE SESSION ----------
@bot.on_message(filters.private & filters.command("string"))
async def save_string(_, m):
    if m.from_user.username != OWNER_USERNAME:
        return await m.reply("❌ Only owner can set session!")

    if len(m.text.split()) < 2:
        return await m.reply("Usage: `/string YOUR_SESSION_STRING`")

    session = m.text.split(None, 1)[1]
    save_session(session)

    await m.reply("✅ Session saved!\nStarting assistant...")
    await start_user()

# ---------- PLAY ----------
@bot.on_message(filters.group & filters.command("play"))
async def play(_, m):
    global vc

    if not user:
        await start_user()

    if len(m.command) < 2:
        return await m.reply("❗ Use: `/play song name`")

    query = m.text.split(None, 1)[1]
    data = yt_search(query)

    chat_id = m.chat.id
    queue.setdefault(chat_id, []).append(data["url"])

    if len(queue[chat_id]) > 1:
        return await m.reply(f"➕ Added to queue: **{data['title']}**")

    await vc.join_group_call(chat_id, AudioPiped(data["url"]))

    await m.reply_photo(
        data["thumb"],
        caption=f"▶️ **Playing Now**\n🎵 {data['title']}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⏸ Pause", "pause"),
                InlineKeyboardButton("▶️ Resume", "resume")
            ],
            [
                InlineKeyboardButton("⏭ Skip", "skip"),
                InlineKeyboardButton("⏹ Stop", "stop")
            ]
        ])
    )

# ---------- BUTTONS ----------
@bot.on_callback_query()
async def buttons(_, q):
    chat_id = q.message.chat.id

    if q.data == "pause":
        await vc.pause_stream(chat_id)
        return await q.answer("⏸ Paused")

    if q.data == "resume":
        await vc.resume_stream(chat_id)
        return await q.answer("▶️ Resumed")

    if q.data == "skip":
        if len(queue.get(chat_id, [])) <= 1:
            return await q.answer("❗ Queue empty")
        queue[chat_id].pop(0)
        await vc.change_stream(chat_id, AudioPiped(queue[chat_id][0]))
        return await q.answer("⏭ Skipped")

    if q.data == "stop":
        queue[chat_id] = []
        await vc.leave_group_call(chat_id)
        return await q.answer("⏹ Stopped")

# ---------- QUEUE ----------
@bot.on_message(filters.group & filters.command("queue"))
async def show_queue(_, m):
    q = queue.get(m.chat.id, [])
    if not q:
        return await m.reply("📭 Queue empty!")

    text = "📜 **Current Queue:**\n"
    for i, url in enumerate(q):
        text += f"{i+1}. {url}\n"

    await m.reply(text)

# ---------- STOP ----------
@bot.on_message(filters.group & filters.command("stop"))
async def stop(_, m):
    queue[m.chat.id] = []
    try:
        await vc.leave_group_call(m.chat.id)
    except:
        pass
    await m.reply("🛑 Stopped!")

# ---------- RUN ----------
async def main():
    await bot.start()

    if load_session():
        await start_user()

    print("Bot Running...")
    await asyncio.get_event_loop().create_future()

asyncio.run(main())
