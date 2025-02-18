import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess
import urllib.parse
import yt_dlp
import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from pytube import YouTube
from aiohttp import web

from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

my_name = "ᴊᴏʜɴ✰ᴡɪᴄᴋ"

cookies_file_path = os.getenv("COOKIES_FILE_PATH", "youtube_cookies.txt")
authorized_users = {5850397219}
allowed_channels = set()  # Store allowed channel IDs here
admins = [5850397219]  # Replace with your admin's Telegram user ID

help_button_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Help", callback_data="help")],
    ]
)

# Function to format the remaining time
def format_remaining_time(expiration_datetime):
    remaining_time = expiration_datetime - datetime.now()
    days, seconds = remaining_time.days, remaining_time.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{days} Days, {hours} Hours, {minutes} Minutes"

# Function to handle subscription removal
async def check_subscriptions():
    while True:
        current_time = datetime.now()
        for user_id, details in list(authorized_users.items()):
            if details["expiration_datetime"] <= current_time:
                authorized_users.pop(user_id)
                await bot.send_message(
                    user_id,
                    "Your subscription has expired and you have been removed from the authorized users list."
                )
        await asyncio.sleep(3600)  # Check every hour

# Define the add_user command handler for admin
@bot.on_message(filters.command("add_user") & filters.user(admins))
async def add_user(client: Client, msg: Message):
    try:
        parts = msg.text.split()
        user_id = int(parts[1])
        subscription_days = int(parts[2])
        join_datetime = datetime.now()
        expiration_datetime = join_datetime + timedelta(days=subscription_days)
        
        if user_id not in authorized_users:
            authorized_users[user_id] = {
                "join_datetime": join_datetime,
                "subscription_days": subscription_days,
                "expiration_datetime": expiration_datetime
            }
            await client.send_photo(
                user_id,
                "IMG_20250218_013652_529.jpg",  # Replace with your offline image path
                caption=(
                    f"Congratulations! You have been added to the authorized users list for {subscription_days} days by {msg.from_user.mention}. 🎉\n\n"
                    f"⏰ Join Datetime: {join_datetime.strftime('%d-%m-%Y %I:%M:%S %p')}\n\n"
                    f"📅 Subscription Days: {subscription_days} Days\n\n"
                    f"⏰ Expiration DateTime: {expiration_datetime.strftime('%d-%m-%Y %I:%M:%S %p')}"
                )
            )
            await msg.reply(f"User {user_id} has been added to the authorized users list for {subscription_days} days.")
        else:
            await msg.reply(f"User {user_id} is already in the authorized users list.")
    except (IndexError, ValueError):
        await msg.reply("Usage: /add_user <user_id> <subscription_days>")

# Define the remove_user command handler for admin
@bot.on_message(filters.command("remove_user") & filters.user(admins))
async def remove_user(client: Client, msg: Message):
    try:
        user_id = int(msg.text.split()[1])
        if user_id in authorized_users:
            authorized_users.pop(user_id)
            await client.send_message(
                user_id,
                f"Sorry, you have been removed from the authorized users list by {msg.from_user.mention}."
            )
            await msg.reply(f"User {user_id} has been removed from the authorized users list.")
        else:
            await msg.reply(f"User {user_id} is not in the authorized users list.")
    except (IndexError, ValueError):
        await msg.reply("Usage: /remove_user <user_id>")

# Define the id command handler to get user or channel ID
@bot.on_message(filters.command("id"))
async def get_id(client: Client, msg: Message):
    if msg.chat.type == "private":
        await msg.reply(f"Your Telegram ID: {msg.from_user.id}")
    else:
        chat_name = msg.chat.title or "Unknown"
        chat_id = msg.chat.id
        await msg.reply(f"📃 Your Channel Name: {chat_name}\n"
                        f"🆔 Your Channel ID: {chat_id}\n\n"
                        "❌ This Chat ID is not in an Allowed Channel List\n\n"
                        "To add this Channel, Click to Copy the Below Command\n\n"
                        f"/add_channel {chat_id}\n\n"
                        "and send to the bot directly.")

# Define the add_channel command handler for admin
@bot.on_message(filters.command("add_channel") & filters.user(admins))
async def add_channel(client: Client, msg: Message):
    try:
        chat_id = int(msg.text.split()[1])
        allowed_channels.add(chat_id)
        await msg.reply(f"Channel ID {chat_id} has been added to the allowed channels list.")
    except (IndexError, ValueError):
        await msg.reply("Usage: /add_channel <channel_id>")

