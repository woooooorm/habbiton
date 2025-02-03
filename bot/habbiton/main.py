import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart

from habbiton import TOKEN
from habbiton.handler import Handler
from habbiton.models.user import User
from habbiton import utils

dp = Dispatcher()
@dp.message(CommandStart())
async def respond_start(message) -> None:
    user = await User.new(
        message.from_user.id,
        message.from_user.username
    )
    await Handler(user, message).handle_start()


@dp.message()
async def respond(message) -> None:
    user = await User.from_id(message.from_user.id)
    if not user:
        await respond_start(message)
    await Handler(user, message).handle()

@dp.callback_query()
async def respond_inline(message) -> None:
    user = await User.from_id(message.from_user.id)
    callback_data = message.data.split("|")
    params = callback_data[1:]
    await getattr(Handler(user, message), callback_data[0])(*params)

async def bot() -> None:
    await utils.fill_new_db()
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.run(bot())