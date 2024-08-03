import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.callback_answer import CallbackAnswerMiddleware

from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage ###
from aiogram.fsm.strategy import FSMStrategy
from redis.asyncio import Redis

from logging import basicConfig, DEBUG, INFO, getLogger

from bot.config_reader import config
from bot.handlers import group, user, debug
from bot.middlewares import ErrorMiddleware, EventTypeMW
from bot.ui_commands import set_ui_commands

from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore


# FIXME and TODO
# delete all unneseccary imports from handler modules
# add redis settings to the .env and load them (host, port, etc.)
#                              ...
# and actually a lot of things cause now it's just a big big mess
# and i don't really know how to make it clearer and to get rid
# of this shit with getting and saving userdata and groupdata 
# in every handler, i used to try to create a middleware but it
# was defenetely not a good expirience bc it loaded userdata and
# groupdata at the same time from message and callback updates
# so it was kinda a godobject so it didn't work properly.
# I think i should create 2 different middlewares for different
# handlers, tho idl now... i just tired of this project for now
# maybe i will continue it later, well, i hope so at least
#                              ...
# 5:10 am / 03.08.2024

logger = getLogger(__name__)


async def main():
    bot = Bot(
        token=config.bot_token.get_secret_value(), 
        default=DefaultBotProperties(parse_mode='HTML')
    )

    redis = Redis()
    storage = RedisStorage(redis)
    # storage = MemoryStorage() ###
    dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.CHAT)

    if config.debug_mode:
        logger.info('DEBUG MODE')
        dp.message.middleware(ErrorMiddleware())
        dp.include_router(debug.rt)
    
    i18n_middleware = I18nMiddleware(
        core=FluentRuntimeCore(path='bot/locales/{locale}')
    )
    i18n_middleware.setup(dp)
    dp.callback_query.middleware(CallbackAnswerMiddleware())

    dp.include_routers(
        group.rt, 
        user.rt
    )

    await set_ui_commands(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot, 
        allowed_updates=dp.resolve_used_update_types(),
        config=config
    )

if __name__ == "__main__":
    basicConfig(
        level=DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s',
    )
    asyncio.run(main())
