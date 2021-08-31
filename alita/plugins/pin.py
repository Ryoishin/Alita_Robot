# Copyright (C) 2020 - 2021 Divkix. All rights reserved. Source code available under the AGPL.
#
# This file is part of Ineruki_Robot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from html import escape as escape_html
from pyrogram.errors import ChatAdminRequired, RightForbidden, RPCError
from pyrogram.filters import regex
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import ikb

from ineruki import LOGGER, SUPPORT_GROUP
from ineruki.bot_class import Ineruki
from ineruki.database.pins_db import Pins
from ineruki.tr_engine import tlang
from ineruki.utils.custom_filters import admin_filter, command
from ineruki.utils.string import build_keyboard, parse_button


@Ineruki.on_message(command("pin") & admin_filter)
async def pin_message(_, m: Message):
    pin_args = m.text.split(None, 1)
    if m.reply_to_message:
        try:
            disable_notification = True

            if len(pin_args) >= 2 and pin_args[1] in ["alert", "notify", "loud"]:
                disable_notification = False

            await m.reply_to_message.pin(
                disable_notification=disable_notification,
            )
            LOGGER.info(
                f"{m.from_user.id} pinned msgid-{m.reply_to_message.message_id} in {m.chat.id}",
            )

            if m.chat.username:
                # If chat has a username, use this format
                link_chat_id = m.chat.username
                message_link = (
                    f"https://t.me/{link_chat_id}/{m.reply_to_message.message_id}"
                )
            elif (str(m.chat.id)).startswith("-100"):
                # If chat does not have a username, use this
                link_chat_id = (str(m.chat.id)).replace("-100", "")
                message_link = (
                    f"https://t.me/c/{link_chat_id}/{m.reply_to_message.message_id}"
                )
            await m.reply_text(
                tlang(m, "pin.pinned_msg").format(message_link=message_link),
                disable_web_page_preview=True,
            )

        except ChatAdminRequired:
            await m.reply_text(tlang(m, "admin.not_admin"))
        except RightForbidden:
            await m.reply_text(tlang(m, "pin.no_rights_pin"))
        except RPCError as ef:
            await m.reply_text(
                (tlang(m, "general.some_error")).format(
                    SUPPORT_GROUP=SUPPORT_GROUP,
                    ef=ef,
                ),
            )
            LOGGER.error(ef)
    else:
        await m.reply_text("Reply to a message to pin it!")

    return


@Ineruki.on_message(command("unpin") & admin_filter)
async def unpin_message(c: Ineruki, m: Message):
    try:
        if m.reply_to_message:
            await c.unpin_chat_message(m.chat.id, m.reply_to_message.message_id)
            LOGGER.info(
                f"{m.from_user.id} unpinned msgid: {m.reply_to_message.message_id} in {m.chat.id}",
            )
            await m.reply_text(tlang(m, "pin.unpinned_last_msg"))
        else:
            await c.unpin_chat_message(m.chat.id)
            await m.reply_text(tlang(m, "Unpinned last pinned message!"))
    except ChatAdminRequired:
        await m.reply_text(tlang(m, "admin.not_admin"))
    except RightForbidden:
        await m.reply_text(tlang(m, "pin.no_rights_unpin"))
    except RPCError as ef:
        await m.reply_text(
            (tlang(m, "general.some_error")).format(
                SUPPORT_GROUP=SUPPORT_GROUP,
                ef=ef,
            ),
        )
        LOGGER.error(ef)

    return


@Ineruki.on_message(command("unpinall") & admin_filter)
async def unpinall_message(_, m: Message):
    await m.reply_text(
        "Do you really want to unpin all messages in this chat?",
        reply_markup=ikb([[("Yes", "unpin_all_in_this_chat"), ("No", "close_admin")]]),
    )
    return


@Ineruki.on_callback_query(regex("^unpin_all_in_this_chat$"))
async def unpinall_calllback(c: Ineruki, q: CallbackQuery):
    user_id = q.from_user.id
    user_status = (await q.message.chat.get_member(user_id)).status
    if user_status not in {"creator", "administrator"}:
        await q.answer(
            "You're not even an admin, don't try this explosive shit!",
            show_alert=True,
        )
        return
    if user_status != "creator":
        await q.answer(
            "You're just an admin, not owner\nStay in your limits!",
            show_alert=True,
        )
        return
    try:
        await c.unpin_all_chat_messages(q.message.chat.id)
        LOGGER.info(f"{q.from_user.id} unpinned all messages in {q.message.chat.id}")
        await q.message.edit_text(tlang(q, "pin.unpinned_all_msg"))
    except ChatAdminRequired:
        await q.message.edit_text(tlang(q, "admin.notadmin"))
    except RightForbidden:
        await q.message.edit_text(tlang(q, "pin.no_rights_unpin"))
    except RPCError as ef:
        await q.message.edit_text(
            (tlang(q, "general.some_error")).format(
                SUPPORT_GROUP=SUPPORT_GROUP,
                ef=ef,
            ),
        )
        LOGGER.error(ef)
    return