# Define the remove_channel command handler for admin
@bot.on_message(filters.command("remove_channel") & filters.user(admins))
async def remove_channel(client: Client, msg: Message):
    try:
        chat_id = int(msg.text.split()[1])
        if chat_id in allowed_channels:
            allowed_channels.remove(chat_id)
            await msg.reply(f"Channel ID {chat_id} has been removed from the allowed channels list.")
        else:
            await msg.reply(f"Channel ID {chat_id} is not in the allowed channels list.")
    except (IndexError, ValueError):
        await msg.reply("Usage: /remove_channel <channel_id>")

# Start the bot
async def main():
    async with bot:
        await bot.start()
        asyncio.create_task(check_subscriptions())
        


# Define aiohttp routes
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("https://text-leech-bot-for-render.onrender.com/")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

async def start_bot():
    await bot.start()
    print("Bot is up and running")

async def stop_bot():
    await bot.stop()

async def main():
    if WEBHOOK:
        # Start the web server
        app_runner = web.AppRunner(await web_server())
        await app_runner.setup()
        site = web.TCPSite(app_runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Web server started on port {PORT}")

    # Start the bot
    await start_bot()

    # Keep the program running
    try:
        while True:
            await bot.polling()  # Run forever, or until interrupted
    except (KeyboardInterrupt, SystemExit):
        await stop_bot()
    

async def start_bot():
    await bot.start()
    print("Bot is up and running")

async def stop_bot():
    await bot.stop()

async def main():
    if WEBHOOK:
        # Start the web server
        app_runner = web.AppRunner(await web_server())
        await app_runner.setup()
        site = web.TCPSite(app_runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Web server started on port {PORT}")

    # Start the bot
    await start_bot()

    # Keep the program running
    try:
        while True:
            await asyncio.sleep(3600)  # Run forever, or until interrupted
    except (KeyboardInterrupt, SystemExit):
        await stop_bot()
        
class Data:
    START = (
        "🌟 Welcome {0}! 🌟\n\n"
    )
# Define the start command handler
@bot.on_message(filters.command("start"))
async def start(client: Client, msg: Message):
    user = await client.get_me()
    mention = user.mention
    start_message = await client.send_message(
        msg.chat.id,
        Data.START.format(msg.from_user.mention)
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "Initializing Uploader bot... 🤖\n\n"
        "Progress: [⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "Loading features... ⏳\n\n"
        "Progress: [🟥🟥🟥⬜⬜⬜⬜⬜⬜] 25%\n\n"
    )
    
    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "This may take a moment, sit back and relax! 😊\n\n"
        "Progress: [🟧🟧🟧🟧🟧⬜⬜⬜⬜] 50%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "Checking Bot Status... 🔍\n\n"
        "Progress: [🟨🟨🟨🟨🟨🟨🟨⬜⬜] 75%\n\n"
    )

   
    await asyncio.sleep(1)
    if msg.from_user.id in authorized_users:
        details = authorized_users[msg.from_user.id]
        join_datetime = details["join_datetime"]
        subscription_days = details["subscription_days"]
        expiration_datetime = details["expiration_datetime"]
        remaining_time = format_remaining_time(expiration_datetime)

        offline_image_path = "IMG_20250218_013652_529.jpg"  # Replace with your offline image path
        await client.send_photo(
            msg.chat.id,
            offline_image_path,
            caption=(
                f"Great! You are a 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 member!\n\n  🌟 Welcome {msg.from_user.mention} ! 👋\n\n"
                f"⏰ Join Datetime : {join_datetime.strftime('%d-%m-%Y %I:%M:%S %p')}\n\n"
                f"📅 Subscription Days : {subscription_days} Days \n\n"
                f"⏰ Expiration DateTime : {expiration_datetime.strftime('%d-%m-%Y %I:%M:%S %p')}\n\n"
                f"⌛️Remaining Time : {remaining_time}\n\n"
                "I Am A Bot For Download Links From Your **🌟.TXT 🌟** File And Then Upload That File On Telegram."
                " So Basically If You Want To Use Me First Send Me /drm Command And Then Follow Few Steps..\n\n"
                "**├── Bot Made By : **『 🅹🅰️🅸 🆂🅷🆁🅸 🆁🅰️🅼 ⚡️ 🧑‍💻』**\n\n"
                "Use /stop to stop any ongoing task."
            ),
            reply_markup=help_button_keyboard
        )
    else:
        offline_image_path = "IMG_20250218_015150_501.jpg"  # Replace with your offline image path
        await client.send_photo(
            msg.chat.id,
            offline_image_path,
            caption=(
                f"  🌟 Welcome {msg.from_user.mention} ! 👋\n\n"
                "You are currently using the 𝗙𝗥𝗘𝗘 version. 🆓\n\n"
                "I'm here to make your life easier by downloading videos from your **.txt** file 📄 and uploading them directly to Telegram!\n\n"
                "Want to get started? Your id\n\n"
                "💬 Contact @Course_diploma_bot to get the 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 🎫 and unlock the full potential of your new bot! 🔓"
            )
        )

@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    if m.from_user.id not in authorized_users:
        await m.reply_text("Sorry, you are not eligible.")
        return
    await m.reply_text("**Stopped**🚦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)


# Define the drm command handler
@bot.on_message(filters.command(["drm"]))
async def upload(bot: Client, m: Message):
    if m.from_user.id not in authorized_users:
        await m.reply_text("Sorry, you are not eligible.")
        return

    editable = await m.reply_text('➠ 𝐒𝐞𝐧𝐝 𝐌𝐞 𝐘𝐨𝐮𝐫 𝐓𝐗𝐓 𝐅𝐢𝐥𝐞 𝐢𝐧 𝐀 𝐏𝐫𝐨𝐩𝐞𝐫 𝐖𝐚𝐲 **\n\n**├── Bot Made By : **『 🅹🅰️🅸 🆂🅷🆁🅸 🆁🅰️🅼 ⚡️ 🧑‍💻』**')
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)

    path = f"./downloads/{m.chat.id}"

    try:
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        links = []
        for i in content:
            links.append(i.split("://", 1))
        os.remove(x)
        # print(len(links))
    except:
        await m.reply_text("**Invalid file input.**")
        os.remove(x)
        return



    
   
    await editable.edit(f"**Total Number of 🔗 Links found are** **{len(links)}**\n**├─ 📽️ Video Links :**\n**├─ 📑 PDF Links :**\n**├─ 🖼️ Image Links :**\n**├─ 🔗 Other Links:**\n\n**Send From where You want to 📩 Download\n**Initial is  :** **1**\n\n **├── Bot Made By : **『 🅹🅰️🅸 🆂🅷🆁🅸 🆁🅰️🅼 ⚡️ 🧑‍💻』**")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    try:
        arg = int(raw_text)
    except:
        arg = 1

    await editable.edit("**Now Please Send Me Your Batch Name**")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    

    await editable.edit("**Enter Resolution 🎞️ : **\n\n**144**\n**240**\n**360**\n**480**\n**720**\n**1080**\n\n**please choose quality**")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"
    
    

    await editable.edit("Enter 🌟 Extracted name  or send \n\n 📄 You can also specify a custom name \n\n   『 🅹🅰️🅸 🆂🅷🆁🅸 🆁🅰️🅼 ⚡️ 🧑‍💻』 ")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    highlighter  = f"️ ⁪⁬⁮⁮⁮"
    if raw_text3 == 'Robin':
        MR = highlighter 
    else:
        MR = raw_text3
    await editable.edit("**𝗘𝗻𝘁𝗲𝗿 𝗣𝘄 𝗧𝗼𝗸𝗲𝗻 𝗙𝗼𝗿 𝗣𝘄 𝗨𝗽𝗹𝗼𝗮𝗱𝗶𝗻𝗴 𝗼𝗿 𝗦𝗲𝗻𝗱 `'noo'` 𝗙𝗼𝗿 𝗢𝘁𝗵𝗲𝗿𝘀**")
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = input4.text
    await input4.delete(True)
    if raw_text4 == 'noo':
        MR = token
    else:
        MR = raw_text4
   
    await editable.edit("Now Upload a Thumbnail URL 🔗 =  \n Or if don't want thumbnail send = no")
    input6 = message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6.text
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb == "no"

    if len(links) == 1:
        count = 1
    else:
        count = int(raw_text)   
    try:
        for i in range(arg-1, len(links)):

            Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + Vxy
            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
                

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            elif 'videos.classplusapp' in url or "tencdn.classplusapp" in url or "webvideos.classplusapp.com" in url or "media-cdn-alisg.classplusapp.com" in url or "videos.classplusapp" in url or "videos.classplusapp.com" in url or "media-cdn-a.classplusapp" in url or "media-cdn.classplusapp" in url:
             url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0'}).json()['url']

            elif "apps-s3-jw-prod.utkarshapp.com" in url:
                if 'enc_plain_mp4' in url:
                    url = url.replace(url.split("/")[-1], res+'.mp4')
                    
                elif 'Key-Pair-Id' in url:
                    url = None
                    
                elif '.m3u8' in url:
                    q = ((m3u8.loads(requests.get(url).text)).data['playlists'][1]['uri']).split("/")[0]
                    x = url.split("/")[5]
                    x = url.replace(x, "")
                    url = ((m3u8.loads(requests.get(url).text)).data['playlists'][1]['uri']).replace(q+"/", x)
                    
            elif '/master.mpd' in url:
             vid_id =  url.split("/")[-2]
             url =  f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={raw_text4}"

            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'𝖏𝖍𝖔𝖓 𝖜𝖎𝖈𝖐 {name1[:60]}'
                      

            if "edge.api.brightcove.com" in url:
                bcov = 'bcov_auth=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjQyMzg3OTEsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiZEUxbmNuZFBNblJqVEROVmFWTlFWbXhRTkhoS2R6MDkiLCJmaXJzdF9uYW1lIjoiYVcxV05ITjVSemR6Vm10ak1WUlBSRkF5ZVNzM1VUMDkiLCJlbWFpbCI6Ik5Ga3hNVWhxUXpRNFJ6VlhiR0ppWTJoUk0wMVdNR0pVTlU5clJXSkRWbXRMTTBSU2FHRnhURTFTUlQwPSIsInBob25lIjoiVUhVMFZrOWFTbmQ1ZVcwd1pqUTViRzVSYVc5aGR6MDkiLCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQwOSIsInJlZmVycmFsX2NvZGUiOiJOalZFYzBkM1IyNTBSM3B3VUZWbVRtbHFRVXAwVVQwOSIsImRldmljZV90eXBlIjoiYW5kcm9pZCIsImRldmljZV92ZXJzaW9uIjoiUShBbmRyb2lkIDEwLjApIiwiZGV2aWNlX21vZGVsIjoiU2Ftc3VuZyBTTS1TOTE4QiIsInJlbW90ZV9hZGRyIjoiNTQuMjI2LjI1NS4xNjMsIDU0LjIyNi4yNTUuMTYzIn19.snDdd-PbaoC42OUhn5SJaEGxq0VzfdzO49WTmYgTx8ra_Lz66GySZykpd2SxIZCnrKR6-R10F5sUSrKATv1CDk9ruj_ltCjEkcRq8mAqAytDcEBp72-W0Z7DtGi8LdnY7Vd9Kpaf499P-y3-godolS_7ixClcYOnWxe2nSVD5C9c5HkyisrHTvf6NFAuQC_FD3TzByldbPVKK0ag1UnHRavX8MtttjshnRhv5gJs5DQWj4Ir_dkMcJ4JaVZO3z8j0OxVLjnmuaRBujT-1pavsr1CCzjTbAcBvdjUfvzEhObWfA1-Vl5Y4bUgRHhl1U-0hne4-5fF0aouyu71Y6W0eg'
                url = url.split("bcov_auth")[0]+bcov
                
            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
            
            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'

            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'

            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:  
                
                cc = f'**——— ✦ ** {str(count).zfill(3)}.**——— ✦ ** \n\n** 🎞️ Title :**{𝗻𝗮𝗺𝗲𝟭}\n**├── Extention : @Course_diploma_bot.mkv**\n**├── Resolution : {res}**\n\n**📚 Course** » **{raw_text0}**\n\n**🌟 Extracted By** **{raw_text3}**'
                cc1 = f'**——— ✦ ** {str(count).zfill(3)}.**——— ✦ **\n\n**📁 Title  :** {𝗻𝗮𝗺𝗲𝟭}\n**├── Extention : @Course_diploma_bot.pdf**\n\n**📚 Course** » **{raw_text0}**\n\n**🌟 Extracted By** **{raw_text3}**'
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        copy = await bot.send_document(chat_id=m.chat.id,document=ka, caption=cc1)
                        count+=1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue
                
                elif ".pdf" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue
                else:
                    progress_percent = (count / len(links)) * 100
                    Show = f"**🚀 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒 = {progress_percent:.2f}%  🚀... »**\n\n**├──🎞️ 📊 Total Links = {len(links)}**\n\n**├──🎞️ ⚡️ Currently On = {str(count).zfill(3)}**\n\n**├──🎞️ 🔥 Remaining Links = {len(links) - count}**\n\n**├──🎞️ 📈 Progress = {progress_percent:.2f}% **\n\n**├──🎞️ Title** {name}\n\n**├── Resolution {raw_text2}**\n\n**├── Url : ** `Time Gya Url Dekhne ka 😅`\n\n**├── Bot Made By : **『 🅹🅰️🅸 🆂🅷🆁🅸 🆁🅰️🅼 ⚡️ 🧑‍💻』"
                    prog = await m.reply_text(Show)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    time.sleep(1)

            except Exception as e:
                await m.reply_text(
                    f"**downloading Interupted **\n{str(e)}\n**Name** » {name}\n**Link** » `{url}`"
                )
                continue

    except Exception as e:
        await m.reply_text(e)
    await m.reply_text("**𝔻ᴏɴᴇ 𝔹ᴏ𝕤𝕤😎**")


bot.run()
