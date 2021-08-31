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


from time import time

from ineruki import LOGGER
from ineruki.bot_class import Ineruki
from ineruki.database.antispam_db import __pre_req_antispam_users
from ineruki.database.approve_db import __pre_req_approve
from ineruki.database.blacklist_db import __pre_req_blacklists
from ineruki.database.chats_db import __pre_req_chats
from ineruki.database.filters_db import __pre_req_filters
from ineruki.database.greetings_db import __pre_req_greetings
from ineruki.database.group_blacklist import __pre_req_group_blacklist
from ineruki.database.lang_db import __load_lang_cache, __pre_req_all_langs
from ineruki.database.pins_db import __pre_req_pins_chats
from ineruki.database.reporting_db import __pre_req_all_reporting_settings
from ineruki.database.rules_db import __pre_req_all_rules
from ineruki.database.users_db import __pre_req_users
from ineruki.database.warns_db import __pre_req_warns


def pre_req_all():
    # Load local cache dictionaries
    start = time()
    LOGGER.info("Starting to load Local Caches!")
    __load_lang_cache()
    __pre_req_all_langs()
    __pre_req_greetings()
    __pre_req_blacklists()
    __pre_req_chats()
    __pre_req_antispam_users()
    __pre_req_users()
    __pre_req_filters()
    __pre_req_all_rules()
    __pre_req_approve()
    __pre_req_warns()
    __pre_req_pins_chats()
    __pre_req_all_reporting_settings()
    __pre_req_group_blacklist()
    LOGGER.info(f"Successfully loaded Local Caches in {round((time() - start), 3)}s\n")


if __name__ == "__main__":
    pre_req_all()
    Ineruki().run()
