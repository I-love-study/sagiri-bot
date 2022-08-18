import asyncio
import datetime
from abc import ABC
from loguru import logger
from typing import Optional, Type
from dateutil.relativedelta import relativedelta

from creart import create
from creart import add_creator
from creart import exists_module
from creart.creator import AbstractCreator, CreateTargetInfo


class GlobalFrequencyLimitDict:
    __temp_blacklist = {}
    __frequency_counter = {}
    __blacklist_announced = {}
    frequency_limit_dict = None

    def __init__(self, frequency_limit_dict: Optional[dict] = None):
        if frequency_limit_dict is None:
            self.frequency_limit_dict = {}
        else:
            self.frequency_limit_dict = frequency_limit_dict

    def get(self, group_id: int, member_id: int, func_name: str):
        if group_id in self.frequency_limit_dict:
            logger.info(
                f"called by {func_name} from member {member_id}, group: {group_id} frequency: {self.frequency_limit_dict[group_id]}"
            )
            return self.frequency_limit_dict[group_id]
        else:
            self.frequency_limit_dict[group_id] = 0
            return 0

    def set_zero(self):
        for key in self.frequency_limit_dict.keys():
            self.frequency_limit_dict[key] = 0
        for group in self.__frequency_counter:
            for member in self.__frequency_counter[group]:
                self.__frequency_counter[group][member] = 0

    def update(self, group_id: int, weight: int):
        if group_id in self.frequency_limit_dict:
            self.frequency_limit_dict[group_id] += weight

    def add_group(self, group_id: int):
        if group_id in self.frequency_limit_dict:
            logger.warning(f"{group_id} is already in frequency limit module!")
        else:
            self.frequency_limit_dict[group_id] = 0

    def add_temp_blacklist(self, group_id: int, member_id: int):
        if group_id in self.__temp_blacklist:
            if member_id in self.__temp_blacklist[group_id]:
                if datetime.datetime.now() > self.__temp_blacklist[group_id][member_id]:
                    self.__temp_blacklist[group_id][
                        member_id
                    ] = datetime.datetime.now() + relativedelta(hours=1)
            else:
                self.__temp_blacklist[group_id][
                    member_id
                ] = datetime.datetime.now() + relativedelta(hours=1)
        else:
            self.__temp_blacklist[group_id] = {}
            self.__temp_blacklist[group_id][
                member_id
            ] = datetime.datetime.now() + relativedelta(hours=1)

    def blacklist_judge(self, group_id: int, member_id: int) -> bool:
        if (
            group_id in self.__temp_blacklist
            and member_id in self.__temp_blacklist[group_id]
        ):
            return datetime.datetime.now() <= self.__temp_blacklist[group_id][member_id]
        else:
            return False

    def add_record(self, group_id: int, member_id: int, weight: int):
        if group_id in self.__frequency_counter:
            if member_id in self.__frequency_counter[group_id]:
                self.__frequency_counter[group_id][member_id] += weight
            else:
                self.__frequency_counter[group_id][member_id] = weight
        else:
            self.__frequency_counter[group_id] = {}
            self.__frequency_counter[group_id][member_id] = weight
        if self.__frequency_counter[group_id][member_id] > 10:
            self.add_temp_blacklist(group_id, member_id)
        # print(self.__frequency_counter[group_id][member_id])

    def announce_judge(self, group_id: int, member_id: int):
        if group_id in self.__blacklist_announced:
            if member_id in self.__blacklist_announced[group_id]:
                return self.__blacklist_announced[group_id][member_id]
            self.__blacklist_announced[group_id][member_id] = False
        else:
            self.__blacklist_announced[group_id] = {member_id: False}
        return False

    def blacklist_announced(self, group_id: int, member_id: int):
        self.__blacklist_announced[group_id][member_id] = True


class FrequencyLimitClassCreator(AbstractCreator, ABC):
    targets = (CreateTargetInfo("sagiri_bot.frequency_limit_module", "GlobalFrequencyLimitDict"),)

    @staticmethod
    def available() -> bool:
        return exists_module("sagiri_bot.frequency_limit_module")

    @staticmethod
    def create(create_type: Type[GlobalFrequencyLimitDict]) -> GlobalFrequencyLimitDict:
        return GlobalFrequencyLimitDict({})


add_creator(FrequencyLimitClassCreator)


async def frequency_limit() -> None:
    frequency_limit_instance = create(GlobalFrequencyLimitDict)
    while 1:
        await asyncio.sleep(10)
        frequency_limit_instance.set_zero()
