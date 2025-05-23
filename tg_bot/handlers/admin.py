from aiogram.filters import Command
from aiogram import Router, types, F
from db import db_crud, db_client
from config import bot_config

admin_router = Router()


@admin_router.message(Command('users'), F.from_user.id == bot_config.admin_id)
async def get_users(message: types.Message):
	with db_client.session_factory() as session:
		users = db_crud.get_users(session)
		if len(users) == 0:
			await message.reply("Нет пользователей")
			return
	await message.reply("\n".join([f"ID {user.user_id} ({user.user_name})" for user in users]))


@admin_router.message(Command('clear'), F.from_user.id == bot_config.admin_id)
async def clear_db(message: types.Message):
	text_data = message.text.split()
	if len(text_data) == 0:
		await message.reply("Чего-то не хватает")
		return
	if text_data[1] == str(bot_config.admin_key):
		res = db_client.re_create()
		await message.reply(res[1])


@admin_router.message(Command('user_add'), F.from_user.id == bot_config.admin_id)
async def get_users(message: types.Message):
	if message.text.split()[1] == str(bot_config.admin_key):
		res = db_client.re_create()
		await message.reply(res[1])
	else:
		await message.reply("Чего-то не хватает")
