import datetime

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from db import db_client, db_crud, db_models
from tg_bot.kbrds import auth_kb

auth_router = Router()


@auth_router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    with db_client.session_factory() as session:
        if db_crud.check_user(session, message.from_user.id):
            await message.answer("Привет! Я тебя знаю! Воспользуйся меню.")
            return
    await message.answer(
        "Бот умеет преобразовывать текст в речь и обратно, а также отвечать на любые вопросы. Зарегистрируемся?",
        reply_markup=auth_kb.get_auth_kb()
    )


@auth_router.message(F.text.lower() == "без предоставления номера")
async def auth_without_phone(message: types.Message, state: FSMContext):
    await message.reply(f"Твой ID {message.from_user.id}. Обратись с этим к администратору.",
                        reply_markup=types.ReplyKeyboardRemove())


@auth_router.message(F.contact)
async def auth_with_phone(message: types.Message, state: FSMContext):
    user_phone = message.contact.phone_number
    user_id = message.from_user.id
    # await state.update_data(is_auth=True, user_phone=user_phone)
    with db_client.session_factory() as session:
        if not db_crud.check_user(session, user_id):
            new_user = db_models.UserCreate(
                user_id=message.from_user.id,
                user_name=message.from_user.username,
                user_phone=user_phone,
                user_reg_timestamp=datetime.datetime.now()
            )
            db_crud.create_user(session, new_user)
    await message.reply(f"Теперь ты в теме с номером {message.contact.phone_number}",
                        reply_markup=types.ReplyKeyboardRemove())
