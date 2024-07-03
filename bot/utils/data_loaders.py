from aiogram.fsm.context import FSMContext
from bot.models import GroupData, UserData


async def set_groupdata(state: FSMContext, data: GroupData) -> None:
    await state.set_data(data.model_dump())
    

async def get_groupdata(state: FSMContext) -> GroupData:
    dictdata = await state.get_data()
    return GroupData(**dictdata)


async def set_userdata(state: FSMContext, data: UserData) -> None:
    await state.set_data(data.model_dump())
    

async def get_userdata(state: FSMContext) -> UserData:
    dictdata = await state.get_data()
    return UserData(**dictdata)
