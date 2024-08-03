from aiogram import Router, F, Bot, Dispatcher, html
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from aiogram.utils.deep_linking import create_start_link
from aiogram_i18n import I18nContext, LazyProxy

from bot.states import GroupStates, UserStates
from bot.models import GroupData, Settings, UserData
from bot.keyboards.keyboards import get_voting_keyboard
from bot.keyboards.callbacks import VotePlayer, DoneVoiting
from bot.utils.validators import is_correct_request
from bot.utils.data_getters import *
from bot.handlers.game_functions import (vote_for_player, 
                                         give_away_requests, 
                                         everyone_has_voted)
from bot.filters.game_filters import RequestFilter

from bot.config_reader import Config

import logging


logger = logging.getLogger(name=__name__)

rt = Router(name=__name__)
rt.message.filter(F.chat.type == 'private')


@rt.message(CommandStart(deep_link=True, deep_link_encoded=True))
async def command_start_by_link(message: Message, command: CommandObject,
                                i18n: I18nContext, bot: Bot, 
                                dispatcher: Dispatcher, state: FSMContext):
    # FIXME deeplink can be invalid  
    game_id = int(command.args)
    user_id = message.from_user.id
    name = message.from_user.first_name

    groupdata = await get_groupdata_from_user(bot, dispatcher, game_id)
    groupdata.players[user_id] = name
    await set_groupdata_from_user(groupdata, bot, dispatcher, game_id)
    

    userdata = UserData(game_id=game_id)
    await state.set_data(userdata.model_dump())
    await state.set_state(UserStates.ingame.requesting.state)
    
    await message.answer(i18n.join.user(game_id=game_id))
    await bot.send_message(game_id, i18n.join.user.group(name=name))


@rt.message(Command('leave'), 
            StateFilter(UserStates.menu, UserStates.ingame.spectator))
async def command_leave_game(message: Message, bot: Bot, i18n: I18nContext,
                             state: FSMContext, dispatcher: Dispatcher):
    userdata = await get_userdata(state)
    game_id = userdata.game_id
    
    if game_id is None:
        message.answer(i18n.leave.user.invalid())
        return
    
    groupdata = await get_groupdata_from_user(bot, dispatcher, userdata.game_id)
    
    del groupdata.players[str(message.from_user.id)]

    userdata = UserData(game_id=None)
    await state.set_state(UserStates.menu)
    
    await message.answer(i18n.leave.user(game_id=game_id))
    await bot.send_message(
        chat_id=game_id, 
        text=i18n.leave.user.group(name=message.from_user.first_name)
    )


@rt.message(CommandStart())
async def command_start(message: Message, state: FSMContext, i18n: I18nContext):
    userdata = UserData(game_id=None)
    await state.set_state(UserStates.menu)
    await state.set_data(userdata.model_dump())
    
    await message.answer(i18n.start.user.help())


@rt.message(RequestFilter(), StateFilter(UserStates.ingame.requesting))
async def get_money_request(message: Message, requested: int, bot: Bot,
                            i18n: I18nContext, state: FSMContext,
                            dispatcher: Dispatcher):
    userdata = await get_userdata(state)
    groupdata = await get_groupdata_from_user(bot, dispatcher, userdata.game_id)
    
    if not is_correct_request(requested, groupdata.current_round.bank):
        await message.answer(i18n.got_request.user.invalid())
        return

    await message.answer(i18n.got_request.user(request=requested))
    await bot.send_message(userdata.game_id, i18n.got_request.group(
        name=message.from_user.first_name))
    
    user_id = message.from_user.id
    groupdata.current_round.alive[user_id].request.request = requested
    
    await state.set_data(userdata.model_dump())
    await set_groupdata_from_user(groupdata, bot, dispatcher, userdata.game_id)
    
    if groupdata.current_round.all_requested():
        await give_away_requests(dispatcher, bot, i18n, groupdata, state)
        await vote_for_player(dispatcher, bot, i18n, groupdata, state, userdata.game_id, userdata)
    


