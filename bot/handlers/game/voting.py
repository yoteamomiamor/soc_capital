from aiogram import Router, F, Bot, Dispatcher
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_i18n.context import I18nContext

from bot.models.states import UserIngame
from bot.filters.game_filters import RequestFilter
from bot.utils.validators import is_correct_request
from bot.models import Group, User
from bot.utils.player_formatter import format_players
from bot.keyboards.keyboards import get_voting_keyboard
from bot.keyboards.callbacks import VotePlayer, DoneVoiting
from bot.handlers.game_functions import start_new_round, end_the_game

import logging


logger = logging.getLogger(name=__name__)

rt = Router(name=__name__)
rt.message.filter(F.chat.type == 'private')
rt.message.filter(StateFilter(UserIngame))


async def everyone_has_voted(dispatcher: Dispatcher, bot: Bot,
                             i18n: I18nContext, group: Group):
    group.data.set_lost_players()
    lost = group.data.current_round.lost
    game_id = group.data.game_id
    
    for player_id in lost:
        await bot.send_message(player_id, i18n.lost.user())
    
    await bot.send_message(
        chat_id=game_id, 
        text=i18n.lost_players(lost_players=format_players(lost.values()))
    )

    alive = group.data.get_alive_players()
    if len(alive) == 1:
        id, player = [(k, v) for k, v in alive.items()][0]
        await bot.send_message(game_id, i18n.win.group(name=player.name))
        await bot.send_message(id, i18n.win.user())
        
        await end_the_game(dispatcher, bot, i18n, group)
        return
        
    await start_new_round(dispatcher, bot, i18n, group)


@rt.callback_query(VotePlayer.filter(), 
                   StateFilter(UserIngame.voiting.person))
async def process_vote_player(callback: CallbackQuery, i18n: I18nContext,
                              callback_data: VotePlayer, user: User,
                              group: Group): 
    await callback.message.answer(i18n.voted.user.player(
        player=callback_data.name,
        money=user.data.temp.money
    ))
    
    user_id = callback.from_user.id
    group.data.current_round.alive[user_id].new_vote(who=callback_data.id)
    user.state = UserIngame.voiting.amount


@rt.callback_query(DoneVoiting.filter(), 
                   StateFilter(UserIngame.voiting.person))
async def process_vote_player_done(callback: CallbackQuery, i18n:I18nContext,
                                   dispatcher: Dispatcher,  bot: Bot, 
                                   group: Group, user: User):
    name = callback.from_user.first_name
    group.data.current_round.alive[callback.from_user.id].has_voted = True
    
    await bot.send_message(
        chat_id=user.data.game_id, 
        text=i18n.voted.group.user(player=name)
    )
    await callback.message.answer(i18n.voted.user.amount())
    if group.data.current_round.all_voted():
        await callback.answer()
        await everyone_has_voted(dispatcher, bot, i18n, group)


@rt.message(RequestFilter(), StateFilter(UserIngame.voiting.amount))
async def process_vote_amount(message: Message, i18n:I18nContext, bot: Bot,
                              state: FSMContext, dispatcher: Dispatcher,
                              requested: int, user: User, group: Group):
    game_id = user.data.game_id
    user_id = message.from_user.id
        
    if not is_correct_request(requested, user.data.temp.money):
        await message.answer(i18n.voted.user.amount.invalid())
        return

    user.data.temp.spend(requested)
    group.data.current_round.alive[user_id].voiting[-1].amount = requested
    group.data.current_round.alive[user_id].has_voted = True

    if user.data.temp.has_money():
        await message.answer(
            text=i18n.voted.user.more(money=user.data.temp.money)
        )
        user.state = UserIngame.voiting.person
        
        await message.answer(
            text=i18n.vote.user(),
            reply_markup=get_voting_keyboard(
                player_ids={i: p for i, p 
                            in group.data.current_round.alive.items()
                            if i != user_id},
                i18n=i18n
            )
        )
        
        return

    name = message.from_user.first_name
    await bot.send_message(game_id, i18n.voted.group.user(name=name))
    await message.answer(i18n.voted.user.amount())
    
    if group.data.current_round.all_voted():
        await everyone_has_voted(dispatcher, bot, i18n, group)
            