from typing import Any, Callable, Dict, Awaitable, Tuple
from aiogram import BaseMiddleware, Dispatcher, Bot
from aiogram.types import Update
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.dispatcher.flags import extract_flags

from bot.models import Group, User, GroupData, UserData

import logging


logger = logging.getLogger(__name__)


class EventTypeMW(BaseMiddleware):
    def __init__(self) -> None:
        logger.debug(f'{self.__class__.__name__} added')

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        logger.debug(f'recieved event type is <{event.event_type}>')
        logger.debug(f'recieved event has flags: {extract_flags(data)}')
        return await handler(event, data)
