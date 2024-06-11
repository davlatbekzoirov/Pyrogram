import os
import re
import random
import time
import pickle
from urllib.parse import urlparse, parse_qs

try:
    from colorama import init, Fore
except ModuleNotFoundError:
    os.system("pip install colorama==0.4.6")
    from colorama import init, Fore
try:
    from pyrogram import Client, raw
    from pyrogram.types import Message, Dialog, InlineKeyboardMarkup
    from pyrogram.enums import ChatType
    from pyrogram.errors import InviteRequestSent, UserNotParticipant
except ModuleNotFoundError:
    os.system("pip install https://github.com/KurimuzonAkuma/pyrogram/archive/dev.zip")
    os.system("pip install tgcrypto")
    from pyrogram import Client, raw
    from pyrogram.types import Message, Dialog, InlineKeyboardMarkup
    from pyrogram.enums import ChatType
    from pyrogram.errors import InviteRequestSent, UserNotParticipant
try:
    import webbrowser

    webbrowser.register("'termux-open \'%s\''", None)
except ModuleNotFoundError:
    os.system("pip install webbrowser")
    import webbrowser
except Exception as e:
    print(e, file=open("error.log", "w"))
init()
n = Fore.RESET
lg = Fore.LIGHTGREEN_EX
r = Fore.RED
w = Fore.WHITE
cy = Fore.CYAN
ye = Fore.YELLOW
error = f'{lg}[{r}!{lg}]{n}'
colors = [lg, r, w, cy, ye]
API_ID = 20991435
API_HASH = '8175e5a6d59e103658692c72c04f23bb'
VERSION = '2.1'
if not os.path.isdir('sessions'):
    os.mkdir('sessions')
if not os.path.isfile('accs.txt'):
    open('accs.txt', 'w').close()
if not os.path.isfile('group_id.txt'):
    GROUP_ID = input(
        f'{lg}[+] Premium yutganlarni yuborish uchun guruhning ID sini kiriting\nmisol uchun -1002103932313\n\n> {n}')
    with open('group_id.txt', 'w') as f:
        f.write(f'{GROUP_ID}')
else:
    with open('group_id.txt', 'r') as f:
        GROUP_ID = f.read()


def intro():
    banner = ['\'##::::\'##:\'####:\'########::\'##::::\'##:\'##::::\'##:',
              ' ###::\'###:. ##:: ##.... ##: ###::\'###:. ##::\'##::',
              ' ####\'####:: ##:: ##:::: ##: ####\'####::. ##\'##:::',
              ' ## ### ##:: ##:: ########:: ## ### ##:::. ###::::',
              ' ##. #: ##:: ##:: ##.. ##::: ##. #: ##::: ## ##:::',
              ' ##:.:: ##:: ##:: ##::. ##:: ##:.:: ##:: ##:. ##::',
              ' ##:::: ##:\'####: ##:::. ##: ##:::: ##: ##:::. ##:',
              '..:::::..::....::..:::::..::..:::::..::..:::::..::']
    for char in banner:
        print(f'{random.choice(colors)}%s%s' % (char, n))
    print()
    print(f'{cy}Telegram Akkauntni boshqarish uchun SCRIPT v{VERSION}')
    print(f'{cy}Scriptni olish uchun yoki fikrlar uchun quyidagi manzillarga murojaat qiling')
    print(f'{lg}Telegram: {w}@mirmakhamat{lg} | Instagram: {w}@mrsunnatov')


def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


