import asyncio
from keys import API_ID, API_HASH
from pyrogram import Client, idle

from pyrogram.handlers import MessageHandler
from pyrogram.types import Message


async def get_channel_id(client: Client, message: Message):
    print(message)

async def start():
    client = Client(name='my_session', api_id=API_ID, api_hash=API_HASH)

    client.add_handler(MessageHandler(callback=get_channel_id))

    try:
        await client.start()
        await idle()
    except Exception as exc:
        await client.stop()

if __name__ == '__main__':
    asyncio.run(start())