@Ineruki.on_message(command("antichannelpin") & admin_filter)
async def anti_channel_pin(_, m: Message):
    pinsdb = Pins(m.chat.id)

    if len(m.text.split()) == 1:
        status = pinsdb.get_settings()["antichannelpin"]
        await m.reply_text(
            tlang(m, "pin.antichannelpin.current_status").format(
                status=status,
            ),
        )
        return

    if len(m.text.split()) == 2:
        if m.command[1] in ("yes", "on", "true"):
            pinsdb.antichannelpin_on()
            LOGGER.info(f"{m.from_user.id} enabled antichannelpin in {m.chat.id}")
            msg = tlang(m, "pin.antichannelpin.turned_on")
        elif m.command[1] in ("no", "off", "false"):
            pinsdb.antichannelpin_off()
            LOGGER.info(f"{m.from_user.id} disabled antichannelpin in {m.chat.id}")
            msg = tlang(m, "pin.antichannelpin.turned_off")
        else:
            await m.reply_text(tlang(m, "general.check_help"))
            return

    await m.reply_text(msg)
    return


@Ineruki.on_message(command("pinned") & admin_filter)
async def pinned_message(c: Ineruki, m: Message):
    chat_title = m.chat.title
    chat = await c.get_chat(chat_id=m.chat.id)
    msg_id = m.reply_to_message.message_id if m.reply_to_message else m.message_id

    if chat.pinned_message:
        pinned_id = chat.pinned_message.message_id
        if m.chat.username:
            link_chat_id = m.chat.username
            message_link = (f"https://t.me/{link_chat_id}/{pinned_id}")
        elif (str(m.chat.id)).startswith("-100"):
            link_chat_id = (str(m.chat.id)).replace("-100", "")
            message_link = (f"https://t.me/c/{link_chat_id}/{pinned_id}")
            
        await m.reply_text(f"The pinned message of {escape_html(chat_title)} is [here]({message_link}).", reply_to_message_id=msg_id, disable_web_page_preview=True,)
    else:
        await m.reply_text(f"There is no pinned message in {escape_html(chat_title)}.")


@Ineruki.on_message(command("cleanlinked") & admin_filter)
async def clean_linked(_, m: Message):
    pinsdb = Pins(m.chat.id)

    if len(m.text.split()) == 1:
        status = pinsdb.get_settings()["cleanlinked"]
        await m.reply_text(
            tlang(m, "pin.antichannelpin.current_status").format(
                status=status,
            ),
        )
        return

    if len(m.text.split()) == 2:
        if m.command[1] in ("yes", "on", "true"):
            pinsdb.cleanlinked_on()
            LOGGER.info(f"{m.from_user.id} enabled CleanLinked in {m.chat.id}")
            msg = "Turned on CleanLinked! Now all the messages from linked channel will be deleted!"
        elif m.command[1] in ("no", "off", "false"):
            pinsdb.cleanlinked_off()
            LOGGER.info(f"{m.from_user.id} disabled CleanLinked in {m.chat.id}")
            msg = "Turned off CleanLinked! Messages from linked channel will not be deleted!"
        else:
            await m.reply_text(tlang(m, "general.check_help"))
            return

    await m.reply_text(msg)
    return


@Ineruki.on_message(command("permapin") & admin_filter)
async def perma_pin(_, m: Message):
    if m.reply_to_message or len(m.text.split()) > 1:
        LOGGER.info(f"{m.from_user.id} used permampin in {m.chat.id}")
        if m.reply_to_message:
            text = m.reply_to_message.text
        elif len(m.text.split()) > 1:
            text = m.text.split(None, 1)[1]
        teks, button = await parse_button(text)
        button = await build_keyboard(button)
        button = ikb(button) if button else None
        z = await m.reply_text(teks, reply_markup=button)
        await z.pin()
    else:
        await m.reply_text("Reply to a message or enter text to pin it.")
    await m.delete()
    return


__PLUGIN__ = "pins"

__alt_name__ = ["pin", "unpin"]
