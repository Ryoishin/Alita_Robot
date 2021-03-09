from time import time

from pyrogram import filters
from pyrogram.errors import ChatAdminRequired, RPCError, UserAdminInvalid
from pyrogram.types import ChatPermissions, Message

from alita import LOGGER, MESSAGE_DUMP, SUPPORT_GROUP
from alita.bot_class import Alita
from alita.database.antispam_db import GBan
from alita.database.approve_db import Approve
from alita.database.blacklist_db import Blacklist
from alita.tr_engine import tlang
from alita.utils.parser import mention_html
from alita.utils.regex_utils import regex_searcher

# Initialise
bl_db = Blacklist()
app_db = Approve()
gban_db = GBan()


@Alita.on_message(filters.group, group=2)
async def aio_watcher(c: Alita, m: Message):
    if not m.from_user:
        return

    await gban_watcher(c, m)
    await bl_watcher(c, m)


async def gban_watcher(c: Alita, m: Message):
    try:
        try:
            _banned = gban_db.check_gban(m.from_user.id)
        except Exception as ef:
            LOGGER.error(ef)
            return
        if _banned:
            try:
                await m.chat.kick_member(m.from_user.id)
                await m.delete(m.message_id)  # Delete users message!
                await m.reply_text(
                    (tlang(m, "antispam.watcher_banned")).format(
                        user_gbanned=(
                            await mention_html(m.from_user.first_name, m.from_user.id)
                        ),
                        SUPPORT_GROUP=SUPPORT_GROUP,
                    ),
                )
                LOGGER.info(f"Banned user {m.from_user.id} in {m.chat.id}")
                return
            except (ChatAdminRequired, UserAdminInvalid):
                # Bot not admin in group and hence cannot ban users!
                # TO-DO - Improve Error Detection
                LOGGER.info(
                    f"User ({m.from_user.id}) is admin in group {m.chat.name} ({m.chat.id})",
                )
            except RPCError as ef:
                await c.send_message(
                    MESSAGE_DUMP,
                    f"<b>Gban Watcher Error!</b>\n<b>Chat:</b> {m.chat.id}\n<b>Error:</b> <code>{ef}</code>",
                )
    except AttributeError:
        pass  # Skip attribute errors!
    return


async def bl_watcher(_, m: Message):

    # TODO - Add warn option when Warn db is added!!
    async def perform_action_blacklist(m: Message, action: str):
        if action == "kick":
            (await m.chat.kick_member(m.from_user.id, int(time() + 45)))
            await m.reply_text(
                (
                    f"Kicked {m.from_user.username if m.from_user.username else m.from_user.first_name}"
                    " for using a blacklisted word!"
                ),
            )
        elif action == "ban":
            (
                await m.chat.kick_member(
                    m.from_user.id,
                )
            )
            await m.reply_text(
                (
                    f"Banned {m.from_user.username if m.from_user.username else m.from_user.first_name}"
                    " for using a blacklisted word!"
                ),
            )
        elif action == "mute":
            (
                await m.chat.restrict_member(
                    m.from_user.id,
                    ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_stickers=False,
                        can_send_animations=False,
                        can_send_games=False,
                        can_use_inline_bots=False,
                        can_add_web_page_previews=False,
                        can_send_polls=False,
                        can_change_info=False,
                        can_invite_users=True,
                        can_pin_messages=False,
                    ),
                )
            )
            await m.reply_text(
                (
                    f"Muted {m.from_user.username if m.from_user.username else m.from_user.first_name}"
                    " for using a blacklisted word!"
                ),
            )
        elif action == "none":
            return
        return

    # If no blacklists, then return
    chat_blacklists = bl_db.get_blacklists(m.chat.id)
    if not chat_blacklists:
        return

    # Get action for blacklist
    action = bl_db.get_action(m.chat.id)

    try:
        approved_users = []
        app_users = app_db.list_approved(m.chat.id)

        for i in app_users:
            approved_users.append(int(i["user_id"]))

        async for i in m.chat.iter_members(filter="administrators"):
            approved_users.append(i.user.id)

        # If user_id in approved_users list, return and don't delete the message
        if m.from_user.id in approved_users:
            return

        if m.text:
            for trigger in chat_blacklists:
                pattern = r"( |^|[^\w])" + trigger + r"( |$|[^\w])"
                match = await regex_searcher(pattern, m.text.lower())
                if not match:
                    continue
                if match:
                    try:
                        await perform_action_blacklist(m, action)
                        await m.delete()
                    except RPCError as ef:
                        LOGGER.info(ef)
                    break

    except AttributeError:
        pass  # Skip attribute errors!