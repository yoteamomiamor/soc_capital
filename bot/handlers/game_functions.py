from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram_i18n.context import I18nContext

from bot.models.states import UserIngame, GroupIngame, GroupMain, UserMain
from bot.models.group import GroupData, Group
from bot.utils.player_formatter import format_players


async def start_new_round(dispatcher: Dispatcher, bot: Bot,
                          i18n: I18nContext, group: Group):
    game_id = group.data.game_id
    
    group.data.new_round()
    
    players_names = [p.name for p in group.data.current_round.alive.values()]

    group.state = GroupIngame.requesting
    
    await bot.send_message(game_id, i18n.start.group.game())
    await bot.send_message(game_id, i18n.round.info(
        round=group.data.round_number + 1, 
        players=format_players(players_names)
    ))
    await bot.send_message(game_id, i18n.request_money.group())
    
    for id, player in group.data.current_round.alive.items():
        storage_key = StorageKey(bot.id, id, id)
        
        await dispatcher.fsm.storage.set_state(
            storage_key, UserIngame.requesting
        )
        await bot.send_message(
            chat_id=id, 
            text=i18n.request_money.user(
                name=player.name, 
                bank=group.data.current_round.bank
            )
        )
        

async def end_the_game(dispatcher: Dispatcher, bot: Bot, 
                       i18n: I18nContext, group: Group):
    game_id = group.data.game_id
    
    await bot.send_message(game_id, i18n.end_game.group())
    for i in range(group.data.round_number + 1):
        await bot.send_message(
            chat_id=game_id, 
            text=group.data.rounds[i].format(i, i18n)
        )
    await bot.send_message(game_id, i18n.create_game_text())
    
    for id, name in group.data.players.items():
        await bot.send_message(id, i18n.end_game.user(name=name))
        
        userkey = StorageKey(bot.id, id, id)
        await dispatcher.fsm.storage.set_state(userkey, UserMain.menu)
        await dispatcher.fsm.storage.set_data(userkey, {})
        
    group.state = GroupMain.menu
    group.data.menu(bank=group.data.settings.bank)
        