def add_new_account():
    new_accounts = []
    number_to_add = input(f'\n{lg} [~] Nechta akkaunt qo`shmoqchisiz: {r}')
    for _ in range(int(number_to_add)):
        phone_number = input(f'\n{lg} [~] Akkauntning telefon raqamini kiriting: {r}')
        new_accounts.append(phone_number)
        with open('accs.txt', 'ab') as file:
            pickle.dump({'phone': phone_number, 'last_msg_id': 0}, file)
    print(f'\n{lg} [i] Barcha raqamlar saqlandi')
    clear_screen()
    print(f'\n{lg} [*] Yangi akkauntlardan tizimga kirish\n')
    for number in new_accounts:
        try:
            print(f'{lg} [+] Akkaunt: {cy}{number}{lg} -- qo`shilmoqda...')
            client = Client(f'sessions/{number}', api_id=API_ID, api_hash=API_HASH, phone_number=number)
            client.start()
            client.stop()
        except:
            print(f'{error}{r} Akkaunt: {cy}{number}{lg} -- xatolik bo`ldi')
        else:
            print(f'{lg}[+] Muvafaqqiyatli login bo`ldi')
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def filter_banned_accounts():
    accounts = []
    banned_accounts = []
    with open('accs.txt', 'rb') as file:
        try:
            accounts.append(pickle.load(file))
        except EOFError:
            pass
    print(f'\n{lg} [~] Akkauntlar filtrlamoqda, bu koproq vaqt olishi mumkin...')
    for account in accounts:
        phone = str(account['phone'])
        try:
            client = Client(f'sessions/{phone}', api_id=API_ID, api_hash=API_HASH)
            client.start()
            client.send_message('me', 'Hi from @mirmakhamat :D')
            time.sleep(2)
            client.stop()
        except:
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- xatolik bo`ldi')
            banned_accounts.append(account)
    if not banned_accounts:
        print(f'{lg}Tabriklayman! Banlangan akkauntlar yo`q')
    else:
        for account in accounts:
            if account in banned_accounts:
                accounts.remove(account)
        with open('accs.txt', 'wb') as file:
            for account in accounts:
                pickle.dump(account, file)
        print(f'{lg}[i] Barcha banlangan akkaunlar chiqarib tashlandi{n}')
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def delete_account():
    accounts = []
    with open('accs.txt', 'rb') as file:
        try:
            accounts.append(pickle.load(file))
        except EOFError:
            pass
    print(f'{lg}[i] O`chiriladigan akkauntni tanlang\n')
    for i, acc in enumerate(accounts):
        print(f"{lg}[{i}] {acc['phone']}{n}")
    index = int(input(f'\n{lg}[+] Tartib raqamini kiriting: {n}'))
    phone = str(accounts[index]['phone'])
    session_file = f'{phone}.session'
    if os.name == 'nt':
        os.system(f'del sessions\\{session_file}')
    else:
        os.system(f'rm sessions/{session_file}')
    del accounts[index]
    with open('accs.txt', 'wb') as f:
        for account in accounts:
            pickle.dump(account, f)
    print(f'\n{lg}[+] Account o`chirildi{n}')
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def show_all_accounts():
    accounts = []
    with open('accs.txt', 'rb') as f:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            pass
    print(f'\n{cy}')
    print('\tAkkauntlar ro`yhati')
    print('==========================================================')
    for account in accounts:
        print(f"\t{account['phone']}")
    print('==========================================================')
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def join_channels():
    n = int(input(f'\n{lg} [~] Nechta kanalga qo`shmilmoqchisiz: {r}'))
    channels = []
    for i in range(n):
        channel_link = input(f'\n{lg} [{i + 1}] Kanal linkini kiriting: {r}')
        channels.append(channel_link)
    accounts = []
    with open('accs.txt', 'rb') as f:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            pass
    for account in accounts:
        phone = str(account['phone'])
        try:
            client = Client(f'sessions/{phone}', api_id=API_ID, api_hash=API_HASH)
            client.start()
        except:
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- ulanishda xatolik bo`ldi')
            for channel in channels:
                try:
                    client.join_chat(channel)
                except InviteRequestSent:
                    print(
                        f"{lg} [~] Akkaunt: {cy}{phone}{lg}{' -- '} f'{channel}{' ga qo`shilish uchun so`rov yuborildi'}")
                except Exception as e:
                    print(e)
                    print(f"{error}{r} Akkaunt: {cy}{phone}{lg}{' -- '}{channel} ga qo`shilishda xatolik bo`ldi")
                    continue
            print(f'\n{lg} [~] User: {cy}{phone}{lg} kanallarga qo`shilishi tugadi')
            client.stop()
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def leave_channels():
    accounts = []
    with open('accs.txt', 'rb') as f:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            pass
    print(f'\n{lg} [i] Kanallardan chiqiladigan akkauntlarni tanlang')
    for i, account in enumerate(accounts):
        print(f"{lg}[{i}] {account['phone']}{n}")
    print(
        f'\n{lg}[+] Akkaunt tartib raqamlarini bosh joy tashlab kiriting. Barchasini tanlash uchun: -1\nMisol uchun: 0 1 5 12 {n}')
    indexes = list(map(int, input('> ').split()))
    if indexes == [(-1)]:
        indexes = list(range(len(accounts)))
    for i, account in enumerate(accounts):
        if i not in indexes:
            continue
        phone = str(account['phone'])
        try:
            client = Client(f'sessions/{phone}', api_id=API_ID, api_hash=API_HASH)
            client.start()
        except:
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- ulanishda xatolik bo`ldi')
            continue
        print(f'\n{lg} [~] Akkaunt: {cy}{phone}{lg} -- kanallardan chiqilmoqda...')
        for dialog in client.get_dialogs():
            if dialog.chat.type == ChatType.CHANNEL:
                try:
                    client.leave_chat(dialog.chat.id)
                except:
                    print(
                        f'{error}{r} Akkaunt: {cy}{phone}{lg} -- {dialog.chat.title} kanaldan chiqishda xatolik bo`ldi')
                    break
        client.stop()
        print(f'\n{lg} [~] User: {cy}{phone}{lg} kanallardan chiqib bo`ldi')
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def leave_specific_channels():
    accounts = []
    with open('accs.txt', 'rb') as f:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            pass
    print(f'\n{lg} [i] Kanallardan chiqiladigan akkauntlarni tanlang')
    for i, account in enumerate(accounts):
        print(f"{lg}[{i}] {account['phone']}{n}")
    print(
        f'\n{lg}[+] Akkaunt tartib raqamlarini bosh joy tashlab kiriting. Barchasini tanlash uchun: -1\nMisol uchun: 0 1 5 12 {n}')
    indexes = list(map(int, input('> ').split()))
    if indexes == [(-1)]:
        indexes = list(range(len(accounts)))
    channels_list = []
    channels_count = int(input(f'\n{lg}[+] Nechta kanallardan chiqmoqchisiz: {n}'))
    for i in range(channels_count):
        channel = input(f'\n{lg}[{i + 1}] Kanal ID raqamini yoki usernameni kiriting: {n}')
        if channel.isdigit():
            channel = int(channel)
        else:
            channel = '@' + channel.replace('@', '')
        channels_list.append(channel)
    for i, account in enumerate(accounts):
        if i not in indexes:
            continue
        phone = str(account['phone'])
        try:
            client = Client(f'sessions/{phone}', api_id=API_ID, api_hash=API_HASH)
            client.start()
        except:
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- ulanishda xatolik bo`ldi')
            print(f'\n{lg} [~] Akkaunt: {cy}{phone}{lg} -- kanallardan chiqilmoqda...')
            for channel in channels_list:
                try:
                    client.leave_chat(channel)
                except UserNotParticipant:
                    print(f"{error}{r} Akkaunt: {cy}{phone}{lg}{' -- '}{channel} kanalga a`zo emas!")
                    break
                else:
                    print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- {channel} kanaldan chiqishda xatolik bo`ldi')
            client.stop()
            print(f'\n{lg} [~] User: {cy}{phone}{lg} kanallardan chiqib bo`ldi')
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def start_bot():
    accounts = []
    with open('accs.txt', 'rb') as f:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            pass
    link = input(f'\n{lg} [+] Start bosish uchun bot linkini kiriting: {n}')
    pattern = '(https:\\/\\/)?t\\.me\\/([a-zA-Z0-9_]+)\\?start=([a-zA-Z0-9_]+)'
    pattern_2 = 'tg:\\/\\/resolve\\?domain=([a-zA-Z0-9_]+)&start=([a-zA-Z0-9_]+)'
    pattern_3 = '(https:\\/\\/)?telegram\\.me\\/([a-zA-Z0-9_]+)\\?start=([a-zA-Z0-9_]+)'
    pattern_4 = '(https:\\/\\/)?t\\.me\\/([a-zA-Z0-9_]+)'
    match = re.match(pattern, link)
    match_2 = re.match(pattern_2, link)
    match_3 = re.match(pattern_3, link)
    match_4 = re.match(pattern_4, link)
    if not match and (not match_2) and (not match_3) and (not match_4):
        print(f'{error} Bot linki noto`g`ri formatda!')
        input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')
        return
    bot_username = match.group(2) if match else match_2.group(1) if match_2 else match_3.group(
        2) if match_3 else match_4.group(2) if match_4 else None
    start_param = match.group(3) if match else match_2.group(2) if match_2 else match_3.group(3) if match_3 else ''
    for account in accounts:
        phone = str(account['phone'])
        try:
            client = Client(f'sessions/{phone}', api_id=API_ID, api_hash=API_HASH)
            client.start()
        except:
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- ulanishda xatolik bo`ldi')
            continue
        try:
            message = client.start_bot(bot_username, start_param)
            time.sleep(1)
            for message in client.get_chat_history(message.chat.id, limit=1):
                if message.reply_markup and type(
                        message.reply_markup) == InlineKeyboardMarkup and message.reply_markup.inline_keyboard:
                    keyboard = message.reply_markup.inline_keyboard
                    for row in keyboard:
                        for button in row:
                            if button.url:
                                link = button.url
                            else:
                                try:
                                    pattern = 'https:\\/\\/t\\.me\\/([a-zA-Z0-9_]+)'
                                    match = re.match(pattern, button.url)
                                    if match:
                                        link = match.group(1)
                                    client.join_chat(link)
                                except InviteRequestSent:
                                    print(
                                        f'{error}{r} Akkaunt: {cy}{phone}{lg} -- {button.url} kanalga qo`shilish uchun so`rov yuborildi')
                                except Exception as e:
                                    print(
                                        f'{error}{r} Akkaunt: {cy}{phone}{lg} -- {button.url} kanalga qo`shishda xatolik bo`ldi')
                                    continue
                        else:
                            try:
                                client.request_callback_answer(message.chat.id, message.id, button.callback_data)
                            except:
                                pass
        except Exception as e:
            print(e)
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- start bosishda xatolik bo`ldi')
        client.stop()
        print(f'\n{lg} [~] User: {cy}{phone}{lg} -- start bosildi')
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def reaction():
    accounts = []
    with open('accs.txt', 'rb') as f:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            pass
    link = input(f'\n{lg} [+] Post linkini kiriting: {n}')
    pattern = '(https:\\/\\/)?t\\.me\\/([a-zA-Z0-9_]+)\\/([0-9]+)'
    pattern_2 = '(https:\\/\\/)?telegram\\.me\\/([a-zA-Z0-9_]+)\\/([0-9]+)'
    pattern_3 = '(https:\\/\\/)?t\\.me\\/\\/c\\/([a-zA-Z0-9_]+)\\/([0-9]+)'
    pattern_4 = '(https:\\/\\/)?telegram\\.me\\/\\/c\\/([a-zA-Z0-9_]+)\\/([0-9]+)'
    match = re.match(pattern, link)
    match_2 = re.match(pattern_2, link)
    match_3 = re.match(pattern_3, link)
    match_4 = re.match(pattern_4, link)
    if not match and (not match_2) and (not match_3) and (not match_4):
        print(f'{error} Post linki noto`g`ri formatda!')
        input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')
        return
    id_or_username = match.group(2) if match else match_2.group(2) if match_2 else match_3.group(
        2) if match_3 else match_4.group(2) if match_4 else None
    message_id = int(
        match.group(3) if match else match_2.group(3) if match_2 else match_3.group(3) if match_3 else match_4.group(
            3) if match_4 else None)
    all_reactions = ['👍', '👎', '❤', '🔥', '🥰', '👏', '😁', '🤔', '🤯', '😱', '🤬', '😢', '🎉', '🤩', '🤮', '💩', '🙏', '👌', '🕊', '🤡',
                     '🥱', '🥴', '😍', '🐳', '❤‍🔥', '🌚', '🌭', '💯', '🤣', '⚡', '🍌', '🏆', '💔', '🤨', '😐', '🍓', '🍾', '💋', '🖕',
                     '😈', '😴', '😭', '🤓', '👻', '👨‍💻', '👀', '🎃', '🙈', '😇', '😨', '🤝', '✍', '🤗', '🫡', '🎅', '🎄', '☃', '💅',
                     '🤪', '🗿', '🆒', '💘', '🙉', '🦄', '😘', '💊', '🙊', '😎', '👾', '🤷‍♂', '🤷', '🤷‍♀', '😡']
    for i in range(0, len(all_reactions), 4):
        print()
        print(f'{i}, {all_reactions[i]}', end='')
        if i + 1 < len(all_reactions):
            print('   ', end='')
            print(f'{i + 1}, {all_reactions[i + 1]}', end='')
        if i + 2 < len(all_reactions):
            print('   ', end='')
            print(f'{i + 2}, {all_reactions[i + 2]}', end='')
        if i + 3 < len(all_reactions):
            print('   ', end='')
            print(f'{i + 3}, {all_reactions[i + 3]}{0}', end='')
    print(
        f'\n{lg} [i] Reaksiyalar tartib raqamlarini bosh joy tashlab kiriting. Barchasini tanlash uchun: -1\nMisol uchun: 0 1 5 12 {n}')
    reactions = list(map(int, input(f'\n{lg}[+] Reaksiyani tanlang: {n}').split()))
    if reactions == ['-1']:
        reactions = list(range(len(all_reactions)))
    for account in accounts:
        phone = str(account['phone'])
        try:
            client = Client(f'sessions/{phone}', api_id=API_ID, api_hash=API_HASH)
            client.start()
        except Exception as error:
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- ulanishda xatolik bo`ldi')
            try:
                client.send_reaction(chat_id=id_or_username, message_id=message_id,
                                     emoji=all_reactions[random.choice(reactions)])
            except Exception as error:
                print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- xatolik yuz berdi')
        client.stop()
        print(f'{lg} [~] Akkaunt: {cy}{phone}{lg} -- Reaksiya yuborildi')
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def get_code():
    accounts = []
    with open('accs.txt', 'rb') as f:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            pass
    for i, account in enumerate(accounts):
        print(f"{lg}[{i}] {account['phone']}{n}")
    index = int(input(f'\n{lg}[+] Akkauntni tanlang: {n}'))
    phone = str(accounts[index]['phone'])
    try:
        client = Client(f'sessions/{phone}', api_id=API_ID, api_hash=API_HASH)
        client.start()
    except:
        print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- ulanishda xatolik bo`ldi')
        input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')
        return None
    print(f"\n{lg} [~] User: {cy}phone{lg}{' -- Akkaunt tekshirilmoqda... '}{n}")
    for message in client.get_chat_history(777000, limit=1):
        if message.text:
            print(message.text)
        else:
            print(f'{error} Kod mavjud emas qaytadan urinib ko`ring')
    client.stop()
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def check_premium():
    accounts = []
    with open('accs.txt', 'rb') as f:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            pass
    print(f'\n{lg} [~] Premium yutgan akkauntlar tekshirilmoqda...')
    c = 0
    for account in accounts:
        phone = str(account['phone'])
        try:
            client = Client(f'sessions/{phone}', api_id=API_ID, api_hash=API_HASH)
            client.start()
        except:
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- ulanishda xatolik bo`ldi')
            continue
        print(f'\n{lg} [~] User: {cy}{phone}{lg} -- Akkaunt tekshirilmoqda...')
        for message in client.get_chat_history(777000, offset=account['last_msg_id']):
            if message.gift_code:
                if message.gift_code.via_giveaway:
                    print(f'{lg} [+] User: {cy}{phone}{lg: -- Premium yutgan}')
                    txt = f'[+] User: {phone} -- Premium yutdi\n\nLink: {message.gift_code.link}'
                    try:
                        client.send_message(GROUP_ID, txt)
                    except:
                        print(
                            f'{error}{r} User: {cy}{phone}{lg} -- Premium yutgan kanalga xabar yuborishda xatolik bo`ldi')
                    c += 1
            account['last_msg_id'] = max(account['last_msg_id'], message.id)
        client.stop()
    if c == 0:
        print(f'\n{r} Premium yutgan akkauntlar topilmadi')
    else:
        print(f'\n{lg} [+] Premium yutgan akkauntlar: {c}')
    with open('accs.txt', 'wb') as f:
        for account in accounts:
            pickle.dump(account, f)
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def start_konkurs():
    accounts = []
    with open('accs.txt', 'rb') as f:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            pass
    link = input(f'\n{lg} [+] Post linkini kiriting: {n}')
    pattern = '(https:\\/\\/)?t\\.me\\/([a-zA-Z0-9_]+)\\/([0-9]+)'
    pattern_2 = '(https:\\/\\/)?telegram\\.me\\/([a-zA-Z0-9_]+)\\/([0-9]+)'
    pattern_3 = '(https:\\/\\/)?t\\.me\\/\\/c\\/([a-zA-Z0-9_]+)\\/([0-9]+)'
    pattern_4 = '(https:\\/\\/)?telegram\\.me\\/\\/c\\/([a-zA-Z0-9_]+)\\/([0-9]+)'
    match = re.match(pattern, link)
    match_2 = re.match(pattern_2, link)
    match_3 = re.match(pattern_3, link)
    match_4 = re.match(pattern_4, link)
    if not match and (not match_2) and (not match_3) and (not match_4):
        print(f'{error} Post linki noto`g`ri formatda!')
        input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')
        return
    id_or_username = match.group(2) if match else match_2.group(2) if match_2 else match_3.group(
        2) if match_3 else match_4.group(2) if match_4 else None
    message_id = int(
        match.group(3) if match else match_2.group(3) if match_2 else match_3.group(3) if match_3 else match_4.group(
            3) if match_4 else None)
    for account in accounts:
        phone = str(account['phone'])
        try:
            client = Client(f'sessions/{phone}', api_id=API_ID, api_hash=API_HASH)
            client.start()
        except:
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- ulanishda xatolik bo`ldi')
            continue
        try:
            message = client.get_messages(id_or_username, message_id)
            res = message.click(0, 0)
            if type(res) == str:
                parsed_url = urlparse(res)
                bot_username = parsed_url.path.split('/')[1]
                platform = parsed_url.path.split('/')[2]
                start_param = parse_qs(parsed_url.query)['startapp'][0]
                peer = client.resolve_peer(id_or_username)
                bot_id = client.resolve_peer(bot_username)
                botapp = raw.types.InputBotAppShortName(bot_id=bot_id, short_name=platform)
                rww = client.invoke(raw.functions.messages.request_app_web_view.RequestAppWebView(peer=peer, app=botapp,
                                                                                                  start_param=start_param,
                                                                                                  platform=platform))
            else:
                try:
                    webbrowser.open(rww.url, new=2, autoraise=True)
                except:
                    print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- web saytida xatolik yuz berdi')
        except Exception as err:
            print(err)
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- xatolik yuz berdi')
        client.stop()
        print(f'{lg} [~] Akkaunt: {cy}{phone}{lg: -- Start bosdi}')
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


def clear_chat():
    accounts = []
    with open('accs.txt', 'rb') as f:
        try:
            accounts.append(pickle.load(f))
        except EOFError:
            pass
    print(f'\n{lg} [i] Chat ochiriladigan akkauntlarni tanlang')
    for i, account in enumerate(accounts):
        print(f"{lg}[{i}] {account['phone']}{n}")
    print(
        f'\n{lg}[+] Akkaunt tartib raqamlarini bosh joy tashlab kiriting. Barchasini tanlash uchun: -1\nMisol uchun: 0 1 5 12 {n}')
    indexes = list(map(int, input('> ').split()))
    if indexes == [(-1)]:
        indexes = list(range(len(accounts)))
    chat_list = []
    chats_count = int(input(f'\n{lg}[+] Nechta chat ochirmoqchisiz: {n}'))
    for i in range(chats_count):
        chat = input(f'\n{lg}[{i + 1}] Chat ID raqamini yoki usernameni kiriting: {n}')
        if chat.replace('-', '').isdigit():
            if int(chat):
                chat = int(chat)
        chat = '@' + chat.replace('@', '')
        chat_list.append(chat)
        continue
    for i, account in enumerate(accounts):
        if i not in indexes:
            continue
        phone = str(account['phone'])
        try:
            client = Client(f'sessions/{phone}', api_id=API_ID, api_hash=API_HASH)
            client.start()
        except:
            print(f'{error}{r} Akkaunt: {cy}{phone}{lg} -- ulanishda xatolik bo`ldi')
            print(f'\n{lg} [~] Akkaunt: {cy}{phone}{lg} -- kanallardan chiqilmoqda...')
            for chat in chat_list:
                try:
                    peer = client.resolve_peer(chat)
                    client.invoke(raw.functions.messages.DeleteHistory(peer=peer, max_id=0))
                except Exception as err:
                    print(err)
                    print(f'{error}{r} Akkaunt: {cy}{phone}{lg}{chat} -- xatolik yuz berdi')
            client.stop()
            print(f'\n{lg} [~] User: {cy}{phone}{lg} -- chat o`chirildi')
    input('\n Asosiy menyuga o`tish uchun Enter tugmasini bosing...')


