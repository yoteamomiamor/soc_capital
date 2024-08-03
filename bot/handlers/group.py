from aiogram import Router, F, Bot, Dispatcher, html
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.types import Message, ChatMemberUpdated
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from aiogram.utils.deep_linking import create_start_link
from aiogram_i18n import I18nContext, LazyProxy

from bot.states import GroupStates, UserStates
from bot.models.user import UserData
from bot.models.group import GroupData, Settings
from bot.keyboards.keyboards import get_start_keyboard
from bot.utils import set_groupdata, get_groupdata, format_players
from bot.handlers.game_functions import start_new_round

from bot.config_reader import Config

from bot.utils import get_groupdata

import logging


logger = logging.getLogger(name=__name__)

rt = Router(name=__name__)
rt.message.filter(F.chat.type.in_(('group', 'supergroup')))
rt.callback_query.filter(F.chat.type.in_(('group', 'supergroup')))


@rt.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def join_group(event: ChatMemberUpdated, state: FSMContext,
                     i18n: I18nContext, config: Config):
    group_id = event.chat.id
    groupdata = GroupData(
        game_id=event.chat.id, 
        settings=Settings(
            bank=config.bank, 
            extent=config.extent
        )
    )
    
    await event.answer(
        text=i18n.join.group(
            group_type=event.chat.type, 
            group_id=str(group_id)
        )
    )
    await state.set_state(GroupStates.menu)
    await set_groupdata(state, groupdata)


@rt.message(CommandStart(), StateFilter(GroupStates.menu, None))
async def command_create_game(message: Message, state: FSMContext, 
                              bot: Bot, i18n: I18nContext):
    await state.set_state(GroupStates.starting)

    deeplink = await create_start_link(bot, str(message.chat.id), True)
    await message.answer(
        text=i18n.start.group(),
        reply_markup=get_start_keyboard(deeplink, i18n)
    )


@rt.message(Command('settings'))
async def command_settigns(message: Message, state: FSMContext):
    await state.set_state(GroupStates.settings)
    
    groupdata = await get_groupdata(state)
    
    await message.answer('Not implemented yet, just a stub')
    await message.answer(f'settings: {groupdata.settings}')


@rt.message(Command('leave'))
async def command_leave_chat(message: Message, bot: Bot, state: FSMContext,
                             dispatcher: Dispatcher, i18n: I18nContext):
    groupdata = await get_groupdata(state)
    
    for player_id in groupdata.players:
        storage_key = StorageKey(bot.id, player_id, player_id)
        await dispatcher.fsm.storage.set_state(storage_key, UserStates.menu)
        await dispatcher.fsm.storage.set_data(storage_key, {})
        
        await bot.send_message(player_id, i18n.leave.group.user())
    
    await message.answer(text=i18n.leave.group())
    await state.clear()
    await bot.leave_chat(message.chat.id)


@rt.message(Command('cancel'), StateFilter(GroupStates.starting))
async def command_cancel_game(message: Message, state: FSMContext, bot: Bot,
                              dispatcher: Dispatcher, i18n: I18nContext):
    groupdata = await get_groupdata(state)
    
    for player_id in groupdata.players:
        storage_key = StorageKey(bot.id, player_id, player_id)
        await dispatcher.fsm.storage.set_state(storage_key, UserStates.menu)
        await dispatcher.fsm.storage.set_data(storage_key, {})

        await bot.send_message(player_id, i18n.cancel.user())
    
    groupdata.menu(groupdata.settings.bank)
    
    await state.set_data(groupdata.model_dump())
    await state.set_state(GroupStates.menu)
    
    await message.answer(i18n.cancel.group())


@rt.message(CommandStart(), StateFilter(GroupStates.starting))
async def command_start_game(message: Message, bot: Bot, config: Config, 
                             i18n: I18nContext, dispatcher: Dispatcher, 
                             state: FSMContext):
    groupdata = await get_groupdata(state)
    
    players_count = len(groupdata.players)
    minimum_players = config.minimum_players
    
    if players_count < minimum_players:
        await message.answer(
            i18n.not_enough_players(minimum_players=minimum_players)
        )
        return
    
    groupdata.settings.bank = config.bank
    groupdata.bank = players_count * config.bank

    await start_new_round(dispatcher, bot, i18n, groupdata, state)
    await state.set_data(groupdata.model_dump())
