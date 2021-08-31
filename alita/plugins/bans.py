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
from traceback import format_exc

from pyrogram.errors import (
    ChatAdminRequired,
    PeerIdInvalid,
    RightForbidden,
    RPCError,
    UserAdminInvalid,
)
from pyrogram.types import Message

from alita import LOGGER, SUPPORT_GROUP, SUPPORT_STAFF, BOT_ID
from alita.bot_class import Ineruki
from alita.tr_engine import tlang
from alita.utils.caching import ADMIN_CACHE, admin_cache_reload
from alita.utils.custom_filters import command, restrict_filter
from alita.utils.extract_user import extract_user
from alita.utils.string import extract_time
from alita.utils.parser import mention_html


@Ineruki.on_message(
    command(["tban", "stban", "dtban"]) & restrict_filter,
)
async def tban_usr(c: Ineruki, m: Message):
    if len(m.text.split()) == 1 and not m.reply_to_message:
        await m.reply_text(tlang(m, "admin.ban.no_target"))
        await m.stop_propagation()

    user_id, user_first_name, _ = await extract_user(c, m)
        
    if not user_id:
        await m.reply_text("Cannot find user to ban")
        return
    if user_id == BOT_ID:
        await m.reply_text("Huh, why would I ban myself?")
        await m.stop_propagation()

    if user_id in SUPPORT_STAFF:
        await m.reply_text(tlang(m, "admin.support_cannot_restrict"))
        LOGGER.info(
            f"{m.from_user.id} trying to ban {user_id} (SUPPORT_STAFF) in {m.chat.id}",
        )
        await m.stop_propagation()

    if m.reply_to_message:
        r_id = m.reply_to_message.message_id
    else:
        r_id = m.message_id
        
    if m.reply_to_message and len(m.text.split()) < 2:
        reason = m.text.split(None, 2)[2]
    elif not m.reply_to_message and len(m.text.split()) < 3:
        reason = m.text.split(None, 2)[2]
    else:
        m.reply_text("Read /help !!")
        return
    
    if not reason:
        await m.reply_text("You haven't specified a time to ban this user for!")
        return

    split_reason = reason.split(None, 1)
    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = await extract_time(m, time_val)

    if not bantime:
        return

    try:
        admins_group = {i[0] for i in ADMIN_CACHE[m.chat.id]}
    except KeyError:
        admins_group = await admin_cache_reload(m, "ban")

    if user_id in admins_group:
        await m.reply_text(tlang(m, "admin.ban.admin_cannot_ban"))
        await m.stop_propagation()

    try:
        LOGGER.info(f"{m.from_user.id} tbanned {user_id} in {m.chat.id}")
        await m.chat.kick_member(user_id, until_date=int(bantime))
        if m.text.split()[0] == "/stban":
            await m.delete()
            if m.reply_to_message:
                await m.reply_to_message.delete()
            await m.stop_propagation()
        if m.text.split()[0] == "/dtban":
            if not m.reply_to_message:
                await m.reply_text("Reply to a message to delete it and tban the user!")
                await m.stop_propagation()
            await m.reply_to_message.delete()
        txt = (tlang(m, "admin.ban.banned_user")).format(
            admin=(await mention_html(m.from_user.first_name, m.from_user.id)),
            banned=(await mention_html(user_first_name, user_id)),
            chat_title=m.chat.title,
        )
        txt += f"\n<b>Reason</b>: {reason}" if reason else ""
        await m.reply_text(txt, reply_to_message_id=r_id)
    except ChatAdminRequired:
        await m.reply_text(tlang(m, "admin.not_admin"))
    except PeerIdInvalid:
        await m.reply_text(
            "I have not seen this user yet...!\nMind forwarding one of their message so I can recognize them?",
        )
    except UserAdminInvalid:
        await m.reply_text(tlang(m, "admin.user_admin_invalid"))
    except RightForbidden:
        await m.reply_text(tlang(m, tlang(m, "admin.ban.bot_no_right")))
    except RPCError as ef:
        await m.reply_text(
            (tlang(m, "general.some_error")).format(
                SUPPORT_GROUP=SUPPORT_GROUP,
                ef=ef,
            ),
        )
        LOGGER.error(ef)
        LOGGER.error(format_exc())
    await m.stop_propagation()


