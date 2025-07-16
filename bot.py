import os
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import aiohttp
import asyncio
import logging
from flask import Flask
from threading import Thread
import time

load_dotenv()

# ===== WOODcraft ==== SudoR2spr ====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise ValueError("API_ID, API_HASH, and BOT_TOKEN must be set.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Client("gofile_uploader_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0
    return f"{size:.{decimal_places}f} PB"

async def progress(current, total, message, status_message, start_time, file_name):
    now = time.time()
    diff = now - start_time or 1
    percentage = current * 100 / total
    speed = current / diff
    eta = (total - current) / speed
    progress_str = "⫷{0}{1}⫸".format(
        ''.join(["●" for _ in range(int(percentage // 10))]),
        ''.join(["○" for _ in range(10 - int(percentage // 10))])
    )
    text = (
        f"**📂 File:** `{file_name}`\n"
        f"**📦 Size:** `{human_readable_size(total)}`\n\n"
        f"**⬇️ Downloading...**\n"
        f"{progress_str} `{percentage:.2f}%`\n"
        f"**⚡ Speed:** `{human_readable_size(speed)}/s`\n"
        f"**⏱️ ETA:** `{int(eta)}s`"
    )
    try:
        await status_message.edit(text)
    except:
        pass

async def get_random_server():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.gofile.io/servers") as response:
                data = await response.json()
                servers = data['data']['servers']
                return random.choice(servers)['name']
    except Exception as e:
        logger.error(f"Error getting server: {e}")
        raise

async def upload_to_gofile(file_path):
    try:
        server = await get_random_server()
        upload_url = f"https://{server}.gofile.io/uploadFile"
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=os.path.basename(file_path))
                async with session.post(upload_url, data=data) as response:
                    result = await response.json()
                    return result["data"]["downloadPage"]
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise

@bot.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):
    file = message.document or message.video or message.audio
    file_name = file.file_name
    file_size = file.file_size
    
    status = await message.reply(f"📥 **Processing File**\n\n"
                               f"📂 **Name:** `{file_name}`\n"
                               f"📦 **Size:** `{human_readable_size(file_size)}`\n\n"
                               "⚙️ Starting download...")
    
    if file_size > 4 * 1024 * 1024 * 1024:
        await status.edit("❌ File too large. Limit is 4GB.")
        return

    start_time = time.time()
    file_path = await message.download(progress=progress, progress_args=(message, status, start_time, file_name))
    
    await status.edit(f"📤 **Uploading to GoFile**\n\n"
                     f"📂 **File:** `{file_name}`\n"
                     f"📦 **Size:** `{human_readable_size(file_size)}`\n\n"
                     "⏳ Please wait...")

    try:
        link = await upload_to_gofile(file_path)
        await status.edit(
            f"✅ **Upload Complete!**\n\n"
            f"📂 **File:** `{file_name}`\n"
            f"📦 **Size:** `{human_readable_size(file_size)}`\n\n"
            f"🔗 **Download Link:** [Click Here]({link})\n\n"
            "🚀 Powered by @Tj_Bots",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 Download Now", url=link)],
                [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/Tj_Bots")]
            ])
        )
    except Exception as e:
        await status.edit(f"❌ Upload failed: `{e}`")
    finally:
        os.remove(file_path)

# START COMMAND WITH IMAGE AND BUTTON
@bot.on_message(filters.command("start"))
async def start(client, message):
    image_url = "https://telegra.ph/file/3da7fe2febcfb9843853b-db22f1c6b1fc059305.jpg"  # Customize your own image
    caption = (
        "**Welcome to GoFile Uploader Bot!**\n\n"
        "Just send me any file (video, audio, or document) and I'll upload it to GoFile.\n\n"
        "⚡ Max file size: 4GB\n"
        "✅ Fast & Free\n\n"
        "__Powered by @Tj_Bots__"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/Tj_Bots")],
        [InlineKeyboardButton("🤖 How to Use", callback_data="help")]
    ])

    await message.reply_photo(photo=image_url, caption=caption, reply_markup=keyboard)

# HELP CALLBACK HANDLER
@bot.on_callback_query(filters.regex("^help$"))
async def help_callback(client, callback_query):
    help_text = (
        "**📚 GoFile Uploader Bot Help**\n\n"
        "1. **Upload Files:**\n"
        "   - Maximum file size: 4GB\n"
        "   - Supported file types: Videos, Audios, Documents\n\n"
        "2. **Process:**\n"
        "   - File download progress will be shown with progress bar\n"
        "   - You'll get download link after upload completes\n\n"
        "3. **Privacy:**\n"
        "   - Uploaded files are private (only accessible via the link you share)\n\n"
        "4. **Features:**\n"
        "   - Real-time upload/download progress\n"
        "   - File size and name displayed\n"
        "   - Fast download links\n\n"
        "⚠️ **Important Notes:**\n"
        "   - Large files may take longer to upload\n"
        "   - Keep stable internet connection during upload\n"
        "   - Files are automatically deleted after 10 days of inactivity (GoFile policy)\n\n"
        "🚀 **Powered by @Tj_Bots**"
    )

    await callback_query.message.edit(
        text=help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")],
            [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/Tj_Bots")]
        ]),
        disable_web_page_preview=True
    )

# BACK TO START CALLBACK HANDLER
@bot.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start(client, callback_query):
    image_url = "https://telegra.ph/file/3da7fe2febcfb9843853b-db22f1c6b1fc059305.jpg"
    caption = (
        "**Welcome to GoFile Uploader Bot!**\n\n"
        "Just send me any file (video, audio, or document) and I'll upload it to GoFile.\n\n"
        "⚡ Max file size: 4GB\n"
        "✅ Fast & Free\n\n"
        "__Powered by @Tj_Bots__"
    )
    
    await callback_query.message.delete()
    await callback_query.message.reply_photo(
        photo=image_url,
        caption=caption,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/Tj_Bots")],
            [InlineKeyboardButton("🤖 How to Use", callback_data="help")]
        ])
    )

# FLASK SERVER TO KEEP ALIVE
def run():
    app = Flask(__name__)
    @app.route('/')
    def home():
        return 'Bot is alive!'
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

Thread(target=run).start()
bot.run()
