from keys import API_ID, API_HASH
from pyrogram import Client
from typing import AsyncGenerator, List
from pyrogram.types import Message
import asyncio
import os

# ! donor_channel_id = klone qilmoqchi bo'lgan kanal ssilkasi
# ! my_channel_id - bzining kanal

async def clone_content(donor_channel_id: int, my_channel_id: int, limit: int):
    client = Client(name='my_session', api_id=API_ID, api_hash=API_HASH)
    await client.start()

    async for message in client.get_chat_history(chat_id=donor_channel_id, limit=limit):
        if message.media:
            if message.photo:  # Если это изображение
                photo = await message.download(in_memory=True)
                await client.send_photo(chat_id=my_channel_id, photo=photo, caption=message.caption.html if message.caption else None)

            elif message.video:  # Если это видео
                video = await message.download(in_memory=True)
                await client.send_video(chat_id=my_channel_id, video=video, caption=message.caption.html if message.caption else None)

            elif message.document:  # Если это документ
                file_ext = message.document.file_name.split('.')[-1].lower()  # Получаем расширение файла
                file_path = await message.download()  # Скачиваем файл

                if file_ext == 'zip':
                    await client.send_document(chat_id=my_channel_id, document=file_path, caption=message.caption.html if message.caption else None)
                elif file_ext == 'jpg':
                    await client.send_photo(chat_id=my_channel_id, photo=file_path, caption=message.caption.html if message.caption else None)
                else:
                    await client.send_document(chat_id=my_channel_id, document=file_path, caption=message.caption.html if message.caption else None)

        elif message.text:  # Если это текстовое сообщение
            await client.send_message(chat_id=my_channel_id, text=message.text)
# from pyrogram.errors import FloodWait

# async def clone_content(donor_channel_id: int, my_channel_id: int, limit: int):
#     client = Client(name='my_session', api_id=API_ID, api_hash=API_HASH)
#     await client.start()

#     try:
#         async for message in client.get_chat_history(chat_id=donor_channel_id, limit=limit):
#             if message.media:
#                 if message.photo:
#                     photo = await message.download(in_memory=True)
#                     await client.send_photo(chat_id=my_channel_id, photo=photo, caption=message.caption.html if message.caption else None)

#                 elif message.video:
#                     video = await message.download(in_memory=True)
#                     await client.send_video(chat_id=my_channel_id, video=video, caption=message.caption.html if message.caption else None)

#                 elif message.document:
#                     file_ext = message.document.file_name.split('.')[-1].lower()
#                     file_path = await message.download()

#                     if file_ext == 'zip':
#                         await client.send_document(chat_id=my_channel_id, document=file_path, caption=message.caption.html if message.caption else None)
#                     elif file_ext == 'jpg':
#                         await client.send_photo(chat_id=my_channel_id, photo=file_path, caption=message.caption.html if message.caption else None)
#                     else:
#                         await client.send_document(chat_id=my_channel_id, document=file_path, caption=message.caption.html if message.caption else None)

#             elif message.text:
#                 await client.send_message(chat_id=my_channel_id, text=message.text)

#     except FloodWait as e:
#         print(f"Flood wait error. Waiting for {e.value} seconds.")
#         await asyncio.sleep(e.value)
#         await clone_content(donor_channel_id, my_channel_id, limit)  # Retry after wait

#     finally:
#         await client.stop()

if __name__ == '__main__':
    limit = int(input("Введите количество последних постов для клонирования: "))
    asyncio.run(clone_content(donor_channel_id=-1002110432893, my_channel_id=-1002082039085, limit=limit))
