from aiogram import Router, F, Bot, Dispatcher, html
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram_i18n.context import I18nContext

from bot.models.states import UserIngame, GroupIngame
from bot.filters.game_filters import RequestFilter
from bot.utils.validators import is_correct_request
from bot.utils.data_loaders import set_userdata, get_userdata, \
    set_groupdata, get_groupdata
from bot.models.group import GroupData, Request, Voiting, Round, Group
from bot.models.user import UserData, User
from bot.models.states import GroupMain, UserMain
from bot.utils.player_formatter import format_players
from bot.keyboards.keyboards import get_voting_keyboard
from bot.keyboards.callbacks import VotePlayer, DoneVoiting
from bot.config_reader import Config
from bot.handlers.game_functions import start_new_round

import logging


logger = logging.getLogger(name=__name__)

rt_user = Router(name=f'{__name__}_user')
rt_user.message.filter(F.chat.type == 'private', 
                       StateFilter(UserIngame))


async def give_away_requests(dispatcher: Dispatcher, bot: Bot,
                             i18n: I18nContext, group: Group):
    await bot.send_message(group.data.game_id, i18n.all_requested.group())
    
    group.data.shrink_bank()
    group.data.set_requests()
    
    for player_id, player in group.data.current_round.alive.items():
        playerkey = StorageKey(bot.id, player_id, player_id)
        playerdata = await dispatcher.fsm.storage.get_data(playerkey)
        playerdata = UserData(**playerdata)
        
        playerdata.temp.money = player.request.response
        await dispatcher.fsm.storage.set_data(
            key=playerkey, 
            data=playerdata.model_dump()
        )
        
        await bot.send_message(player_id, i18n.response.user(
            request=player.request.request,
            response=player.request.response
        ))
    
    await bot.send_message(group.data.game_id, i18n.response.group())


async def vote_for_player(dispatcher: Dispatcher, bot: Bot,
                          i18n: I18nContext, group: Group, user: User):
    group.state = GroupIngame.voting
    await bot.send_message(user.data.game_id, i18n.vote.group())
    
    for user_id in group.data.current_round.alive:
        await dispatcher.fsm.storage.set_state(
            key=StorageKey(bot.id, user_id, user_id),
            state=UserIngame.voiting.person
        )

        await bot.send_message(
            user_id, 
            i18n.vote.user(),
            reply_markup=get_voting_keyboard(
                player_ids={i: p for i, p 
                            in group.data.current_round.alive.items()
                            if i != user_id},
                i18n=i18n
            )
        )


@rt_user.message(RequestFilter(), StateFilter(UserIngame.requesting))
async def get_money_request(message: Message, requested: int, bot: Bot,
                            i18n: I18nContext, user: User,
                            group: Group, dispatcher: Dispatcher):
    if not is_correct_request(requested, group.data.current_round.bank):
        await message.answer(i18n.got_request.user.invalid())
        return

    await message.answer(i18n.got_request.user(request=requested))
    await bot.send_message(user.data.game_id, i18n.got_request.group(
        name=message.from_user.first_name))
    
    user_id = message.from_user.id
    group.data.current_round.alive[user_id].request.request = requested
    
    if group.data.current_round.all_requested():
        await give_away_requests(dispatcher, bot, i18n, group)
        await vote_for_player(dispatcher, user.data, group.data, i18n, bot)
            
    await dispatcher.fsm.storage.set_data(group.key, group.data.model_dump()) 
