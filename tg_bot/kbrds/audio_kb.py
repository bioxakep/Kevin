from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_audio_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Текст > Звук"),
        types.KeyboardButton(text="Звук > Текст")
    )
    return builder.as_markup(resize_keyboard=True)
