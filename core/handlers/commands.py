import os
import re
import soundfile as sf
from aiogram.types import Message
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from dotenv import find_dotenv, load_dotenv
from aiogram import Bot, Dispatcher, F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.middlewares.ai import get_question
from core.middlewares.voice import get_text_from_audio
from core.data.env import get_bot_stats, get_bot_stats_today, get_bot_users_stats, get_stats, get_today_topic_statistic, get_topic_statistic, text, word_confirm
from core.middlewares.texts import get_lesson_text, get_new_quests
from core.markup.inline import get_topics_kb, get_topics_types_kb, quest_type_kb, quest_confirmation_kb, confirm_key
from db.queries import add_questions, change_language, change_topic, generate_lesson, get_user


class NewQuest(StatesGroup):
    quest = State()
    topic = State()
    qtype = State()
    quests = State()    


class NewWord(StatesGroup):
    topic = State()
    eword = State()
    rword = State()
    edef = State()
    rdef = State()
    end = State()
    word_message = State()


class ChangeTopic(StatesGroup):
    topic = State()

class TopicStats(StatesGroup):
    topic = State()
    today = State()


router = Router()
load_dotenv(find_dotenv())
ADMINS = list(map(lambda id: int(id),os.environ.get("ADMIN_ID").split(",")))


@router.message(Command(commands=["add_quest"]))
async def add_question(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    kb = get_topics_types_kb(user.mode)
    
    if(message.from_user.id in ADMINS): 
        await state.clear()
        await state.set_state(NewQuest.quest)
        await message.answer("Выберите тематику:", reply_markup=kb)
    
    else: await message.answer("Вы не имеете доступа к этой команде.")


@router.callback_query(F.data.startswith("topictype"), NewQuest.quest)
async def change(call: Message):
    user = get_user(call.from_user.id)
    topictype = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    await call.message.edit_text(f"Выберите тематику изучения:", reply_markup=get_topics_kb(user.mode, topictype))


@router.callback_query(F.data.startswith("topic_"), NewQuest.quest)
async def new_question_topic(call: CallbackQuery, state: FSMContext):
    topic = call.data.split("_")[1]

    await state.update_data(topic=topic)
    await call.message.edit_text(f"Выберите тип вопроса: ", reply_markup=quest_type_kb)
    

@router.callback_query(F.data.startswith("type_"), NewQuest.quest)
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
    await call.message.edit_text(text, reply_markup=quest_confirmation_kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("new_quest_regenerate"))
async def regenerate_quest(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = False

    while(not text):
        questions = get_question(data["topic"], data["qtype"])
        text = get_new_quests(questions)

    await state.update_data(questions=questions)
    await call.message.edit_text(text, reply_markup=quest_confirmation_kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("new_quest"))
async def set_quest(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    confirm = call.data.split("_")[2]
    if(confirm == "false"): await call.message.edit_text("Добавление вопроса было отменено")
    else: 
        add_questions(data["questions"])
        await call.message.edit_text("Вопросы были успешно добавлены в таблицу", parse_mode=ParseMode.HTML)


@router.message(Command(commands=["stats"]))
async def stats(message: Message):
    answer = get_stats(message.from_user.id)
    await message.answer(text=answer, parse_mode=ParseMode.HTML)


@router.message(Command(commands=["day_stats"]))
async def stats(message: Message):
    if(message.from_user.id in ADMINS): answer = get_bot_stats_today()    
    else: answer = "Вы не имеете доступа к этой команде."
    
    await message.answer(text=answer, parse_mode=ParseMode.HTML)


@router.message(Command(commands=["all_stats"]))
async def stats(message: Message):
    if(message.from_user.id in ADMINS): answer = get_bot_stats()    
    else: answer = "Вы не имеете доступа к этой команде."
    
    await message.answer(text=answer, parse_mode=ParseMode.HTML)


@router.message(Command(commands=["all_users_stats"]))
async def stats(message: Message):
    if(message.from_user.id in ADMINS): answer = get_bot_users_stats()    
    else: answer = "Вы не имеете доступа к этой команде."
    
    await message.answer(text=answer, parse_mode=ParseMode.HTML)


@router.message(Command(commands=["change_mode"]))
async def change_mode(message: Message):
    user = change_language(message.from_user.id)
    await message.answer(text=text["change_mode"][user.mode])


@router.message(Command(commands=["change_topic"]))
async def kb_change_topic(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    await state.set_state(ChangeTopic.topic)
    await message.answer(text=text["change_topic"][user.mode], reply_markup=get_topics_types_kb(user.mode))


@router.callback_query(F.data.startswith("topictype"), ChangeTopic.topic)
async def change(call: Message):
    user = get_user(call.from_user.id)
    topictype = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    await call.message.edit_text(f"Выберите тематику изучения:", reply_markup=get_topics_kb(user.mode, topictype))


@router.callback_query(F.data.startswith("topic_"), ChangeTopic.topic)
async def change(call: Message):
    topic = call.data.split("_")[1]
    change_topic(call.from_user.id, topic)
    await call.message.edit_text(f"Тематика изучения: {topic.capitalize()}.\n")


@router.message(F.text.lower() == "уроки")
async def lesson(message: Message, state: FSMContext):
    data = await state.get_data()
    user = get_user(message.from_user.id)

    if(data.get("lesson") is not None):
        await message.answer(text=text["unfinished_lesson"][user.mode])
        return
    
    if(data.get("test") is not None):
        await message.answer(text=text["unfinished_test"][user.mode])
        return
    
    lesson = generate_lesson(message.from_user.id)
    msg = await message.answer(
        text=get_lesson_text(lesson), 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Далее" if lesson.user.mode == "eng" else "Next",
                callback_data="next"
            )]
        ])
    )
    
    await state.update_data(lesson=lesson, message_id=msg.message_id)
    
