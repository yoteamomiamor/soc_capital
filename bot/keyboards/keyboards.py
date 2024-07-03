from aiogram_i18n.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext
from pydantic import HttpUrl
from bot.models.group import Player
from bot.keyboards.callbacks import VotePlayer, DoneVoiting


def get_start_keyboard(link: HttpUrl, 
                       i18n: I18nContext) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=i18n.start.group.button(), url=link)]
        ]
    )

def get_voting_keyboard(player_ids: dict[int, Player], i18n: I18nContext) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(
            text=player.name, 
            callback_data=VotePlayer(
                id=id, 
                name=player.name
            ).pack()
        )] for id, player in player_ids.items()
    ]
    
    done_button = InlineKeyboardButton(
        text=i18n.vote.button.done(), 
        callback_data=DoneVoiting().pack()
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard + [[done_button]])
