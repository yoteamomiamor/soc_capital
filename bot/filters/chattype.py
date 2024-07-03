from aiogram.filters import Filter


class ChatType(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.text == self.my_text