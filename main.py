import asyncio
import os
from telethon.sync import TelegramClient, events
from telethon.tl import functions, types
from telethon.errors.rpcerrorlist import FloodWaitError
import time
import random

API_TOKEN = os.environ['API_TOKEN']
API_HASH = os.environ['API_HASH']
API_ID = int(os.environ['API_ID'])

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=API_TOKEN)

with TelegramClient('my_account', API_ID, API_HASH) as client:
    # Define a function to simulate typing
    async def simulate_typing(msg, text):
        for char in text:
            await client.send_typing(msg.chat_id)
            await asyncio.sleep(0.05)


    # Define a function to edit a message
    async def edit_message(msg, text):
        await msg.edit(text)
        await asyncio.sleep(0.05)


    # Define a function to send messages
    async def send_message(chat, text):
        msg = await client.send_message(chat, text)
        return msg


    # Define the '.type' command handler
    @client.on(events.NewMessage(pattern=r'\.type (.+)', outgoing=True))
    async def type_handler(event):
        orig_text = event.pattern_match.group(1)
        tbp = ""  # to be printed
        typing_symbol = "▒"

        async with client.action(event.chat_id, 'typing'):
            for char in orig_text:
                tbp += char
                await edit_message(event, tbp + typing_symbol)
                await asyncio.sleep(0.05)

        await edit_message(event, orig_text)


    # Define the '.hack' command handler
    @client.on(events.NewMessage(pattern=r'\.hack', outgoing=True))
    async def hack_handler(event):
        perc = 0
        message = await send_message(event.chat_id, "👮‍ Взлом пентагона в процессе ...")

        while perc < 100:
            text = f"👮‍ Взлом пентагона в процессе ... {perc}%"
            await edit_message(message, text)
            perc += random.randint(1, 3)
            await asyncio.sleep(0.1)

        await edit_message(message, "🟢 Пентагон успешно взломан!")
        await asyncio.sleep(3)

        message = await send_message(event.chat_id, "👽 Поиск секретных данных об НЛО ...")
        perc = 0

        while perc < 100:
            text = f"👽 Поиск секретных данных об НЛО ... {perc}%"
            await edit_message(message, text)
            perc += random.randint(1, 5)
            await asyncio.sleep(0.15)

        await edit_message(message, "🦖 Найдены данные о существовании динозавров на земле!")


    client.run_until_disconnected()