while True:
    clear_screen()
    intro()
    print()
    print(f'{lg}[1] Yangi akkaunt qo`shish{n}')
    print(f'{lg}[2] Barcha banlangan akkauntlarni filtrlash{n}')
    print(f'{lg}[3] Akkauntni o`chirish{n}')
    print(f'{lg}[4] Barcha akkauntlarni ko`rsatish{n}')
    print(f'{lg}[5] Kanallarga qo`shilish{n}')
    print(f'{lg}[6] Barcha kanallardan chiqish{n}')
    print(f'{lg}[7] Tanlangan kanallardan chiqish{n}')
    print(f'{lg}[8] Start bot{n}')
    print(f'{lg}[9] Reaksiya bosish{n}')
    print(f'{lg}[10] Telegram kod olish{n}')
    print(f'{lg}[11] Premium yutganini tekshirish{n}')
    print(f'{lg}[12] Konkurs bot start{n}')
    print(f'{lg}[13] Chatni tozalash{n}')
    print(f'{lg}[14] Chiqish{n}')
    option = input('\nYuqoridagilardan birini tanlang: ')

    if option == '1':
        add_new_account()
    elif option == '2':
        filter_banned_accounts()
    elif option == '3':
        delete_account()
    elif option == '4':
        show_all_accounts()
    elif option == '5':
        join_channels()
    elif option == '6':
        leave_channels()
    elif option == '7':
        leave_specific_channels()
    elif option == '8':
        start_bot()
    elif option == '9':
        reaction()
    elif option == '10':
        get_code()
    elif option == '11':
        check_premium()
    elif option == '12':
        start_konkurs()
    elif option == '13':
        clear_chat()
    elif option == '14':
        clear_screen()
        break
