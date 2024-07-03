from typing import Any, Callable, Dict, Awaitable, Tuple
from aiogram import BaseMiddleware, Dispatcher, Bot, flags
from aiogram.types import Update
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.dispatcher.flags import get_flag, extract_flags, check_flags

from bot.models import Group, User, GroupData, UserData

import logging


logger = logging.getLogger(__name__)


class FSMMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        logger.debug(f'{self.__class__.__name__} added')

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        if get_flag(data, 'exclude'):
            logger.info(f'no data set for event id: {event.update_id}')
            return await handler(event, data)
        
        is_user = True if get_flag(data, 'user') else False
        
        self.dispatcher: Dispatcher = data['dispatcher']
        bot_id: int = data['bot'].id
        
        if event.message:
            user_id = event.message.from_user.id
            chat = event.message.chat
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
            chat = event.callback_query.chat
        else:
            logger.info(f'no data set for <{event.event_type}>')
            return await handler(event, data)

        match chat.type:
            case 'private':
                statedata = await data['state'].get_data()
                group_id: int = statedata['game_id']
            case 'group' | 'supergroup':
                group_id = chat.id
            case _:
                raise TypeError(f'Unsupported chat type: <{chat.type}>')

        groupkey = StorageKey(bot_id, group_id, group_id)

        groupdata = await self.dispatcher.fsm.storage.get_data(groupkey)
        groupdata = GroupData(**groupdata)
        groupstate = await self.dispatcher.fsm.storage.get_state(groupkey)

        data['group'] = Group(data=groupdata, state=groupstate, key=groupkey)

        if is_user:
            userkey = StorageKey(bot_id, user_id, user_id)

            userdata = await self.dispatcher.fsm.storage.get_data(userkey)
            userdata = UserData(**userdata)
            userstate = await self.dispatcher.fsm.storage.get_state(userkey)

            data['user'] = User(data=userdata, state=userstate, key=userkey)


        result = await handler(event, data)


        await self.set(data['group'])
        if is_user:
            await self.set(data['user'])

        return result


    async def set(self, group_or_user: Group | User) -> None:
        if not isinstance(group_or_user, (Group, User)):
            raise ValueError(f'unsupported type: <{type(group_or_user)}>')

        await self.dispatcher.fsm.storage.set_data(
            key=group_or_user.key,
            data=group_or_user.data.model_dump()
        )
        await self.dispatcher.fsm.storage.set_state(
            key=group_or_user.key,
            state=group_or_user.state
        )