@rt.callback_query(VotePlayer.filter(), 
                   StateFilter(UserStates.ingame.voiting.person))
async def process_vote_player(callback: CallbackQuery, i18n: I18nContext,
                              callback_data: VotePlayer, state: FSMContext,
                              bot: Bot, dispatcher: Dispatcher):
    userdata = await get_userdata(state)
    
    await callback.message.answer(i18n.voted.user.player(
        player=callback_data.name,
        money=userdata.temp.money
    ))
    
    user_id = callback.from_user.id
    chat_id = userdata.game_id
    
    groupdata = await get_groupdata_from_user(bot, dispatcher, chat_id)
    groupdata.current_round.alive[user_id].new_vote(who=callback_data.id)
    await state.set_state(UserStates.ingame.voiting.amount)
    await set_groupdata_from_user(groupdata, bot, dispatcher, chat_id)
    await state.set_data(userdata.model_dump())


@rt.callback_query(DoneVoiting.filter(), 
                   StateFilter(UserStates.ingame.voiting.person))
async def process_vote_player_done(callback: CallbackQuery, i18n:I18nContext,
                                   dispatcher: Dispatcher,  bot: Bot, 
                                   state: FSMContext):
    name = callback.from_user.first_name
    userdata = await get_userdata(state)
    
    chat_id = userdata.game_id
    groupdata = await get_groupdata_from_user(bot, dispatcher, chat_id)
    groupdata.current_round.alive[callback.from_user.id].has_voted = True
    await set_groupdata_from_user(groupdata, bot, dispatcher, userdata.game_id)
    
    await bot.send_message(
        chat_id=userdata.game_id, 
        text=i18n.voted.group.user(name=name)
    )
    await callback.message.answer(i18n.voted.user.amount())
    if groupdata.current_round.all_voted():
        await callback.answer()
        await everyone_has_voted(dispatcher, bot, i18n, groupdata, state)
    
    await state.set_data(userdata.model_dump())
    await set_groupdata_from_user(groupdata, bot, dispatcher, chat_id)


@rt.message(RequestFilter(), StateFilter(UserStates.ingame.voiting.amount))
async def process_vote_amount(message: Message, i18n:I18nContext, bot: Bot,
                              state: FSMContext, dispatcher: Dispatcher,
                              requested: int):
    userdata = await get_userdata(state)
    
    game_id = userdata.game_id
    user_id = message.from_user.id
        
    if not is_correct_request(requested, userdata.temp.money):
        await message.answer(i18n.voted.user.amount.invalid())
        return

    userdata.temp.spend(requested)
    
    groupdata = await get_groupdata_from_user(bot, dispatcher, game_id)
    
    groupdata.current_round.alive[user_id].voiting[-1].amount = requested
    groupdata.current_round.alive[user_id].has_voted = True

    if userdata.temp.has_money():
        await message.answer(
            text=i18n.voted.user.more(money=userdata.temp.money)
        )
        await state.set_state(UserStates.ingame.voiting.person)
        
        await message.answer(
            text=i18n.vote.user(),
            reply_markup=get_voting_keyboard(
                player_ids={i: p for i, p 
                            in groupdata.current_round.alive.items()
                            if i != user_id},
                i18n=i18n
            )
        )
        
        await state.set_data(userdata.model_dump())
        await set_groupdata_from_user(groupdata, bot, dispatcher, game_id)
        
        return

    name = message.from_user.first_name
    await bot.send_message(game_id, i18n.voted.group.user(name=name))
    await message.answer(i18n.voted.user.amount())
    
    if groupdata.current_round.all_voted():
        await everyone_has_voted(dispatcher, bot, i18n, groupdata, state)
    
    await state.set_data(userdata.model_dump())
    await set_groupdata_from_user(groupdata, bot, dispatcher, game_id)
    