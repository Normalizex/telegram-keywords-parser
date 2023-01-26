import os
import time
import asyncio
from bs4 import BeautifulSoup
from telethon import TelegramClient
from telethon.tl.types import PeerChannel

async def main():
    API_ID = os.getenv('API_ID') if os.getenv(
        'API_ID') is not None else input('[INPUT] Api ID =>')
    API_HASH = os.getenv('API_HASH') if os.getenv(
        'API_HASH') is not None else input('[INPUT] Api Hash =>')
    KEYWORDS = list(map(lambda x: x.lower(), os.getenv('KEYWORDS').split(',') if os.getenv(
        'KEYWORDS') is not None else input('[INPUT] Enter keywords (separated by spaces) =>').split(' ')))

    client = TelegramClient('./session/client', int(API_ID), API_HASH)
    await client.start()
    dialogs = await client.get_dialogs()

    # records limit to 1000 entries
    records = []
    recordsLimit = 1000

    filename = f'results/result-{round(time.time())}.html'
    soup = BeautifulSoup(open('template.html').read(), features="html.parser")
    with open(filename, "w") as outf:
        outf.write(str(soup))

    def new_record(
        userId,#number|string
        username,#string
        time,#string
        is_bot,#boolean
        messageId,#number
        channelType,#string (user|group|channe;)
        channelId,#number|string
        keyword#string
    ):
        tr = soup.new_tag('tr')

        #id
        th_userid = soup.new_tag('th', scope='row')
        th_userid.string = str(userId)
        tr.append(th_userid)
        
        #username
        td_username = soup.new_tag('td')
        td_a = soup.new_tag('a', href=f"http://t.me/{username}", target="_blank", rel="noopener noreferrer")
        td_a.string = username
        td_username.append(td_a)
        tr.append(td_username)

        #time
        th_isbot = soup.new_tag('td')
        th_isbot.string = str(time)
        tr.append(th_isbot)


        #is_bot
        th_isbot = soup.new_tag('td')
        th_isbot.string = str(is_bot)
        tr.append(th_isbot)

        #messageId
        th_messageid = soup.new_tag('td')
        th_messageid.string = str(messageId)
        tr.append(th_messageid)

        #channelType
        th_channelType = soup.new_tag('td')
        th_channelType.string = str(channelType)
        tr.append(th_channelType)

        #channelId
        th_channelId = soup.new_tag('td')
        th_channelId.string = str(channelId)
        tr.append(th_channelId)

        #keyword
        th_keyword = soup.new_tag('td')
        th_keyword.string = str(keyword)
        tr.append(th_keyword)

        #records count
        soup.find(id="records").string = f'{int(soup.find(id="records").string) + 1}'
        #add new record
        soup.find(id="resultlist").append(tr)

        with open(filename, "w") as outf:
            outf.write(str(soup))

    print(f'[INFO] Total channels: {dialogs.total} | All records will be written to a file: {filename}')
    for dialogIndex in range(0, len(dialogs)):
        dialog = dialogs[dialogIndex]
        if len(records) >= recordsLimit:
            break

        if dialog.is_user:
            print(f'[INFO] [{dialogIndex + 1} of {len(dialogs)}] | [USER]: {dialog.entity.id} (http://t.me/{dialog.entity.username}) | Records: {len(records)} | OutFile: {filename}')
            
            finded = False
            async for msg in client.iter_messages(dialog.entity.id):
                if len(records) >= recordsLimit:
                    break

                if not msg.message or dialog.entity.id in records:
                    continue

                for word in msg.message.split(' '):
                    if word.lower() not in KEYWORDS:
                        continue

                    finded = True

                    new_record(
                        dialog.entity.id,
                        dialog.entity.username,
                        msg.date.strftime("%m/%d/%Y, %H:%M:%S"),
                        dialog.entity.bot,
                        msg.id,
                        "user",
                        dialog.entity.id,
                        word
                    )
                    records.append(dialog.entity.id)

                    break

                #In the dm channel, you just need to find one stop word, since this is one user.
                if finded:
                    break

        elif dialog.is_group:
            print(f'[INFO] [{dialogIndex + 1} of {len(dialogs)}] | [GROUP]: {dialog.entity.title} | Records: {len(records)} | OutFile: {filename}')
            async for msg in client.iter_messages(dialog.entity.id):
                if len(records) >= recordsLimit:
                    break

                if not msg.from_id:
                    continue

                user_id = msg.from_id.channel_id if isinstance(msg.from_id, PeerChannel) else msg.from_id.user_id
                if not msg.message or user_id in records:
                    continue

                for word in msg.message.split(' '):
                    if word.lower() not in KEYWORDS:
                        continue

                    user_data = await client.get_entity(user_id)
                    if not user_data.username:
                        break

                    new_record(
                        user_id,
                        user_data.username,
                        msg.date.strftime("%m/%d/%Y, %H:%M:%S"),
                        False if isinstance(msg.from_id, PeerChannel) else user_data.bot,
                        msg.id,
                        "group",
                        dialog.entity.id,
                        word
                    )
                    records.append(user_id)

                    print(f'[INFO] [{dialogIndex + 1} of {len(dialogs)}] | [GROUP]: {dialog.entity.title} | Records: {len(records)} | OutFile: {filename}')
                    break

        elif dialog.is_channel:
            async for msg in client.iter_messages(dialog.entity.id):
                if len(records) >= recordsLimit:
                    break

                if not msg.message or not msg.from_id:
                    continue

                user_id = msg.from_id.channel_id if isinstance(msg.from_id, PeerChannel) else msg.from_id.user_id
                if user_id in records:
                    continue

                for word in msg.message.split(' '):
                    if word.lower() not in KEYWORDS:
                        continue

                    user_data = await client.get_entity(user_id)
                    if not user_data.username:
                        break

                    new_record(
                        user_id,
                        user_data.username,
                        msg.date.strftime("%m/%d/%Y, %H:%M:%S"),
                        False if isinstance(msg.from_id, PeerChannel) else user_data.bot,
                        msg.id,
                        "channel",
                        dialog.entity.id,
                        word
                    )
                    records.append(user_id)
                    print(f'[INFO] [{dialogIndex + 1} of {len(dialogs)}] | [CHANNEL]: {dialog.entity.title} | Records: {len(records)} | OutFile: {filename}')
                    break
    
    print(f'[RESULT] Saved as: {filename}')



if __name__ == '__main__':
    asyncio.run(main())
