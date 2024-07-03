from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware, html
from aiogram.types import Message
from aiogram.enums.parse_mode import ParseMode

import logging


logger = logging.getLogger(__name__)


class ErrorMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        logger.debug(f'{self.__class__.__name__} added')

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exception:
            result = await event.answer(
                text=html.code(f'{type(exception).__name__}: {exception}'),
                parse_mode=ParseMode.HTML
            )
            logger.error(str(exception))
            raise exception

            return result
