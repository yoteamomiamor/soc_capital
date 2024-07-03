from bot.models.group import GroupData
from typing import Callable


def is_correct_request(amount: int, border: int | tuple[int, int]) -> bool:
    if isinstance(border, int):
        return 0 <= amount <= border
    elif isinstance(border, tuple):
        return border[0] <= amount <= border[1]
    else:
        raise ValueError(f'incorrect type: {type(border)}')