@Ineruki.on_message(
    command(["kick", "skick", "dkick"]) & restrict_filter,
)
async def kick_usr(c: Ineruki, m: Message):
    if len(m.text.split()) == 1 and not m.reply_to_message:
        await m.reply_text(tlang(m, "admin.kick.no_target"))
        await m.stop_propagation()

    reason = None
    if m.reply_to_message:
        r_id = m.reply_to_message.message_id
        if len(m.text.split()) >= 2:
            reason = m.text.split(None, 1)[1]
    else:
        r_id = m.message_id
        if len(m.text.split()) >= 3:
            reason = m.text.split(None, 2)[2]
    user_id, user_first_name, _ = await extract_user(c, m)

    if not user_id:
        await m.reply_text("Cannot find user to kick")
        return

    if user_id == BOT_ID:
        await m.reply_text("Huh, why would I kick myself?")
        await m.stop_propagation()

    if user_id in SUPPORT_STAFF:
        await m.reply_text(tlang(m, "admin.support_cannot_restrict"))
        LOGGER.info(
            f"{m.from_user.id} trying to kick {user_id} (SUPPORT_STAFF) in {m.chat.id}",
        )
        await m.stop_propagation()

    try:
        admins_group = {i[0] for i in ADMIN_CACHE[m.chat.id]}
    except KeyError:
        admins_group = await admin_cache_reload(m, "kick")

    if user_id in admins_group:
        await m.reply_text(tlang(m, "admin.kick.admin_cannot_kick"))
        await m.stop_propagation()

    try:
        LOGGER.info(f"{m.from_user.id} kicked {user_id} in {m.chat.id}")
        await m.chat.kick_member(user_id)
        if m.text.split()[0] == "/skick":
            await m.delete()
            if m.reply_to_message:
                await m.reply_to_message.delete()
            await m.stop_propagation()
        if m.text.split()[0] == "/dkick":
            if not m.reply_to_message:
                await m.reply_text("Reply to a message to delete it and kick the user!")
                await m.stop_propagation()
            await m.reply_to_message.delete()
        txt = (tlang(m, "admin.kick.kicked_user")).format(
            admin=(await mention_html(m.from_user.first_name, m.from_user.id)),
            kicked=(await mention_html(user_first_name, user_id)),
            chat_title=m.chat.title,
        )
        txt += f"\n<b>Reason</b>: {reason}" if reason else ""
        await m.reply_text(txt, reply_to_message_id=r_id)
        await m.chat.unban_member(user_id)
    except ChatAdminRequired:
        await m.reply_text(tlang(m, "admin.not_admin"))
    except PeerIdInvalid:
        await m.reply_text(
            "I have not seen this user yet...!\nMind forwarding one of their message so I can recognize them?",
        )
    except UserAdminInvalid:
        await m.reply_text(tlang(m, "admin.user_admin_invalid"))
    except RightForbidden:
        await m.reply_text(tlang(m, "admin.kick.bot_no_right"))
    except RPCError as ef:
        await m.reply_text(
            (tlang(m, "general.some_error")).format(
                SUPPORT_GROUP=SUPPORT_GROUP,
                ef=ef,
            ),
        )
        LOGGER.error(ef)
        LOGGER.error(format_exc())

    await m.stop_propagation()


