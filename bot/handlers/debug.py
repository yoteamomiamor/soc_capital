from aiogram import Router, md, flags
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums.parse_mode import ParseMode

from aiogram.fsm.context import FSMContext

from bot.models import GroupData, UserData

import json

import logging


logger = logging.getLogger(name=__name__)
rt = Router(name=__name__)


@rt.message(Command('error'))
async def raise_error():
    raise Exception('this is test of the ErrorMiddleware')


@rt.message(Command('info'))
async def command_info(message: Message, state: FSMContext):
    data = await state.get_data()
    data = json.dumps(data, indent=2, ensure_ascii=False)
    
    await message.answer(
        md.pre_language(await state.get_state(), "STATE") + md.pre_language(data, "DATA"),
        parse_mode=ParseMode.MARKDOWN_V2
    )


@rt.message(Command('clear'))
async def command_clear(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('cleared')
