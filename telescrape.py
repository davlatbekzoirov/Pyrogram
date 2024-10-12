import abc
import asyncio
import os
import time
import typing
from datetime import datetime
from typing import List, AsyncIterable, Union

import hydrogram
import hydrogram.utils as utils
import pymongo
from dotenv import load_dotenv
from hydrogram import Client as TelegramClient, types, raw
from hydrogram.enums import MessageMediaType

load_dotenv()


def get_peer_type(peer_id: int) -> str:
    peer_id_str = str(peer_id)
    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    else:
        return "chat"


utils.get_peer_type = get_peer_type


class MongoClient:
    mongo_db = "telegram"
    client: typing.Optional[pymongo.MongoClient]
    db: typing.Optional[pymongo.database.Database]

    def __init__(self, uri):
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[self.mongo_db]
        self.posts = []
        self.current_album_id = None

    @staticmethod
    def _make_post_collection_name(project_id: int, group_id: int):
        group_id = str(group_id)
        if group_id.startswith("-100"):
            group_id = group_id.replace("-100", "", 1)
        return f"{project_id}_{group_id}"

    def save_post(self, project_id: int, group_id: int, post: dict):
        collection_name = self._make_post_collection_name(project_id, group_id)
        self.db[collection_name].update_one(
            {'_id': post['_id']}, {
                '$set': post,
                '$setOnInsert': {
                    'created_at': datetime.utcnow(),
                    'comments': [],
                },
            }, upsert=True
        )

    def add_comment_to_post(self, project_id: int, group_id: int, post_id: int, comment: dict):
        collection_name = self._make_post_collection_name(project_id, group_id)
        self.db[collection_name].update_one(
            {'_id': post_id},
            {'$push': {'comments': comment}}
        )

    def get_posts(self, project_id: int, group_id: int) -> list:
        collection_name = self._make_post_collection_name(project_id, group_id)
        for post in list(self.db[collection_name].find({})):
            if post.get("media_group_id"):
                if self.current_album_id is None:
                    self.current_album_id = post.get("media_group_id")

                if post.get("media_group_id") == self.current_album_id:
                    self.posts.append(post)
                else:
                    if self.posts:
                        result = self.posts
                        self.posts = [post]
                        self.current_album_id = post.get("media_group_id")
                        yield result
            else:
                if self.posts:
                    result = self.posts
                    self.posts = []
                    self.current_album_id = None
                    yield result
                yield post

        if self.posts:
            result = self.posts
            self.posts = []
            self.current_album_id = None
            yield result

    def close(self):
        self.client.close()


