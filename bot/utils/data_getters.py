from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import StorageKey
from bot.models import GroupData, UserData


async def get_groupdata(state: FSMContext) -> GroupData:
    d = await state.get_data()
    return GroupData(**d)


async def get_groupdata_from_user(bot: Bot, dp: Dispatcher, 
                                  chat_id: int) -> GroupData:
    groupkey = StorageKey(bot.id, chat_id, chat_id)
    d = await dp.fsm.storage.get_data(groupkey)
    return GroupData(**d)


async def set_groupdata_from_user(data: GroupData, bot: Bot, dp: Dispatcher, 
                                  chat_id: int) -> None:
    groupkey = StorageKey(bot.id, chat_id, chat_id)
    await dp.fsm.storage.set_data(groupkey, data.model_dump())


async def get_userdata(state: FSMContext) -> UserData:
    d = await state.get_data()
    return UserData(**d)
