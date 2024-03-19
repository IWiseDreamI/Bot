import os
import soundfile as sf
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from dotenv import find_dotenv, load_dotenv


from core.markup.inline import get_topics_kb, quest_type_kb, confirmation_kb
from core.markup.reply import menu
from core.data.env import user_already_exist, admin_commands, user_commands
from core.data.env import text
from core.middlewares.ai import get_question
from core.middlewares.texts import get_new_quests
from core.middlewares.voice import get_text_from_audio

from db.queries import add_questions, add_user, change_language, get_general_info, get_user, get_user_info


class Audio(StatesGroup):
    audio = State()


class NewQuest(StatesGroup):
    topic = State()
    qtype = State()
    quests = State()    


router = Router()
load_dotenv(find_dotenv())
ADMINS = list(map(lambda id: int(id),os.environ.get("ADMIN_ID").split(",")))


@router.message(Command(commands=["add_question"]))
async def add_question(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    kb = get_topics_kb(user.mode)

    if(message.from_user.id in ADMINS): 
        await state.set_state(NewQuest.topic)
        await message.answer("Выберите тематику:", reply_markup=kb)
    
    else: await message.answer("Вы не имеете доступа к этой команде.")


@router.callback_query(F.data.startswith("topic_"), NewQuest.topic)
async def new_question_topic(call: CallbackQuery, state: FSMContext):
    topic = call.data.split("_")[1]

    await state.update_data(topic=topic)
    await state.set_state(NewQuest.qtype)
    await call.message.edit_text(f"Выберите тип вопроса: ", reply_markup=quest_type_kb)
    

@router.callback_query(F.data.startswith("type_"), NewQuest.qtype)
async def new_question_type(call: CallbackQuery, state: FSMContext):
    qtype = call.data.split("_")[1]
    await state.update_data(qtype=qtype)
    data = await state.get_data()
    text = False

    await call.message.edit_text("Идёт генерация заданий, подождите...", parse_mode=ParseMode.HTML)

    while(not text):
        questions = get_question(data["topic"], qtype)
        if(questions): text = get_new_quests(questions)

    await state.update_data(questions=questions)
    await call.message.edit_text(text, reply_markup=confirmation_kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("new_quest_regenerate"))
async def regenerate_quest(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = False

    while(not text):
        questions = get_question(data["topic"], data["qtype"])
        text = get_new_quests(questions)

    await state.update_data(questions=questions)
    await call.message.edit_text(text, reply_markup=confirmation_kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("new_quest"))
async def set_quest(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    confirm = call.data.split("_")[2]
    if(confirm == "false"): await call.message.edit_text("Добавление вопроса было отменено")
    else: 
        add_questions(data["questions"])
        await call.message.edit_text("Вопросы были успешно добавлены в таблицу", parse_mode=ParseMode.HTML)


@router.message(Command(commands=["commands"]))
async def command(message: Message):
    if(message.from_user.id in ADMINS): await message.answer(admin_commands, parse_mode=ParseMode.HTML)
    else: await message.answer(user_commands, parse_mode=ParseMode.HTML)


@router.message(Command(commands=["stats"]))
async def stats(message: Message):
    answer = ""
    if(message.from_user.id in ADMINS):
        info = get_general_info()
        answer = f"Статистика использования бота за посследние 24 часа:\n\nКол-во пройденных тестов:{info['tests_num']}\nКол-во успешно пройденных тестов: {info['success_tests']}\n\nВсего ответов: {info['answers_num']}\nПравильных ответов: {info['correct_answers']}"

    else:
        answer = "Yes"

    await message.answer(text=answer)


@router.message(Command(commands=["change_mode"]))
async def change_mode(message: Message):
    user = change_language(message.from_user.id)
    await message.answer(text=text["change_mode"][user.mode])


@router.message(Command(commands=["change_topic"]))
async def kb_change_topic(message: Message):
    user = get_user(message.from_user.id)
    await message.answer(text=text["change_topic"][user.mode], reply_markup=get_topics_kb(user.mode))


@router.callback_query(F.data.startswith("topic_"))
async def change_topic(call: Message):
    topic = call.data.split("_")[1]
    change_topic(call.from_user.id, topic)
    await call.message.edit_text(f"Тематика изучения: {topic.capitalize()}.\n")
    

@router.message(Command(commands=["audio"]))
async def audio(message: Message, state: FSMContext):
    await state.set_state(Audio.audio)
    await message.answer("Запишите голосовое - бот отправит вам текстовый вариант произнесенного")


@router.message(Audio.audio)
async def audio(message: Message, bot: Bot, state: FSMContext):
    file = await bot.get_file(message.voice.file_id)
    filename = file.file_id
    await bot.download(message.voice.file_id, f"core/data/voice/ogg/{filename}.ogg")
    data, samplerate = sf.read(f"core/data/voice/ogg/{filename}.ogg")
    sf.write(f"core/data/voice/wav/{filename}.wav", data, samplerate)
    text = get_text_from_audio(filename)
    await message.answer(text)
    await state.clear()


async def set_admin_commands(dp: Dispatcher):
    dp.include_router(router)