@Ineruki.on_message(
    command(["ban", "sban", "dban"]) & restrict_filter,
)
async def ban_usr(c: Ineruki, m: Message):
    if len(m.text.split()) == 1 and not m.reply_to_message:
        await m.reply_text(tlang(m, "admin.ban.no_target"))
        await m.stop_propagation()

    reason = None
    if m.reply_to_message:
        r_id = m.reply_to_message.message_id
        if len(m.text.split()) >= 2:
            reason = m.text.split(None, 1)[1]
    else:
        r_id = m.message_id
        if len(m.text.split()) >= 3:
            reason = m.text.split(None, 2)[2]
    user_id, user_first_name, _ = await extract_user(c, m)

    if not user_id:
        await m.reply_text("Cannot find user to ban")
        return
    if user_id == BOT_ID:
        await m.reply_text("Huh, why would I ban myself?")
        await m.stop_propagation()

    if user_id in SUPPORT_STAFF:
        await m.reply_text(tlang(m, "admin.support_cannot_restrict"))
        LOGGER.info(
            f"{m.from_user.id} trying to ban {user_id} (SUPPORT_STAFF) in {m.chat.id}",
        )
        await m.stop_propagation()

    try:
        admins_group = {i[0] for i in ADMIN_CACHE[m.chat.id]}
    except KeyError:
        admins_group = await admin_cache_reload(m, "ban")

    if user_id in admins_group:
        await m.reply_text(tlang(m, "admin.ban.admin_cannot_ban"))
        await m.stop_propagation()

    try:
        LOGGER.info(f"{m.from_user.id} banned {user_id} in {m.chat.id}")
        await m.chat.kick_member(user_id)
        if m.text.split()[0] == "/sban":
            await m.delete()
            if m.reply_to_message:
                await m.reply_to_message.delete()
            await m.stop_propagation()
        if m.text.split()[0] == "/dban":
            if not m.reply_to_message:
                await m.reply_text("Reply to a message to delete it and ban the user!")
                await m.stop_propagation()
            await m.reply_to_message.delete()
        txt = (tlang(m, "admin.ban.banned_user")).format(
            admin=(await mention_html(m.from_user.first_name, m.from_user.id)),
            banned=(await mention_html(user_first_name, user_id)),
            chat_title=m.chat.title,
        )
        txt += f"\n<b>Reason</b>: {reason}" if reason else ""
        await m.reply_text(txt, reply_to_message_id=r_id)
    except ChatAdminRequired:
        await m.reply_text(tlang(m, "admin.not_admin"))
    except PeerIdInvalid:
        await m.reply_text(
            "I have not seen this user yet...!\nMind forwarding one of their message so I can recognize them?",
        )
    except UserAdminInvalid:
        await m.reply_text(tlang(m, "admin.user_admin_invalid"))
    except RightForbidden:
        await m.reply_text(tlang(m, tlang(m, "admin.ban.bot_no_right")))
    except RPCError as ef:
        await m.reply_text(
            (tlang(m, "general.some_error")).format(
                SUPPORT_GROUP=SUPPORT_GROUP,
                ef=ef,
            ),
        )
        LOGGER.error(ef)
        LOGGER.error(format_exc())
    await m.stop_propagation()


@Ineruki.on_message(command("unban") & restrict_filter)
async def unban_usr(c: Ineruki, m: Message):
    if len(m.text.split()) == 1 and not m.reply_to_message:
        await m.reply_text(tlang(m, "admin.unban.no_target"))
        await m.stop_propagation()

    user_id, user_first_name, _ = await extract_user(c, m)

    if m.reply_to_message and len(m.text.split()) >= 2:
        reason = m.text.split(None, 1)[1]
    elif not m.reply_to_message and len(m.text.split()) >= 3:
        reason = m.text.split(None, 2)[2]
    else:
        reason = None

    try:
        await m.chat.unban_member(user_id)
        txt = (tlang(m, "admin.unban.unbanned_user")).format(
            admin=(await mention_html(m.from_user.first_name, m.from_user.id)),
            unbanned=(await mention_html(user_first_name, user_id)),
            chat_title=m.chat.title,
        )
        txt += f"\n<b>Reason</b>: {reason}" if reason else ""
        await m.reply_text(txt)
    except ChatAdminRequired:
        await m.reply_text(tlang(m, "admin.not_admin"))
    except RightForbidden:
        await m.reply_text(tlang(m, tlang(m, "admin.unban.bot_no_right")))
    except RPCError as ef:
        await m.reply_text(
            (tlang(m, "general.some_error")).format(
                SUPPORT_GROUP=SUPPORT_GROUP,
                ef=ef,
            ),
        )
        LOGGER.error(ef)
        LOGGER.error(format_exc())

    await m.stop_propagation()


__PLUGIN__ = "bans"

__alt_name__ = ["ban", "unban", "kick", "tban", ]
