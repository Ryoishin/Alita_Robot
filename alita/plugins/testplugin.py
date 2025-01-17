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


from pyrogram.types import Message
from time import time

from ineruki.bot_class import Ineruki
from ineruki.utils.custom_filters import command


@Ineruki.on_message(command("test", sudo_cmd=True))
async def test_bot(_, m: Message):
    start = time()
    replymsg = await m.reply_text("Calculating...")
    end = round(time() - start, 2)
    await replymsg.edit_text(f"Test complete\nTime Taken:{end} seconds")
    return
