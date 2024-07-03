from typing import Tuple

from aiogram.filters import BaseFilter
from aiogram.types import Message


class RequestFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        value = message.text
        if value.isdigit():
            return {'requested': int(value)}
