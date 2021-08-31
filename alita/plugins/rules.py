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


from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import ikb

from ineruki import LOGGER
from ineruki.bot_class import Ineruki
from ineruki.database.rules_db import Rules
from ineruki.tr_engine import tlang
from ineruki.utils.custom_filters import admin_filter, command


@Ineruki.on_message(command("rules") & filters.group)
async def get_rules(_, m: Message):
    db = Rules(m.chat.id)
    msg_id = m.reply_to_message.message_id if m.reply_to_message else m.message_id

    rules = db.get_rules()
    LOGGER.info(f"{m.from_user.id} fetched rules in {m.chat.id}")

    if not rules:
        await m.reply_text(
            (tlang(m, "rules.no_rules")),
            quote=True,
        )
        return

    priv_rules_status = db.get_privrules()

    if priv_rules_status:
        from ineruki import BOT_USERNAME

        pm_kb = ikb(
            [
                [
                    (
                        "Rules",
                        f"https://t.me/{BOT_USERNAME}?start=rules_{m.chat.id}",
                        "url",
                    ),
                ],
            ],
        )
        await m.reply_text(
            (tlang(m, "rules.pm_me")),
            quote=True,
            reply_markup=pm_kb,
            reply_to_message_id=msg_id,
        )
        return

    await m.reply_text(
        (tlang(m, "rules.get_rules")).format(
            chat=m.chat.title,
            rules=rules,
        ),
        disable_web_page_preview=True,
        reply_to_message_id=msg_id,
    )
    return


@Ineruki.on_message(command("setrules") & admin_filter)
async def set_rules(_, m: Message):
    db = Rules(m.chat.id)
    if m.reply_to_message and m.reply_to_message.text:
        rules = m.reply_to_message.text
    elif (not m.reply_to_message) and len(m.text.split()) >= 2:
        rules = m.text.split(None, 1)[1]

    if len(rules) > 4000:
        rules = rules[0:3949]  # Split Rules if len > 4000 chars
        await m.reply_text("Rules truncated to 3950 characters!")

    db.set_rules(rules)
    LOGGER.info(f"{m.from_user.id} set rules in {m.chat.id}")
    await m.reply_text(tlang(m, "rules.set_rules"))
    return


@Ineruki.on_message(
    command(["privrules", "privaterules"]) & admin_filter,
)
async def priv_rules(_, m: Message):
    db = Rules(m.chat.id)
    if len(m.text.split()) == 2:
        option = (m.text.split())[1]
        if option in ("on", "yes"):
            db.set_privrules(True)
            LOGGER.info(f"{m.from_user.id} enabled privaterules in {m.chat.id}")
            msg = tlang(m, "rules.priv_rules.turned_on").format(chat_name=m.chat.title)
        elif option in ("off", "no"):
            db.set_privrules(False)
            LOGGER.info(f"{m.from_user.id} disbaled privaterules in {m.chat.id}")
            msg = tlang(m, "rules.priv_rules.turned_off").format(chat_name=m.chat.title)
        else:
            msg = tlang(m, "rules.priv_rules.no_option")
        await m.reply_text(msg)
    elif len(m.text.split()) == 1:
        curr_pref = db.get_privrules()
        msg = tlang(m, "rules.priv_rules.current_preference").format(
            current_option=curr_pref,
        )
        LOGGER.info(f"{m.from_user.id} fetched privaterules preference in {m.chat.id}")
        await m.reply_text(msg)
    else:
        await m.replt_text(tlang(m, "general.check_help"))

    return


@Ineruki.on_message(command("clearrules") & admin_filter)
async def clear_rules(_, m: Message):
    db = Rules(m.chat.id)

    rules = db.get_rules()
    if not rules:
        await m.reply_text(tlang(m, "rules.no_rules"))
        return

    await m.reply_text(
        (tlang(m, "rules.clear_rules")),
        reply_markup=ikb(
            [[("⚠️ Confirm", "clear_rules"), ("❌ Cancel", "close_admin")]],
        ),
    )
    return


@Ineruki.on_callback_query(filters.regex("^clear_rules$"))
async def clearrules_callback(_, q: CallbackQuery):
    Rules(q.message.chat.id).clear_rules()
    await q.message.edit_text(tlang(q, "rules.cleared"))
    LOGGER.info(f"{q.from_user.id} cleared rules in {q.message.chat.id}")
    await q.answer("Rules for the chat have been cleared!", show_alert=True)
    return


__PLUGIN__ = "rules"

__alt_name__ = ["rule"]
