from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram_i18n.context import I18nContext

from bot.models.user import UserData
from bot.states import GroupStates, UserStates
from bot.models.group import GroupData
from bot.keyboards.keyboards import get_voting_keyboard
from bot.utils.player_formatter import format_players

from bot.utils.data_getters import *


async def start_new_round(dispatcher: Dispatcher, bot: Bot,
                          i18n: I18nContext, groupdata: GroupData,
                          state: FSMContext):
    game_id = groupdata.game_id
    
    groupdata.new_round()
    
    players_names = [p.name for p in groupdata.current_round.alive.values()]

    await state.set_state(GroupStates.ingame.requesting)
    
    await bot.send_message(game_id, i18n.start.group.game())
    await bot.send_message(game_id, i18n.round.info(
        round=groupdata.round_number + 1, 
        players=format_players(players_names)
    ))
    await bot.send_message(game_id, i18n.request_money.group())
    
    for id, player in groupdata.current_round.alive.items():
        storage_key = StorageKey(bot.id, id, id)
        
        await dispatcher.fsm.storage.set_state(
            storage_key, UserStates.ingame.requesting
        )
        await bot.send_message(
            chat_id=id, 
            text=i18n.request_money.user(
                name=player.name, 
                bank=groupdata.current_round.bank
            )
        )

async def end_the_game(dispatcher: Dispatcher, bot: Bot, 
                       i18n: I18nContext, groupdata: GroupData,
                       state: FSMContext):
    game_id = groupdata.game_id
    
    await bot.send_message(game_id, i18n.end_game.group())
    for i in range(groupdata.round_number + 1):
        await bot.send_message(
            chat_id=game_id, 
            text=groupdata.rounds[i].format(i, i18n)
        )
    await bot.send_message(game_id, i18n.create_game_text())
    
    for id, name in groupdata.players.items():
        await bot.send_message(id, i18n.end_game.user(name=name))
        
        userkey = StorageKey(bot.id, id, id)
        await dispatcher.fsm.storage.set_state(userkey, UserStates.menu)
        await dispatcher.fsm.storage.set_data(userkey, {})
        
    await state.set_state(GroupStates.menu)
    groupdata.menu(bank=groupdata.settings.bank)


async def give_away_requests(dispatcher: Dispatcher, bot: Bot,
                             i18n: I18nContext, groupdata: GroupData,
                             state: FSMContext):
    await bot.send_message(groupdata.game_id, i18n.all_requested.group())
    
    groupdata.shrink_bank()
    groupdata.set_requests()
    
    for player_id, player in groupdata.current_round.alive.items():
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
    
    await bot.send_message(groupdata.game_id, i18n.response.group())


async def vote_for_player(dispatcher: Dispatcher, bot: Bot,
                          i18n: I18nContext, groupdata: GroupData, 
                          state: FSMContext, chat_id, userdata: UserData):
    await state.set_state(GroupStates.ingame.voting)
    
    groupdata = await get_groupdata_from_user(bot, dispatcher, chat_id)
    await bot.send_message(userdata.game_id, i18n.vote.group())
    
    for user_id in groupdata.current_round.alive:
        await dispatcher.fsm.storage.set_state(
            key=StorageKey(bot.id, user_id, user_id),
            state=UserStates.ingame.voiting.person
        )

        await bot.send_message(
            user_id, 
            i18n.vote.user(),
            reply_markup=get_voting_keyboard(
                player_ids={i: p for i, p 
                            in groupdata.current_round.alive.items()
                            if i != user_id},
                i18n=i18n
            )
        )


async def everyone_has_voted(dispatcher: Dispatcher, bot: Bot,
                             i18n: I18nContext, groupdata: GroupData,
                             state: FSMContext):
    groupdata.set_lost_players()
    lost = groupdata.current_round.lost
    game_id = groupdata.game_id
    
    for player_id in lost:
        await bot.send_message(player_id, i18n.lost.user())
    
    await bot.send_message(
        chat_id=game_id, 
        text=i18n.lost_players(lost_players=format_players(lost.values()))
    )

    alive = groupdata.get_alive_players()
    if len(alive) == 1:
        id, player = [(k, v) for k, v in alive.items()][0]
        await bot.send_message(game_id, i18n.win.group(name=player.name))
        await bot.send_message(id, i18n.win.user())
        
        await set_groupdata_from_user(groupdata, bot, dispatcher, game_id)
        
        await end_the_game(dispatcher, bot, i18n, groupdata, state)
        
        return
        
    await start_new_round(dispatcher, bot, i18n, groupdata, state)