@router.message(Command(commands=["add_word"]))
async def add_word(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    kb = get_topics_types_kb(user.mode)

    if(message.from_user.id in ADMINS):
        await state.clear() 
        await state.set_state(NewWord.topic)
        msg = await message.answer("Выберите тематику:", reply_markup=kb)
        await state.update_data(word_message=msg.message_id)
    
    else: await message.answer("Вы не имеете доступа к этой команде.")


@router.callback_query(F.data.startswith("topictype"), NewWord.topic)
async def change(call: Message):
    user = get_user(call.from_user.id)
    topictype = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    await call.message.edit_text(f"Выберите тематику изучения:", reply_markup=get_topics_kb(user.mode, topictype))


@router.callback_query(F.data.startswith("topic_"), NewWord.topic)
async def change(call: Message, state: FSMContext):
    topic = call.data.split("_")[1]
    
    await state.update_data(topic=topic)
    await state.set_state(NewWord.eword)
    await call.message.edit_text(f"Напишите слово на английском:")


@router.message(NewWord.eword)
async def word_def_eng(message: Message, state: FSMContext, bot: Bot):
    data  = await state.get_data()
    await state.update_data(eword=message.text)
    await state.set_state(NewWord.edef)
    
    await message.delete()
    await bot.edit_message_text(
        chat_id=message.chat.id, message_id=data.get("word_message"), 
        text=f"Напишите определение слова на английском:", parse_mode=ParseMode.HTML
    )


@router.message(NewWord.edef)
async def new_word_rus(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data(edef=message.text)
    await state.set_state(NewWord.rword)
    
    await message.delete()
    await bot.edit_message_text(
        chat_id=message.chat.id, message_id=data.get("word_message"), 
        text=f"Напишите слово на русском:", parse_mode=ParseMode.HTML
    )


@router.message(NewWord.rword)
async def word_def_rus(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data(rword=message.text)
    await state.set_state(NewWord.rdef)
    
    await message.delete()
    await bot.edit_message_text(
        chat_id=message.chat.id, message_id=data.get("word_message"), 
        text=f"Напишите определение слова на русском:", parse_mode=ParseMode.HTML
    )


@router.message(NewWord.rdef)
async def new_word_confirm(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(rdef=message.text)
    data = await state.get_data()
    text = word_confirm(data)   
    await state.set_state(NewWord.end)
    await message.delete()
    await bot.edit_message_text(
        chat_id=message.chat.id, message_id=data.get("word_message"), 
        text=text, parse_mode=ParseMode.HTML, reply_markup=confirm_key
    )


@router.callback_query(NewWord.end, F.data.startswith("confirm_"))
async def add_new_word(call: CallbackQuery, state: FSMContext):
    confirm = call.data.split("_")[1]
    
    if(confirm == "false"): await call.message.edit_text("Слово не было добавлено в бд.")
    else: await call.message.edit_text("Слово было успешно добавлено в бд.")


@router.message(Command(commands=["topic_stats", "today_topic_stats"]))
async def topic_stats(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    kb = get_topics_types_kb(user.mode)

    if(message.text == "/today_topic_stats"): await state.update_data(today="True")
    else: await state.update_data(today="False")

    if(message.from_user.id in ADMINS): 
        await state.clear()
        await state.set_state(TopicStats.topic)
        await message.answer("Выберите тематику:", reply_markup=kb)
    
    else: await message.answer("Вы не имеете доступа к этой команде.")


@router.callback_query(F.data.startswith("topictype"), TopicStats.topic)
async def topic(call: Message):
    user = get_user(call.from_user.id)
    topictype = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    await call.message.edit_text(f"Выберите тематику изучения:", reply_markup=get_topics_kb(user.mode, topictype))


@router.callback_query(F.data.startswith("topic_"), TopicStats.topic)
async def get_result(call: Message, state: FSMContext):
    topic = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    data = await state.get_data()

    answer = ""

    if(data.get("today")): answer = get_today_topic_statistic(topic)
    else: answer = get_topic_statistic(topic)

    await call.message.edit_text(answer, parse_mode=ParseMode.HTML)


async def set_admin_commands(dp: Dispatcher):
    dp.include_router(router)