print("Initializing...")

from os import unlink
from random import randint
from pyrogram import Client
from pyrogram.types import Message
import asyncio
import aiohttp
from yarl import URL
import re

from conf import *
from draft_to_calendar import send_calendar


async def get_token(base_url: URL, user: str, passw: str):
    query: dict = {
        "service": "moodle_mobile_app",
        "username": darmartinez,
        "password": dar1079dar*,
    }
    token_url: URL = base_url.with_path("login/token.php").with_query(query)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(token_url) as response:
                result = await response.json()
                return result["token"]
    except:
        return False


def sign_url(token: str, url: URL):
    query: dict = dict(url.query)
    query["token"] = token
    path = "webservice" + url.path
    return url.with_path(path).with_query(query)


async def shorten_url(url: URL):
    query = {"url": str(url)}
    base = URL("https://da.gd/shorten/")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base.with_query(query)) as response:
                return URL(await response.text())
    except:
        return False


# url_list = {
#     101010101: {
#         "http://adasdad": ["user", "pass", "token"],
#         "urls": ["url1", "url2", "url3"],
#     },
# }
url_list = {}
bot = Client("bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@bot.on_message()
async def message_handler(client: Client, message: Message):
    uid: int = message.from_user.id
    msg: str = message.text   
    verdad = True

    if msg.lower() == "/start":
        await message.reply("Bienvenidos {}".format(message.from_user.first_name))
        return

    # Comprobar que el usuario esté en el grupo o está autorizado
    if not url_list.get(uid):
        group_members = client.get_chat_members(bot_admin_group)
        auth = False
        async for member in group_members:
            if uid == member.user.id:
                auth = True
                url_list[uid] = {"urls": []}
        if auth == False:
            return

    # Autenticación
    if msg.lower().startswith("/setauth"):
        progress_message = await message.reply(
            "⏳Autenticando⏳")
        auth: list = msg.split(" ")
        print(auth)
        if len(auth) != 5:
            await progress_message.edit(
                "❌La forma correcta es: /setauth https://moodle.uclv.edu.cu/ Usuario Contraseña\n\n"
            )
            return
        url = URL(auth[1]).origin()
        user = auth[2]
        passw = auth[3]
        enlac = auth[4]
        token = await get_token(url, user, passw)
        if token:
            url_list[uid][str(url).lower()] = [user, passw, token, enlac]
            await progress_message.edit("✅Configuración completada✅")
        else:
            if not token:
                await progress_message.edit(
                    "❌Error al obtener token con las credenciales actuales❌"
                )
        return
    # Firmar enlaces
    if re.search("https?://[^\s]+[a-zA-z0-9]", msg, re.IGNORECASE):
        urls = re.findall("https?://[^\s]+[a-zA-z0-9]", msg, re.IGNORECASE)
        progress_message = await message.reply(
            "⏳ Firmando {} links...".format(len(urls)))

        base_url = URL(urls[0]).origin()
        auth = url_list[uid].get(str(base_url).lower())
        if auth:
            user = auth[0]
            passw = auth[1]
            token = auth[2]
            enlac = auth[3]
        else:
            await message.reply(
                "❌ No se encuentra autenticación para " + str(base_url)
            )
            return
        counter = 0

        if str(urls[0]).__contains__("/draftfile.php/"):
            await progress_message.edit("⏳Moviendo draft a calenario⏳")
            urls = await send_calendar(str(base_url), user, passw, urls)
            await progress_message.edit("⏳Firmando {} links⏳".format(len(urls)))

        for url in urls:
            url_signed = sign_url(token, URL(url))
            url_short = await shorten_url(url_signed)
            if enlac=='cortos':
                url_list[uid]["urls"].append(str(url_short))
            elif enlac=='normal':
                url_list[uid]["urls"].append(str(url_signed))
            counter += 1
        
        if url_list[uid]["urls"] == []:
            await message.reply(
                "❌No hay ningún link firmado❌"
            )
        else:
            links = "\n".join(url_list[uid]["urls"])
            fname = str(randint(100000000, 9999999999)) + ".txt"
            with open(fname, "w") as f:
                f.write(links)
            try:
                await progress_message.edit(links)
            except:
                pass
            await message.reply_document(fname)
            url_list[uid]["urls"] = []
            unlink(fname)
        #await progress_message.edit(
        #    "✅ Firmados {}/{} links. Puede usar /txt para generar el .txt".format(
        #        counter, len(urls)
        #    )
        #)
        return

    # Generar TXT
    if msg == "/txt":
        if url_list[uid]["urls"] == []:
            await message.reply(
                "❌No hay ningún link firmado❌"
            )
        else:
            links = "\n".join(url_list[uid]["urls"])
            fname = str(randint(100000000, 9999999999)) + ".txt"
            with open(fname, "w") as f:
                f.write(links)
            try:
                await message.reply(links)
            except:
                pass
            await message.reply_document(fname)
            url_list[uid]["urls"] = []
            unlink(fname)


print("Starting...")
bot.start()
print("Ready.")
bot.send_message(bot_admin_group, "✅Bot reiniciado✅")
loop: asyncio.AbstractEventLoop = asyncio.get_event_loop_policy().get_event_loop()
loop.run_forever()
