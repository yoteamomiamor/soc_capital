import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.callback_answer import CallbackAnswerMiddleware

from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy
from redis.asyncio import Redis

from logging import basicConfig, DEBUG, INFO, getLogger

from bot.config_reader import config
from bot.handlers import starting, requesting, voting, debug
from bot.middlewares import ErrorMiddleware, FSMMiddleware, EventTypeMW
from bot.ui_commands import set_ui_commands

from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore


# FIXME and TODO
# delete all unneseccary imports from handler modules
# add redis settings to the .env and load them (host, port, etc.)
logger = getLogger(__name__)


async def main():
    bot = Bot(
        token=config.bot_token.get_secret_value(), 
        default=DefaultBotProperties(parse_mode='HTML')
    )

    redis = Redis()
    storage = RedisStorage(redis)
    dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.CHAT)

    if config.debug_mode:
        logger.info('DEBUG MODE')
        dp.update.outer_middleware(EventTypeMW())
        dp.message.middleware(ErrorMiddleware())
        dp.include_router(debug.rt)
    
    i18n_middleware = I18nMiddleware(
        core=FluentRuntimeCore(path='bot/locales/{locale}')
    )
    i18n_middleware.setup(dp)
    dp.callback_query.middleware(CallbackAnswerMiddleware())

    dp.include_routers(
        starting.rt_group, 
        starting.rt_user,
        requesting.rt_user, 
        voting.rt
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
