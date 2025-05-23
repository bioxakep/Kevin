import io
import os.path
import datetime
import aiogram
from aiogram.filters import Command, StateFilter
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile
from db import db_client, db_crud, db_models, RequestTypes
from voices import VoiceRecognizer, VoiceGenerator
from config import voice_config, bot_config

audio_router = Router()


class AudioStates(StatesGroup):
    recognize_voice = State()
    generate_voice = State()


@audio_router.message(Command("text"))
async def start_recognize_voice(message: types.Message, state: FSMContext):
    with db_client.session_factory() as session:
        if not db_crud.check_user(session, message.from_user.id):
            await message.reply(text='Для начала необходимо авторизоваться: /start')
            return
        now = datetime.datetime.now()
        user_req_text = db_crud.get_last_user_request_by_type(
            session,
            message.from_user.id,
            RequestTypes.AUDIO_TEXT
        )
        next_req_time: datetime.datetime = user_req_text.request_timestamp + datetime.timedelta(
            minutes=bot_config.request_time
        )
        if now < next_req_time:
            elapsed = int((next_req_time - now).total_seconds())
            await message.reply(text=f'Прошло меньше 2 минут...подождите еще {elapsed} секунд')
            return
    await state.set_state(AudioStates.recognize_voice)
    await message.reply(text='Отправьте боту аудиозапись, текст из которой вам нужно получить.')


@audio_router.message(Command("voice"))
async def start_generate_voice(message: types.Message, state: FSMContext):
    with db_client.session_factory() as session:
        if not db_crud.check_user(session, message.from_user.id):
            await message.reply(text='Для начала необходимо авторизоваться: /start')
            return
        now = datetime.datetime.now()
        user_req_text = db_crud.get_last_user_request_by_type(
            session,
            message.from_user.id,
            RequestTypes.TEXT_AUDIO
        )
        next_req_time: datetime.datetime = user_req_text.request_timestamp + datetime.timedelta(
            minutes=bot_config.request_time
        )
        if now < next_req_time:
            elapsed = int((next_req_time - now).total_seconds())
            await message.reply(text=f'Прошло меньше 2 минут...подождите еще {elapsed} секунд')
            return
    await state.set_state(AudioStates.generate_voice)
    await message.reply(text='Отправьте боту текст, который необходимо преобразовать в речь.')


@audio_router.message(StateFilter(AudioStates.recognize_voice), F.content_type == "voice")
async def recognizing_voice(message: types.Message, state: FSMContext):
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
    await message.reply(text=recognized_text)
    new_user_request = db_models.RequestCreate(
        request_type=RequestTypes.AUDIO_TEXT,
        request_data=file_name,
        request_timestamp=datetime.datetime.now(),
        user_id=message.from_user.id,
    )
    with db_client.session_factory() as session:
        db_crud.create_request(session, new_user_request)


@audio_router.message(StateFilter(AudioStates.generate_voice))
async def generating_voice(message: types.Message, state: FSMContext):
    if len(message.text) < 5:
        await message.reply('Слишком короткий текст, он должен быть не менее 5 символов.')
        return
    if len(message.text) > 1000:
        await message.reply('Слишком длинный текст, он должен быть не более 999 символов.')
        return
    voice_factory = VoiceGenerator()
    voice_file_path = voice_factory.text_to_audio_file(text=message.text)
    await message.bot.send_chat_action(message.from_user.id, aiogram.enums.ChatAction.UPLOAD_VOICE)
    await message.reply_audio(audio=FSInputFile(path=voice_file_path))
    new_user_request = db_models.RequestCreate(
        request_type=RequestTypes.TEXT_AUDIO,
        request_data=message.text,
        request_timestamp=datetime.datetime.now(),
        user_id=message.from_user.id,
    )
    with db_client.session_factory() as session:
        db_crud.create_request(session, new_user_request)
