"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import re
import urllib
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError

import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from NekoRobot import NEKO_PTB
from NekoRobot.modules.disable import DisableAbleCommandHandler

opener = urllib.request.build_opener()
useragent = "Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36"
opener.addheaders = [("User-agent", useragent)]


def reverse(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    chat_id = update.effective_chat.id
    rtmid = msg.message_id
    imagename = "googlereverse.png"

    if os.path.isfile(imagename):
        os.remove(imagename)

    if reply := msg.reply_to_message:
        if reply.sticker:
            file_id = reply.sticker.file_id
        elif reply.photo:
            file_id = reply.photo[-1].file_id
        elif reply.document:
            file_id = reply.document.file_id
        else:
            msg.reply_text("Reply To An Image Or Sticker To Lookup!")
            return

        image_file = context.bot.get_file(file_id)
        image_file.download(imagename)
    else:
        msg.reply_text(
            "Please Reply To A Sticker, Or An Image To Search It!",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    MsG = context.bot.send_message(
        chat_id,
        "Let Me See...",
        reply_to_message_id=rtmid,
    )
    try:
        searchUrl = "https://www.google.com/searchbyimage/upload"
        multipart = {
            "encoded_image": (imagename, open(imagename, "rb")),
            "image_content": "",
        }
        response = requests.post(searchUrl,
                                 files=multipart,
                                 allow_redirects=False)
        fetchUrl = response.headers.get("Location")

        os.remove(imagename)
        if response != 400:
            MsG.edit_text("Downloading...")
        else:
            MsG.edit_text("Google Told Me To Go Away...")
            return

        match = ParseSauce(f"{fetchUrl}&hl=en")
        guess = match.get("best_guess")
        MsG.edit_text("Uploading...")
        if match.get("override") and (match.get("override") != ""
                                      or match.get("override") is not None):
            imgspage = match.get("override")
        else:
            imgspage = match.get("similar_images")

        buttuns = []
        if guess:
            MsG.edit_text("Hmmm....")
            search_result = guess.replace("Possible related search: ", "")
            buttuns.append(
                [InlineKeyboardButton(text="Images Link", url=fetchUrl)])
        else:
            MsG.edit_text("Couldn't Find Anything!")
            return

        if imgspage:
            buttuns.append(
                [InlineKeyboardButton(text="Similar Images", url=imgspage)])

        MsG.edit_text(
            f"*Search Results*: \n\n`{search_result}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttuns),
        )

    except BadRequest as Bdr:
        MsG.edit_text(
            f"ERROR! - _Couldn't Find Anything!!_ \n\n*Reason*: BadRequest!\n\n{Bdr}",
            parse_mode=ParseMode.MARKDOWN)
    except TelegramError as Tge:
        MsG.edit_text(
            f"ERROR! - _Couldn't Find Anything!!_ \n\n*Reason*: TelegramError!\n\n{Tge}",
            parse_mode=ParseMode.MARKDOWN)
    except Exception as Exp:
        MsG.edit_text(
            f"ERROR! - _Couldn't Find Anything!!_ \n\n*Reason*: Exception!\n\n{Exp}",
            parse_mode=ParseMode.MARKDOWN)


def ParseSauce(googleurl):
    source = opener.open(googleurl).read()
    soup = BeautifulSoup(source, "html.parser")

    results = {"similar_images": "", "override": "", "best_guess": ""}

    try:
        for bess in soup.findAll("a", {"class": "PBorbe"}):
            url = "https://www.google.com" + bess.get("href")
            results["override"] = url
    except:
        pass

    for similar_image in soup.findAll("input", {"class": "gLFyf"}):
        url = "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote_plus(
            similar_image.get("value"))
        results["similar_images"] = url

    for best_guess in soup.findAll("div", attrs={"class": "r5a77d"}):
        results["best_guess"] = best_guess.get_text()

    return results


def scam(imgspage, lim):
    """Parse/Scrape the HTML code for the info we want."""

    single = opener.open(imgspage).read()
    decoded = single.decode("utf-8")
    if int(lim) > 10:
        lim = 10

    imglinks = []
    counter = 0

    pattern = r"^,\[\"(.*[.png|.jpg|.jpeg])\",[0-9]+,[0-9]+\]$"
    oboi = re.findall(pattern, decoded, re.I | re.M)

    for imglink in oboi:
        counter += 1
        imglinks.append(imglink)
        if counter >= int(lim):
            break

    return imglinks


REVERSE_HANDLER = DisableAbleCommandHandler(
    ["grs", "reverse", "pp"], reverse)


NEKO_PTB.add_handler(REVERSE_HANDLER)

__mod_name__ = "Reverse"
