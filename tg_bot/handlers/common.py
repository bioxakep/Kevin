from aiogram import Router, types, F
from aiogram.filters.command import Command

common_router = Router()


@common_router.message(Command("id"))  # /id
async def cmd_id(message: types.Message):
    await message.answer(f"Привет! Твой ID: {message.from_user.id}")


@common_router.message(F.text)
async def user_text(message: types.Message):
    await message.reply("Не понял Вас.")


@common_router.message(F.sticker)
async def cmd_stickers(message: types.Message):
    await message.reply("Зачем слать мне стикеры?")


@common_router.message(F.photo)
async def cmd_photo(message: types.Message):
    await message.reply("Зачем слать мне фото?")


@common_router.message(F.animation)
async def cmd_animation(message: types.Message):
    await message.reply("Зачем слать мне анимации всякие?")
