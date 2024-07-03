from aiogram import Router, F, Bot, Dispatcher, html
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.types import Message, ChatMemberUpdated
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from aiogram.utils.deep_linking import create_start_link
from aiogram_i18n import I18nContext, LazyProxy

from bot.models.states import GroupMain, GroupIngame, UserMain, UserIngame
from bot.models.user import User, UserData
from bot.models.group import Group, GroupData, Settings
from bot.keyboards.keyboards import get_start_keyboard
from bot.utils import set_groupdata, get_groupdata, format_players
from bot.handlers.game_functions import start_new_round
from bot.middlewares.fsmmiddleware import FSMMiddleware

from bot.config_reader import Config

import logging


logger = logging.getLogger(name=__name__)

rt = Router(name=__name__)
rt.message.middleware(FSMMiddleware)

@rt_user.message(CommandStart(deep_link=True, deep_link_encoded=True))
async def command_start_by_link(message: Message, command: CommandObject,
                                user: User, group: Group, i18n: I18nContext,
                                bot: Bot):
    # FIXME deeplink can be invalid  
    game_id = int(command.args)
    user_id = message.from_user.id
    name = message.from_user.first_name

    group.data.players[user_id] = name

    user.state = UserIngame.requesting.state
    user.data = UserData(game_id=game_id)
    
    await message.answer(i18n.join.user(game_id=game_id))
    await bot.send_message(game_id, i18n.join.user.group(name=name))


@rt_group.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
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
    await state.set_state(GroupMain.menu)
    await set_groupdata(state, groupdata)


@rt_group.message(CommandStart(), StateFilter(GroupMain.menu, None))
async def command_create_game(message: Message, state: FSMContext, bot: Bot,
                              i18n: I18nContext, group: Group):
    group.state = GroupMain.starting.state

    deeplink = await create_start_link(bot, str(message.chat.id), True)
    await message.answer(
        text=i18n.start.group(),
        reply_markup=get_start_keyboard(deeplink, i18n)
    )


@rt_group.message(Command('settings'))
async def command_settigns(message: Message, group: Group):
    group.state = GroupMain.settings.state
    
    await message.answer('Not implemented yet, just a stub')
    await message.answer(f'settings: {group.data.settings}')


@rt_group.message(Command('leave'))
async def command_leave_chat(message: Message, bot: Bot, group: Group,
                             dispatcher: Dispatcher, i18n: I18nContext):
    for player_id in group.data.players:
        storage_key = StorageKey(bot.id, player_id, player_id)
        await dispatcher.fsm.storage.set_state(storage_key, UserMain.menu)
        await dispatcher.fsm.storage.set_data(storage_key, {})
        
        await bot.send_message(player_id, i18n.leave.group.user())
    
    await message.answer(text=i18n.leave.group())
    group.state = None
    await bot.leave_chat(message.chat.id)


@rt_group.message(Command('cancel'), StateFilter(GroupMain.starting))
async def command_cancel_game(message: Message, group: Group, bot: Bot,
                              dispatcher: Dispatcher, i18n: I18nContext):
    for player_id in group.data.players:
        storage_key = StorageKey(bot.id, player_id, player_id)
        await dispatcher.fsm.storage.set_state(storage_key, UserMain.menu)
        await dispatcher.fsm.storage.set_data(storage_key, {})

        await bot.send_message(player_id, i18n.cancel.user())
    
    group.data.menu(group.data.settings.bank)
    group.state = GroupMain.menu.state
    
    await message.answer(i18n.cancel.group())


@rt_group.message(CommandStart(), StateFilter(GroupMain.starting))
async def command_start_game(message: Message, bot: Bot, config: Config, 
                             i18n: I18nContext, dispatcher: Dispatcher, 
                             group: Group):
    players_count = len(group.data.players)
    minimum_players = config.minimum_players
    
    if players_count < minimum_players:
        await message.answer(
            i18n.not_enough_players(minimum_players=minimum_players)
        )
        return
    
    group.data.settings.bank = config.bank
    group.data.bank = players_count * config.bank

    await start_new_round(dispatcher, bot, i18n, group)


@rt_user.message(Command('leave'), 
                 StateFilter(UserMain.menu, UserIngame.spectator))
async def command_leave_game(message: Message, bot: Bot, i18n: I18nContext,
                             user: User, group: Group):
    game_id = user.data.game_id
    
    if game_id is None:
        message.answer(i18n.leave.user.invalid())
        return
    
    del group.data.players[str(message.from_user.id)]

    user.data = UserData(game_id=None)
    user.state = UserMain.menu.state
    
    await message.answer(i18n.leave.user(game_id=game_id))
    await bot.send_message(
        chat_id=game_id, 
        text=i18n.leave.user.group(name=message.from_user.first_name)
    )


@rt_user.message(CommandStart())
async def command_start(message: Message, user: User, i18n: I18nContext):
    user.state = UserMain.menu.state
    user.data = UserData(game_id=None)
    
    await message.answer(i18n.start.user.help())
