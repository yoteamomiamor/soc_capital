from typing import Any, Callable, Dict, Awaitable, Tuple
from aiogram import BaseMiddleware, Dispatcher, Bot
from aiogram.types import Update
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from bot.models import Group, User, GroupData, UserData

import logging


logger = logging.getLogger(__name__)


class GroupMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        logger.debug(f'{self.__class__.__name__} added')
     
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        self.dispatcher: Dispatcher = data['dispatcher']
        bot_id: int = data['bot'].id
        
        if event.message:
            chat = event.message.chat
        elif event.callback_query:
            chat = event.callback_query.chat
        else:
            logger.info(f'no data set for <{event.event_type}>')
            return await handler(event, data)

        groupkey = StorageKey(bot_id, chat.id, chat.id)

        groupdata = await self.dispatcher.fsm.storage.get_data(groupkey)
        groupdata = GroupData(**groupdata)
        groupstate = await self.dispatcher.fsm.storage.get_state(groupkey)
        
        data['group'] = Group(data=groupdata, state=groupstate, key=groupkey)
        
        result = await handler(event, data)
    
        await self.set(data['group'])
        
        return result


    async def set(self, group: Group) -> None:
        if not isinstance(group, (Group)):
            raise ValueError(f'unsupported type: <{type(group)}>')

        await self.dispatcher.fsm.storage.set_data(
            key=group.key, 
            data=group.data.model_dump()
        )
        await self.dispatcher.fsm.storage.set_state(
            key=group.key, 
            state=group.state
        )


class UserMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        logger.debug(f'{self.__class__.__name__} added')

     
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        
        # if any(
        #     event.message,
        #     event.callback_query
        # ):
        #     chat_id = event.event.chat.id
        
        self.dispatcher: Dispatcher = data['dispatcher']
        bot_id: int = data['bot'].id
        
        if event.message:
            chat = event.message.chat
        elif event.callback_query:
            chat = event.callback_query.chat
        else:
            logger.info(f'no data set for <{event.event_type}>')
            return await handler(event, data)

        userkey = StorageKey(bot_id, chat.id, chat.id)

        userdata = await self.dispatcher.fsm.storage.get_data(userkey)
        userdata = UserData(**userdata)
        userstate = await self.dispatcher.fsm.storage.get_state(userkey)
        
        data['user'] = User(data=userdata, state=userstate, key=userkey)
        
        result = await handler(event, data)
    
        await self.set(data['user'])
        
        return result


    async def set(self, user: User) -> None:
        if not isinstance(user, (User)):
            raise ValueError(f'unsupported type: <{type(user)}>')

        await self.dispatcher.fsm.storage.set_data(
            key=user.key, 
            data=user.data.model_dump()
        )
        await self.dispatcher.fsm.storage.set_state(
            key=user.key, 
            state=user.state
        )
