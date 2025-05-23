from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_auth_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Без предоставления номера"),
        types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
    )
    return builder.as_markup(resize_keyboard=True)
