from aiogram import Router, types, F
from aiogram.filters.command import Command

weather_router = Router()


@weather_router.message(Command("weather_voice"))  # /weather voice
async def weather_voice(message: types.Message):
    await message.answer("Бот умеет преобразовывать текст в речь и обратно. "
                         "Ткните /help для получения подробной информации.")
