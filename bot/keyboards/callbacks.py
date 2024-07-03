from aiogram.filters.callback_data import CallbackData


class VotePlayer(CallbackData, prefix='vote'):
    id: int
    name: str


class DoneVoiting(CallbackData, prefix='vote'):
    done: bool = True
    