import io
import os.path
import datetime
import aiogram
from aiogram.filters import Command, StateFilter
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile, InlineKeyboardMarkup

from db import db_client, db_crud, RequestTypes, db_models
from ollama_bot import OllamaBot
from voices import VoiceRecognizer, VoiceGenerator
from config import voice_config, ollama_config, bot_config

chat_router = Router()
smart_bot = OllamaBot(bin_path=ollama_config.binary_path, model=OllamaBot.SMART_MODEL)


class ChatStates(StatesGroup):
	answer_for_question = State()
	select_model = State()


@chat_router.message(StateFilter(ChatStates.answer_for_question), F.content_type == "voice")
async def catch_audio_from_auth_user(message: types.Message, state: FSMContext):
	# Сохранить в файл, прочитать распознаванием, вывести текст.
	voice_file_info = await message.bot.get_file(message.voice.file_id)
	voice_ogg = io.BytesIO()
	await message.bot.download_file(voice_file_info.file_path, voice_ogg)
	file_prefix = str(message.from_user.id) + '_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	file_name = file_prefix + '_' + voice_file_info.file_path.split('/')[1].replace('.oga', '.ogg')
	voice_ogg_path = os.path.join(voice_config.audio_files, file_name)
	with open(voice_ogg_path, 'wb') as out_voice_file:
		out_voice_file.write(voice_ogg.read())
	voice_recognizer = VoiceRecognizer(model_path=voice_config.small_ru_model)
	recognized_text = voice_recognizer.recognize_ogg(voice_ogg_path)
	data = await state.get_data()
	model = data.get('model', None)
	await message.bot.send_chat_action(message.from_user.id, aiogram.enums.ChatAction.UPLOAD_VOICE)
	response = smart_bot.ask(recognized_text, model=model)
	voice_factory = VoiceGenerator()
	voice_file_path = voice_factory.text_to_audio_file(text=response)
	await message.reply_audio(audio=FSInputFile(path=voice_file_path))
	await message.reply(text=response)
	new_user_request = db_models.RequestCreate(
		request_type=RequestTypes.QUESTION_AUDIO,
		request_data=file_name,
		request_timestamp=datetime.datetime.now(),
		user_id=message.from_user.id,
	)
	with db_client.session_factory() as session:
		db_crud.create_request(session, new_user_request)
	await state.clear()


@chat_router.message(StateFilter(ChatStates.answer_for_question))
async def catch_text_from_auth_user(message: types.Message, state: FSMContext):
	await message.bot.send_chat_action(message.from_user.id, aiogram.enums.ChatAction.UPLOAD_VOICE)
	data = await state.get_data()
	model = data.get('model', None)
	response = smart_bot.ask(message.text, model=model)
	voice_factory = VoiceGenerator()
	voice_file_path = voice_factory.text_to_audio_file(text=response)
	await message.reply_audio(audio=FSInputFile(path=voice_file_path))
	await message.reply(text=response)
	new_user_request = db_models.RequestCreate(
		request_type=RequestTypes.QUESTION_TEXT,
		request_data=message.text,
		request_timestamp=datetime.datetime.now(),
		user_id=message.from_user.id,
	)
	with db_client.session_factory() as session:
		db_crud.create_request(session, new_user_request)
	await state.clear()


@chat_router.message(Command("ask"))
async def start_recognize_text(message: types.Message, state: FSMContext):
	with db_client.session_factory() as session:
		if not db_crud.check_user(session, message.from_user.id):
			await message.reply(text='Для начала необходимо авторизоваться: /start')
			return
		now = datetime.datetime.now()
		user_req_text = db_crud.get_last_user_request_by_type(
			session,
			message.from_user.id,
			RequestTypes.QUESTION_TEXT
		)
		next_req_time: datetime.datetime = user_req_text.request_timestamp + datetime.timedelta(
			minutes=bot_config.request_time
		)
		if now < next_req_time:
			elapsed = int((next_req_time - now).total_seconds())
			await message.reply(text=f'Прошло меньше 2 минут...подождите еще {elapsed} секунд')
			return
		user_req_audio = db_crud.get_last_user_request_by_type(
			session,
			message.from_user.id,
			RequestTypes.QUESTION_AUDIO
		)
		next_req_time: datetime.datetime = user_req_audio.request_timestamp + datetime.timedelta(
			minutes=bot_config.request_time
		)
		if now < next_req_time:
			elapsed = int((next_req_time - now).total_seconds())
			await message.reply(text=f'Прошло меньше 2 минут...подождите еще {elapsed} секунд')
			return
	await state.set_state(ChatStates.answer_for_question)
	await message.reply(text='Отправьте боту голосовое с вопросом или задайте его текстом')


@chat_router.message(Command("models"))
async def start_recognize_text(message: types.Message, state: FSMContext):
	with db_client.session_factory() as session:
		if not db_crud.check_user(session, message.from_user.id):
			await message.reply(text='Для начала необходимо авторизоваться: /start')
			return
	inline_keyboard_buttons = [[
		types.InlineKeyboardButton(text=m, callback_data=m) for m in smart_bot.models
	]]
	kb_markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard_buttons)
	await state.set_state(ChatStates.select_model)
	await message.reply(text='Выберите модель', reply_markup=kb_markup)


@chat_router.callback_query(StateFilter(ChatStates.select_model))
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.bot.answer_callback_query(callback_query.id)
	await state.update_data(model=callback_query.data)
	await callback_query.bot.send_message(
		chat_id=callback_query.from_user.id,
		text='Выбрана модель: ' + callback_query.data,
		reply_markup=types.ReplyKeyboardRemove()
	)
	await state.clear()