class Entity(abc.ABC):
    @abc.abstractmethod
    def parse(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    def send(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    def save(self, *args, **kwargs):
        ...


class MessageCopier:
    def __init__(self, client: TelegramClient, bot_client: TelegramClient = None):
        self.client = client
        self.bot_client = bot_client
        self.media_group_id = None

    def return_sender_function(self, message: types.Message):
        print(message.media)
        if message.media == MessageMediaType.AUDIO:
            return self.client.send_audio
        elif message.media == MessageMediaType.DOCUMENT:
            return self.client.send_document
        elif message.media == MessageMediaType.VIDEO:
            return self.client.send_video
        elif message.media == MessageMediaType.VOICE:
            return self.client.send_voice
        elif message.media == MessageMediaType.VIDEO_NOTE:
            return self.client.send_video_note
        elif message.media == MessageMediaType.PHOTO:
            return self.client.send_photo
        elif message.media == MessageMediaType.ANIMATION:
            return self.client.send_animation

    @staticmethod
    def get_file(message: types.Message, media, caption="", caption_entities=None):
        if message.photo:
            return types.InputMediaPhoto(
                media=media, caption=caption, caption_entities=caption_entities,
                has_spoiler=message.has_media_spoiler,
            )
        elif message.media.DOCUMENT:
            return types.InputMediaDocument(media=media, caption=caption, caption_entities=caption_entities)
        elif message.media.VIDEO:
            return types.InputMediaVideo(
                media=media, caption=caption, caption_entities=caption_entities,
                has_spoiler=message.has_media_spoiler,
            )
        elif message.media.AUDIO:
            return types.InputMediaAudio(media=media, caption=caption, caption_entities=caption_entities)

    async def get_media_group(
            self, message: types.Message
    ) -> List[Union[types.InputMediaPhoto, types.InputMediaDocument, types.InputMediaVideo, types.InputMediaAudio]]:
        first = True
        messages = []
        for message in await self.client.get_media_group(message.chat.id, message.id):
            media = await self.client.download_media(message, in_memory=True)
            if first:
                first = False
                messages.append(self.get_file(message, media, str(message.caption or ""), message.caption_entities))
            else:
                messages.append(self.get_file(message, media))
        return messages

    async def send_group_message(
            self, message: types.Message, chat_id: int, text, entities=None, reply_to: int = None
    ) -> List["types.Message"]:
        # try:
        #     return await self.client.copy_media_group(
        #         from_chat_id=message.chat.id,
        #         message_id=message.id,
        #         chat_id=chat_id,
        #         reply_to_message_id=reply_to
        #     )
        # except ChatForwardsRestricted as exc:
        media = await self.get_media_group(message)

        if not message.from_user:
            return_message = await self.client.send_media_group(
                chat_id=chat_id,
                media=media,
                reply_to_message_id=reply_to,
            )
        else:
            try:
                return_message = await self.bot_client.send_media_group(
                    chat_id=chat_id,
                    media=media,
                    reply_to_message_id=reply_to,
                )
            except ValueError:
                time.sleep(10)
                return_message = await self.send_group_message(message, chat_id, text, entities)
            except Exception as exc:
                return_message = await self.client.send_media_group(
                    chat_id=chat_id,
                    media=media,
                    reply_to_message_id=reply_to,
                )
        return return_message

    async def _send_file(self, client, message, chat_id, reply_to):
        caption = message.caption or ""
        if message.text:
            return await client.send_message(chat_id, message.text, reply_to_message_id=reply_to)

        file = await message.download(in_memory=True)

        if message.photo:
            return await client.send_photo(chat_id, file, caption=caption, reply_to_message_id=reply_to)
        elif message.video:
            return await client.send_video(chat_id, file, caption=caption, reply_to_message_id=reply_to)
        elif message.document:
            return await client.send_document(chat_id, file, caption=caption, reply_to_message_id=reply_to)
        elif message.voice:
            return await client.send_voice(chat_id, file, caption=caption, reply_to_message_id=reply_to)
        elif message.video_note:
            return await client.send_video_note(chat_id, file, reply_to_message_id=reply_to)
        elif message.animation:
            return await client.send_animation(chat_id, file, reply_to_message_id=reply_to)
        elif message.sticker:
            return await client.send_sticker(chat_id, file, reply_to_message_id=reply_to)

    async def send_message(
            self, message: types.Message, chat_id: int, reply_to: int = None
    ) -> "types.Message":
        # try:
        #     return await message.copy(chat_id, reply_to_message_id=reply_to)
        # except ChatForwardsRestricted as exc:
        #     pass
        # except Exception as exc:
        #     pass

        if not message.from_user:
            return await self._send_file(self.client, message, chat_id, reply_to)
        try:
            return await self._send_file(self.bot_client, message, chat_id, reply_to)
        except Exception as exc:
            return await self._send_file(self.client, message, chat_id, reply_to)


class UserClient:
    def __init__(self, session_path, api_id, api_hash):
        self.session_path = session_path
        self.api_id = api_id
        self.api_hash = api_hash
        self.current_album_id = None
        self.messages = []
        self.client = TelegramClient(self.session_path, self.api_id, self.api_hash)
        self.message_copier = MessageCopier(self.client)
        self._bot_client: typing.Optional[BotClient] = None

    @property
    def bot_client(self):
        return self._bot_client

    @bot_client.setter
    def bot_client(self, value):
        self._bot_client = value
        self.message_copier.bot_client = value

    async def get_discussion_message(
            self,
            chat_id: Union[int, str],
            message_id: int,
    ) -> "types.Message":
        r = await self.client.invoke(
            raw.functions.messages.GetDiscussionMessage(
                peer=await self.client.resolve_peer(chat_id), msg_id=message_id
            )
        )

        users = {u.id: u for u in r.users}
        chats = {c.id: c for c in r.chats}

        return await types.Message._parse(self.client, r.messages[-1], users, chats)

    @staticmethod
    async def get_chunk(
            *,
            client: "hydrogram.Client",
            chat_id: Union[int, str],
            limit: int = 0,
            offset: int = 0,
            from_message_id: int = 0,
            from_date: datetime = utils.zero_datetime(),
            reverse: bool = False,
            replies: int = 0,
    ):
        from_message_id = from_message_id or (1 if reverse else 0)

        messages = await utils.parse_messages(
            client,
            await client.invoke(
                raw.functions.messages.GetHistory(
                    peer=await client.resolve_peer(chat_id),
                    offset_id=from_message_id,
                    offset_date=utils.datetime_to_timestamp(from_date),
                    add_offset=offset * (-1 if reverse else 1) - (limit if reverse else 0),
                    limit=limit,
                    max_id=0,
                    min_id=0,
                    hash=0
                ),
                sleep_threshold=60
            ),
            replies=replies
        )

        if reverse:
            messages.reverse()

        return messages

    async def get_chat_history(
            self,
            chat_id: Union[int, str],
            limit: int = 0,
            offset: int = 0,
            offset_id: int = 0,
            offset_date: datetime = utils.zero_datetime(),
            reverse: bool = False,
            replies: int = 0,
    ) -> typing.Optional[typing.AsyncGenerator["types.Message", None]]:
        current = 0
        total = limit or (1 << 31) - 1
        limit = min(100, total)

        while True:
            messages = await self.get_chunk(
                client=self.client,
                chat_id=chat_id,
                limit=limit,
                offset=offset,
                from_message_id=offset_id,
                from_date=offset_date,
                reverse=reverse,
                replies=replies,
            )

            if not messages:
                return

            offset_id = messages[-1].id + (1 if reverse else 0)

            for message in messages:
                yield message

                current += 1

                if current >= total:
                    return

    async def get_entity(self, entity_id) -> Union["types.Chat", "types.ChatPreview"]:
        async with self.client:
            return await self.client.get_chat(entity_id)

    async def parse(
            self,
            chat: Union["types.Chat", "types.ChatPreview"],
            reverse: bool = True,
            limit: int = 0,
            offset_id: int = 0,
            offset_date: datetime = utils.zero_datetime(),
            replies: int = 0,
            reply_to: int = None,
    ) -> typing.Optional[typing.AsyncGenerator["types.Message", None]]:
        async with self.client:
            async for message in self.get_chat_history(
                    chat.id,
                    reverse=reverse,
                    limit=limit,
                    offset_id=offset_id,
                    offset_date=offset_date,
                    replies=replies,
                    # reply_to=reply_to,
            ):
                if message.service is not None:
                    continue

                if message.media_group_id:
                    if self.current_album_id is None:
                        self.current_album_id = message.media_group_id

                    if message.media_group_id == self.current_album_id:
                        self.messages.append(message)
                    else:
                        if self.messages:
                            result = self.messages
                            self.messages = [message]
                            self.current_album_id = message.media_group_id
                            yield result
                else:
                    if self.messages:
                        result = self.messages
                        self.messages = []
                        self.current_album_id = None
                        yield result
                    yield message

            if self.messages:
                result = self.messages
                self.messages = []
                self.current_album_id = None
                yield result

    async def send_message(
            self,
            target: Union["types.Chat", "types.ChatPreview", int],
            message: Union['types.Message', List['types.Message']],
            reply_to=None,
            comment_to=None,
            file=None,
            buttons=None,
    ):
        if not isinstance(target, int):
            target = target.id
        if isinstance(message, list):
            return await self.message_copier.send_group_message(
                message[0], target, message[0].caption, reply_to=reply_to
            )
        else:
            return await self.message_copier.send_message(message, target, reply_to=reply_to)


class BotClient(UserClient):
    def __init__(self, session_path, api_id, api_hash, token, client):
        self.session_path = session_path
        self.api_id = api_id
        self.api_hash = api_hash
        self.current_album_id = None
        self.messages = []
        self.token = token
        self.client = client
        self._bot_client = TelegramClient(self.session_path, self.api_id, self.api_hash, bot_token=token)
        self.message_copier = MessageCopier(self.client, self._bot_client)

    async def send_message(
            self,
            target: Union["types.Chat", "types.ChatPreview", int],
            message: Union['types.Message', List['types.Message']],
            reply_to=None,
            comment_to=None,
            file=None,
            buttons=None,
    ):
        return await super().send_message(target, message, reply_to, comment_to, file, buttons)


class MessageEntity(Entity):
    def __init__(
            self,
            client: 'UserClient',
            post: Union['types.Message', List['types.Message']],
            message: Union['types.Message', List['types.Message']]
    ):
        self.client = client
        self.post = post
        self.message = message

    def parse(self) -> List['MessageEntity']:
        ...

    def _get_sender_text(self, message):
        if message.sender:
            name = f"{message.sender.first_name} {message.sender.last_name} ({message.date})"
            url = f"tg://openmessage?user_id={message.sender.id}"
            if message.sender.username:
                url = f"https://t.me/{message.sender.username}"
            return f"[{name}]({url})"
        else:
            # if source_entity.username:
            #     url = f"https://t.me/{source_entity.username}"
            #     title = f"{source_entity.title} ({message.date})"
            #     button = Button.url(title, url=url)
            return f"[Group url](https://example.com/)"

    def append_sender(self):
        if isinstance(self.message, list):
            text = str(self.message[0].text)
            # self.message[0].text = f"{self._get_sender_text(self.message[0])}\n\n{text}"
        else:
            text = str(self.message.text)
            # self.message.text = f"{self._get_sender_text(self.message)}\n\n{text}"

    async def send(
            self, client: Union[UserClient, BotClient], target: 'PostEntity', reply_message_chat_id, reply_to,
    ) -> 'MessageEntity':
        post = target.post

        if isinstance(post, list):
            post = post[0]

        # self.append_sender()
        message = await client.send_message(
            reply_message_chat_id,
            self.message,
            reply_to=reply_to,
        )
        return MessageEntity(client, post, message)

    def save(self):
        ...


class PostEntity(Entity):
    def __init__(
            self,
            client: 'UserClient',
            channel: Union["types.Chat", "types.ChatPreview"],
            post: Union['types.Message', List['types.Message']],
            bot_client: 'BotClient' = None,
    ):
        self.client = client
        self.channel = channel
        self.post = post
        self.current_album_id = None
        self.messages = []

    @staticmethod
    async def get_discussion_replies(
        client: "hydrogram.Client",
        chat_id: Union[int, str],
        message_id: int,
        limit: int = 0,
        from_message_id: int = 0,
        reverse: bool = True,
    ) -> typing.Optional[typing.AsyncGenerator["types.Message", None]]:

        from_message_id = from_message_id or (1 if reverse else 0)

        current = 0
        total = limit or (1 << 31) - 1
        limit = min(100, total)

        while True:
            r = await client.invoke(
                raw.functions.messages.GetReplies(
                    peer=await client.resolve_peer(chat_id),
                    msg_id=message_id,
                    offset_id=from_message_id + 1,
                    offset_date=0,
                    add_offset=current * (-1 if reverse else 1) - (limit if reverse else 0),
                    limit=limit,
                    max_id=0,
                    min_id=0,
                    hash=0,
                )
            )

            users = {u.id: u for u in r.users}
            chats = {c.id: c for c in r.chats}
            messages = r.messages

            if not messages:
                return

            for message in messages:
                yield await types.Message._parse(client, message, users, chats, replies=0)

                current += 1

                if current >= total:
                    return

    async def _parse(self, reply_to_message_ids, from_message_id):
        async for message in self.get_discussion_replies(
                self.client.client,
                self.channel.id,
                message_id=reply_to_message_ids,
                from_message_id=from_message_id,
        ):
            if message.media_group_id:
                if self.current_album_id is None:
                    self.current_album_id = message.media_group_id

                if message.media_group_id == self.current_album_id:
                    self.messages.append(message)
                else:
                    if self.messages:
                        result = self.messages
                        result.reverse()
                        self.messages = [message]
                        self.current_album_id = message.media_group_id
                        yield result
            else:
                if self.messages:
                    result = self.messages
                    result.reverse()
                    self.messages = []
                    self.current_album_id = None
                    yield result
                yield message

        if self.messages:
            result = self.messages
            result.reverse()
            self.messages = []
            self.current_album_id = None
            yield result

    async def parse(self, reply_to_message_ids, from_message_id) -> typing.AsyncIterable['MessageEntity']:
        messages = []
        async for message in self._parse(reply_to_message_ids, from_message_id):
            messages.append(MessageEntity(self.client, self.post, message))
        messages.reverse()
        for message in messages:
            yield message

    async def send(
            self,
            client: Union[UserClient, BotClient],
            target: Union["types.Chat", "types.ChatPreview"],
            reply_to=None,
    ) -> 'PostEntity':
        post = await client.send_message(
            target,
            self.post,
            reply_to=reply_to,
        )
        return PostEntity(client, target, post)

    def save(self):
        ...


class ChannelEntity(Entity):
    def __init__(
            self,
            client: UserClient,
            channel: Union["types.Chat", "types.ChatPreview"],
    ):
        self._client = client
        self.channel = channel
        self.current_album_id = None
        self.grouped_posts = []
        self.current_grouped_post = None
        self.message_mapping = {}

    @property
    def client(self) -> UserClient:
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @classmethod
    async def get(cls, client: UserClient, channel_link: str) -> 'ChannelEntity':
        if channel_link.lstrip("-").isdigit():
            channel_link = int(channel_link)
        channel = await client.get_entity(channel_link)
        return cls(client, channel)

    async def parse(
            self,
            reverse: bool = True,
            limit: int = 0,
            offset_id: int = 0,
            offset_date: datetime = utils.zero_datetime(),
    ) -> AsyncIterable[PostEntity]:
        async for post in self.client.parse(self.channel, reverse, limit, offset_id, offset_date):
            yield PostEntity(self.client, self.channel, post)

    async def send(self, post: PostEntity, reply_to=None) -> PostEntity:
        return await post.send(self.client, self.channel, reply_to=reply_to)

    async def save(self):
        ...

    def get_reply_to(self, original_post):
        posts = original_post.post
        if not isinstance(posts, list):
            posts = [posts]
        for post in posts:
            if post.reply_to_message_id in self.message_mapping.keys():
                return self.message_mapping[post.reply_to_message_id]

    async def clone(
            self,
            target: 'ChannelEntity',
            reverse: bool = True,
            limit: int = 0,
            offset_id: int = 0,
            offset_date: datetime = utils.zero_datetime(),
            posts: list = None,
    ):
        if posts:
            offset_id = posts[-1]["_id"] + 1
            for post in posts:
                if not isinstance(post, list):
                    post = [post]
                for p in post:
                    self.message_mapping[p["original_post_id"]] = p["target_post_id"]

        async for original_post in self.parse(
                reverse,
                limit,
                offset_id,
                offset_date,
        ):
            target_post = await target.send(original_post, reply_to=self.get_reply_to(original_post))

            if isinstance(original_post.post, list):
                for i, post in enumerate(original_post.post):
                    self.message_mapping[post.id] = target_post.post[i].id
            else:
                self.message_mapping[original_post.post.id] = target_post.post.id

            yield original_post, target_post


class GroupEntity(Entity):
    def __init__(
            self,
            client: UserClient,
            channel_id: int,
            bot_client: BotClient = None,
    ):
        self.client = client
        self.channel_id = channel_id
        self.bot_client = bot_client
        self.comments_map = {}

    @classmethod
    def get(cls, client: UserClient, chat_id: int, bot_client: BotClient) -> 'GroupEntity':
        return cls(client, chat_id, bot_client)

    async def get_reply_to(self, post_id) -> tuple[int, int]:
        result = await self.client.get_discussion_message(self.channel_id, post_id)
        return result.chat.id, result.id

    def parse(self):
        ...

    def __get_reply_to(self, source_message, reply_to):
        reply_to_msg_id = None
        messages = source_message.message
        if not isinstance(messages, list):
            messages = [messages]

        for message in messages:
            if message.reply_to_message_id in self.comments_map.keys():
                reply_to_msg_id = self.comments_map[message.reply_to_message_id]

        if reply_to_msg_id:
            reply_to = reply_to_msg_id

        return reply_to

    async def send(
            self,
            source_message: 'MessageEntity',
            target_post: 'PostEntity',
            chat_id: int,
            reply_to: int,
            comments: list = None,
    ):
        reply_to = self.__get_reply_to(source_message, reply_to)

        target_message = await source_message.send(self.client, target_post, chat_id, reply_to)

        if isinstance(source_message.message, list):
            for i, message in enumerate(source_message.message):
                self.comments_map[message.id] = target_message.message[i].id
        else:
            self.comments_map[source_message.message.id] = target_message.message.id

        return target_message

    def get_user_info_message(self, message: MessageEntity):
        msg = message.message
        if isinstance(msg, list):
            msg = msg[0]

        if msg.from_user:
            if msg.from_user.first_name:
                name = msg.from_user.full_name
            else:
                name = "Удалённый аккаунт"

            if msg.from_user.username:
                link = f"https://t.me/{msg.from_user.username}"
                return f"[{name}]({link})"
            else:
                return f"[{name}]({msg.link})"
        else:
            return f"[{msg.sender_chat.title}]({msg.link})"

    async def clone_comments(self, post, source_channel, chat_id, reply_to):
        if isinstance(post, list):
            post = post[0]

        for comment in post.get("comments", []):
            self.comments_map[comment["original_message_id"]] = comment["target_message_id"]

        post_object = PostEntity(self.client, source_channel.channel, post)

        async for original_message in post_object.parse(post["original_post_id"], post.get("last_comment_id") or 0):

            check_msg = original_message.message
            if isinstance(check_msg, list):
                check_msg = check_msg[0]

            if check_msg.from_user:
                await self.bot_client._bot_client.send_message(
                    chat_id,
                    self.get_user_info_message(original_message),
                    reply_to_message_id=reply_to,
                    disable_web_page_preview=True,
                )
            else:
                await self.bot_client.client.send_message(
                    chat_id,
                    self.get_user_info_message(original_message),
                    reply_to_message_id=reply_to,
                    disable_web_page_preview=True,
                )

            yield original_message, await self.send(original_message, post_object, chat_id, reply_to)


    def save(self):
        ...


async def clone_channel(
        project_id: int,
        session_path: str,
        api_id: str,
        api_hash: str,
        token: str,
        source: str,  # link or id
        target: str,  # link or id
        offset_id: int = 0,
        offset_date: datetime = utils.zero_datetime(),
):
    client = UserClient(session_path, api_id, api_hash)
    bot_client = BotClient(f"{session_path}_bot", api_id, api_hash, token, client.client)
    client.bot_client = bot_client.bot_client

    source_channel = await ChannelEntity.get(client, source)
    target_channel = await ChannelEntity.get(client, target)

    mongo_client = MongoClient(os.getenv("MONGO_URI"))
    posts = list(mongo_client.get_posts(project_id, source_channel.channel.id))

    async for original_post, target_post in source_channel.clone(
            target_channel, offset_id=offset_id, offset_date=offset_date, posts=posts
    ):
        original_post = original_post.post
        target_post = target_post.post
        if not isinstance(original_post, list):
            original_post = [original_post]
            target_post = [target_post]

        for i, post in enumerate(original_post):
            mongo_client.save_post(project_id, source_channel.channel.id, {
                "_id": post.id,
                "original_channel_id": post.chat.id,
                "target_channel_id": target_post[i].chat.id,
                "original_post_id": post.id,
                "target_post_id": target_post[i].id,
                "media_group_id": post.media_group_id,
                "reply_to_msg_id": post.reply_to_message_id,
                "last_comment_id": None,
                "chat_id": None,
                "reply_to": None,
            })


async def clone_comments(
        project_id: int,
        session_path: str,
        api_id: str,
        api_hash: str,
        token: str,
        source: str,  # link or id
        target: str,  # link or id
):
    client = UserClient(session_path, api_id, api_hash)
    bot_client = BotClient(f"{session_path}_bot", api_id, api_hash, token, client.client)
    client.bot_client = bot_client.bot_client

    source_channel = await ChannelEntity.get(client, source)
    target_channel = await ChannelEntity.get(client, target)

    mongo_client = MongoClient(os.getenv("MONGO_URI"))
    posts = list(mongo_client.get_posts(project_id, source_channel.channel.id))

    async with client.client, bot_client._bot_client:
        group_entity = GroupEntity.get(client, target_channel.channel.id, bot_client)

        for post in posts:
            if isinstance(post, list):
                post = post[0]

            chat_id, reply_to = post.get("chat_id"), post.get("reply_to")

            if not chat_id or not reply_to:
                chat_id, reply_to = await group_entity.get_reply_to(post["target_post_id"])
                mongo_client.save_post(project_id, source_channel.channel.id, {
                    "_id": post["_id"],
                    "last_comment_id": None,
                    "chat_id": chat_id,
                    "reply_to": reply_to,
                })

            async for original_message, target_message in group_entity.clone_comments(
                    post, source_channel, chat_id, reply_to
            ):
                original_message = original_message.message
                target_message = target_message.message
                if not isinstance(original_message, list):
                    original_message = [original_message]
                    target_message = [target_message]

                for i, message in enumerate(original_message):
                    mongo_client.add_comment_to_post(
                        project_id, source_channel.channel.id, post["_id"], {
                            "_id": message.id,
                            "original_message_id": message.id,
                            "target_message_id": target_message[i].id,
                            "media_group_id": message.media_group_id,
                            "reply_to_msg_id": message.reply_to_message_id,
                        }
                    )
                    mongo_client.save_post(project_id, source_channel.channel.id, {
                        "_id": post["_id"],
                        "last_comment_id": message.id,
                    })


asyncio.run(clone_channel(
    111,  # ID проекта в БД (Django), пока не используется
    "/Users/nikolaj/projects/freelance/kwork-mini/CRT/backend/core/....+....",  # Путь до сессионного файла
    "21795....",  # Api Id
    "899a2dabc6fd3601a4a0f893....",  # Api Hash
    "......:.....-jJZ2v5svZY",  # Токен бота ТГ (Должен быть добавлен в целевой канал!)
    "https://t.me/+...",  # Канал донор (Закрытый)
    "https://t.me/+...",  # Целевой канал
    # offset_id=12,
))

asyncio.run(clone_comments(
    111,  # ID проекта в БД (Django), пока не используется
    "/Users/nikolaj/projects/freelance/kwork-mini/CRT/backend/core/....+....",  # Путь до сессионного файла
    "21795....",  # Api Id
    "899a2dabc6fd3601a4a0f893....",  # Api Hash
    "......:.....-jJZ2v5svZY",  # Токен бота ТГ (Должен быть добавлен в целевой канал!)
    "https://t.me/+...",  # Канал донор (Закрытый)
    "https://t.me/+...",  # Целевой канал
))
