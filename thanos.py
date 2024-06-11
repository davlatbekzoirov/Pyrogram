# Get a list of all non-admin members of a specified chat and shuffle this list.
# Then mute half of that list for 24 hours.

import time
from random import shuffle

from pyrogram import Client
from pyrogram.types import ChatPermissions
from pyrogram.errors import FloodWait

chat = "pyrogramlounge"
app = Client("my_account")

with app:
    members = [
        x
        for x in app.iter_chat_members(chat)
        if x.status not in ("administrator", "creator")
    ]
    shuffle(members)
    for i in range(len(members) // 2):
        try:
            app.restrict_chat_member(
                chat_id=chat,
                user_id=members[i].user.id,
                permissions=ChatPermissions(),
                until_date=int(time.time() + 86400),
            )
            print("muted", members[i].user.first_name)
        except FloodWait as e:
            print("> waiting", e.x, "seconds.")
            time.sleep(e.x)