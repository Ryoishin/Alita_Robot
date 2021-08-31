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


from threading import RLock
from time import time

from alita import LOGGER
from alita.database import MongoDB

INSERTION_LOCK = RLock()


class Warns(MongoDB):
    db_name = "chat_warns"

    def __init__(self, chat_id: int) -> None:
        super().__init__(self.db_name)
        self.chat_id = chat_id

    def __ensure_in_db(self, user_id: int):
        chat_data = self.find_one(
            {"chat_id": self.chat_id, "user_id": user_id},
        )
        if not chat_data:
            new_data = {
                "chat_id": self.chat_id,
                "user_id": user_id,
                "warns": [],
                "num_warns": 0,
            }
            self.insert_one(new_data)
            LOGGER.info(f"Initialized Warn Document for {user_id} in {self.chat_id}")
            return new_data
        return chat_data

    def warn_user(self, user_id: int, warn_reason=None):
        with INSERTION_LOCK:
            self.user_info = self.__ensure_in_db(user_id)
            warns = self.user_info["warns"] + [warn_reason]
            num_warns = len(warns)
            self.update(
                {"chat_id": self.chat_id, "user_id": user_id},
                {"warns": warns, "num_warns": num_warns},
            )
            return warns, num_warns

    def remove_warn(self, user_id: int):
        with INSERTION_LOCK:
            self.user_info = self.__ensure_in_db(user_id)
            curr_warns = self.user_info["warns"][:-1]
            num_warns = len(curr_warns)
            self.update(
                {"chat_id": self.chat_id, "user_id": user_id},
                {"warns": curr_warns, "num_warns": num_warns},
            )
            return curr_warns, num_warns

    def reset_warns(self, user_id: int):
        with INSERTION_LOCK:
            self.user_info = self.__ensure_in_db(user_id)
            return self.delete_one(
                {"chat_id": self.chat_id, "user_id": user_id},
            )

    def get_warns(self, user_id: int):
        with INSERTION_LOCK:
            self.user_info = self.__ensure_in_db(user_id)
            return self.user_info["warns"], len(self.user_info["warns"])

    @staticmethod
    def count_all_chats_using_warns():
        with INSERTION_LOCK:
            collection = MongoDB(Warns.db_name)
            curr = collection.find_all()
            return len({i["chat_id"] for i in curr})

    @staticmethod
    def count_warned_users():
        with INSERTION_LOCK:
            collection = MongoDB(Warns.db_name)
            curr = collection.find_all()
            return len({i["user_id"] for i in curr if i["num_warns"] >= 1})

    @staticmethod
    def count_warns_total():
        with INSERTION_LOCK:
            collection = MongoDB(Warns.db_name)
            curr = collection.find_all()
            return sum(i["num_warns"] for i in curr if i["num_warns"] >= 1)

    @staticmethod
    def repair_db(collection):
        all_data = collection.find_all()
        keys = {
            "warns": [],
            "num_warns": 0,
        }
        for data in all_data:
            for key, val in keys.items():
                try:
                    _ = data[key]
                except KeyError:
                    LOGGER.warning(
                        f"Repairing Approve Database - setting '{key}:{val}' for {data['user_id']} in {data['chat_id']}",
                    )
                    collection.update(
                        {"chat_id": data["chat_id"], "user_id": data["user_id"]},
                        {key: val},
                    )


class WarnSettings(MongoDB):
    db_name = "chat_warn_settings"

    def __init__(self, chat_id: int) -> None:
        super().__init__(self.db_name)
        self.chat_id = chat_id
        self.chat_info = self.__ensure_in_db()

    def __ensure_in_db(self):
        chat_data = self.find_one({"_id": self.chat_id})
        if not chat_data:
            new_data = {"_id": self.chat_id, "warn_mode": "none", "warn_limit": 3}
            self.insert_one(new_data)
            LOGGER.info(f"Initialized Warn Settings Document for {self.chat_id}")
            return new_data
        return chat_data

    def get_warnings_settings(self):
        with INSERTION_LOCK:
            return self.chat_info

    def set_warnmode(self, warn_mode: str = "none"):
        with INSERTION_LOCK:
            self.update(
                {"_id": self.chat_id},
                {"warn_mode": warn_mode},
            )
            return warn_mode

    def get_warnmode(self):
        with INSERTION_LOCK:
            return self.chat_info["warn_mode"]

    def set_warnlimit(self, warn_limit: int = 3):
        with INSERTION_LOCK:
            self.update(
                {"_id": self.chat_id},
                {"warn_limit": warn_limit},
            )
            return warn_limit

    def get_warnlimit(self):
        with INSERTION_LOCK:
            return self.chat_info["warn_limit"]

    @staticmethod
    def count_action_chats(mode: str):
        collection = MongoDB(WarnSettings.db_name)
        return collection.count({"warn_mode": mode})

    @staticmethod
    def repair_db(collection):
        all_data = collection.find_all()
        keys = {"warn_mode": "none", "warn_limit": 3}
        for data in all_data:
            for key, val in keys.items():
                try:
                    _ = data[key]
                except KeyError:
                    LOGGER.warning(
                        f"Repairing Approve Database - setting '{key}:{val}' for {data['_id']}",
                    )
                    collection.update({"_id": data["_id"]}, {key: val})


def __pre_req_warns():
    start = time()
    LOGGER.info("Starting Warns Database Repair...")
    collection_warns = MongoDB(Warns.db_name)
    collection_warn_settings = MongoDB(WarnSettings.db_name)
    Warns.repair_db(collection_warns)
    WarnSettings.repair_db(collection_warn_settings)
    LOGGER.info(f"Done in {round((time() - start), 3)}s!")
