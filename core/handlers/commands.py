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

from core.middlewares.ai import gen_question
from core.middlewares.voice import get_text_from_audio
from core.data.env import get_bot_stats, get_bot_stats_today, get_bot_users_stats, get_stats, get_today_topic_statistic, get_topic_statistic, text, word_confirm
from core.middlewares.texts import get_lesson_text, get_new_quests, get_text_quest, get_text_word
from core.markup.inline import get_edit_quest_kb, get_topics_kb, get_topics_types_kb, quest_type_kb, quest_confirmation_kb, confirm_key, edit_word_kb
from db.queries import add_questions, change_language, change_topic, edit_quest, edit_word, generate_lesson, get_quest, get_user, get_word


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

class AddQuest(StatesGroup):
    quest = State()
    topic = State()
    qtype = State()
    quests = State() 

    equest = State()
    rquest = State()
    eanswer = State()
    ranswer = State()
    
    quest_message = State()
    end = State()


class ChangeTopic(StatesGroup):
    topic = State()

class TopicStats(StatesGroup):
    topic = State()
    today = State()


router = Router()
load_dotenv(find_dotenv())
ADMINS = list(map(lambda id: int(id),os.environ.get("ADMIN_ID").split(",")))


###############################
# Добавление вопросов вручную #
###############################

@router.message(Command(commands=["add_quest"]))
async def add_question(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    kb = get_topics_types_kb(user.mode)
    
    if(message.from_user.id in ADMINS): 
        await state.clear()
        await state.set_state(AddQuest.quest)
        msg = await message.answer("Выберите тематику:", reply_markup=kb)
        await state.update_data(quest_message=msg.message_id)
    

    else: await message.answer("Вы не имеете доступа к этой команде.")


@router.callback_query(F.data.startswith("topictype"), AddQuest.quest)
async def add_quest(call: CallbackQuery):
    user = get_user(call.from_user.id)
    topictype = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    await call.message.edit_text(f"Выберите тематику:", reply_markup=get_topics_kb(user.mode, topictype))


@router.callback_query(F.data.startswith("topic_"), AddQuest.quest)
async def added_question_topic(call: CallbackQuery, state: FSMContext):
    topic = call.data.split("_")[1]

    await state.update_data(topic=topic)
    await call.message.edit_text(f"Выберите тип вопроса: ", reply_markup=quest_type_kb)
    

@router.callback_query(F.data.startswith("type_"), AddQuest.quest)
async def added_question_type(call: CallbackQuery, state: FSMContext):
    qtype = call.data.split("_")[1]
    await state.update_data(qtype=qtype)
    await state.set_state(AddQuest.equest)
    await call.message.edit_text("Отправьте вариант вопроса на английском:", parse_mode=ParseMode.HTML)


@router.message(AddQuest.equest)
async def question_text(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    data  = await state.get_data()

    await message.delete()
    await state.update_data(equest=text)
    await state.set_state(AddQuest.rquest)
    await bot.edit_message_text(
        chat_id=message.chat.id, message_id=data.get("quest_message"), 
        text=f"Отправьте вариант вопроса на русском:", parse_mode=ParseMode.HTML
    )


@router.message(AddQuest.rquest)
async def question_text(message: Message, state: FSMContext, bot: Bot):
    text = message.text

    await state.update_data(rquest=text)
    data  = await state.get_data()
    
    await message.delete()

    if(data.get("qtype")  == "translate"):
        await state.set_state(AddQuest.end)

        quest = [{
            "eng": data.get("equest"),
            "rus": data.get("rquest"),
            "quest_type": "translate",
            "difficulty": "2",
            "topic": data.get("topic")
        }]

        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=data.get("quest_message"), 
            text=get_new_quests(quest), parse_mode=ParseMode.HTML,
            reply_markup=confirm_key
        )


    else:
        await state.set_state(AddQuest.eanswer)
        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=data.get("quest_message"), 
            text=f"Напишите ответ на вопрос в английском варианте:", parse_mode=ParseMode.HTML
        )


@router.message(AddQuest.eanswer)
async def question_text(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    data  = await state.get_data()

    await message.delete()
    await state.update_data(eanswer=text)

    await state.set_state(AddQuest.ranswer)
    await bot.edit_message_text(
        chat_id=message.chat.id, message_id=data.get("quest_message"), 
        text=f"Напишите ответ на вопрос в русском варианте:", parse_mode=ParseMode.HTML
    )


@router.message(AddQuest.ranswer)
async def question_text(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    await state.update_data(ranswer=text)
    data  = await state.get_data()

    await message.delete()
    await state.set_state(AddQuest.end)

    quest = [{
        "eng": data.get("equest"),
        "rus": data.get("rquest"),
        "eng_answer": data.get("eanswer"),
        "rus_answer": data.get("ranswer"),
        "quest_type": data.get("qtype"),
        "difficulty": "1",
        "topic": data.get("topic")
    }]

    await state.update_data(quest=quest)

    await bot.edit_message_text(
        chat_id=message.chat.id, message_id=data.get("quest_message"), 
        text=get_new_quests(quest), parse_mode=ParseMode.HTML,
        reply_markup=confirm_key
    )

@router.callback_query(AddQuest.end)
async def set_quest(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    confirm = call.data.split("_")[1]
    if(confirm == "false"): await call.message.edit_text("Добавление вопроса было отменено")
    else: 
        add_questions(data["quest"])
        await call.message.edit_text("Вопрос был успешно добавлены в таблицу", parse_mode=ParseMode.HTML)


#######################################
# Добавление вопросов через генерацию # 
#######################################

@router.message(Command(commands=["generate_quest"]))
async def add_question(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    kb = get_topics_types_kb(user.mode)
    
    if(message.from_user.id in ADMINS): 
        await state.clear()
        await state.set_state(NewQuest.quest)
        await message.answer("Выберите тематику:", reply_markup=kb)
    
    else: await message.answer("Вы не имеете доступа к этой команде.")


@router.callback_query(F.data.startswith("topictype"), NewQuest.quest)
async def new_question_topic(call: CallbackQuery):
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
        questions = gen_question(data["topic"], qtype)
        if(questions): text = get_new_quests(questions)

    await state.update_data(questions=questions)
    await call.message.edit_text(text, reply_markup=quest_confirmation_kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("new_quest_regenerate"), NewQuest.quest)
async def regenerate_quest(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.message.edit_text(f"Идет генерация нового вопроса...")
    text = False

    while(not text):
        questions = gen_question(data["topic"], data["qtype"])
        text = get_new_quests(questions)

    await state.update_data(questions=questions)
    await call.message.edit_text(text, reply_markup=quest_confirmation_kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("new_quest"), NewQuest.quest)
async def set_quest(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    confirm = call.data.split("_")[2]
    if(confirm == "false"): await call.message.edit_text("Добавление вопроса было отменено")
    else: 
        add_questions(data["questions"])
        await call.message.edit_text("Вопросы были успешно добавлены в таблицу", parse_mode=ParseMode.HTML)
    
    state.clear()

#####################
# Команды статистик #
#####################

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


###################################
# Смена пользовательских настроек #
###################################


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


#########
# Уроки #
#########

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

###################
# Добавление слов #
###################

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
async def word_topictype(call: Message):
    user = get_user(call.from_user.id)
    topictype = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    await call.message.edit_text(f"Выберите тематику изучения:", reply_markup=get_topics_kb(user.mode, topictype))


@router.callback_query(F.data.startswith("topic_"), NewWord.topic)
async def word_topic(call: Message, state: FSMContext):
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
    await state.clear()


#################
# Question edit #
#################
class EditQuest(StatesGroup):
    quest = State()
    updated = State()
    quest_item = State()
    edit_message = State()

@router.message(Command(commands=["edit_quest"]))
async def start_edit_quest(message: Message, state: FSMContext):
    await state.set_state(EditQuest.quest)
    msg = await message.answer("Введите числовое ID вопроса (#1024):")
    await state.update_data(edit_message = msg.message_id)


@router.message(EditQuest.quest)
async def edit_quest_id(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    quest_id = int(message.text.replace("#", "")) 
    await message.delete()

    qdata = get_quest(quest_id) 
    
    if qdata:
        text = get_text_quest(qdata)    
        
        await state.update_data(quest=qdata)
        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=data.get("edit_message"), 
            text=text, parse_mode=ParseMode.HTML, reply_markup=confirm_key
        )
    
    else: 
        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=data.get("edit_message"), 
            text="Вопроса не найдено, попробуйте ещё раз.", parse_mode=ParseMode.HTML, reply_markup=confirm_key
        )

@router.callback_query(EditQuest.quest, F.data.startswith("confirm_"))
async def edit_quest_item(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    confirm = call.data.split("_")[1]

    if(confirm == "false"): await call.message.edit_text("Введите числовое ID вопроса (#1024):")
    else:
        kb = get_edit_quest_kb(data.get("quest").quest_type)
        await call.message.edit_text("Выберите значение для изменения:", reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(EditQuest.quest, F.data.startswith("quest_"))
async def edit_quest_item_value(call: CallbackQuery, state: FSMContext):
    data = call.data.split("_")[1]
    data = "eng_answer" if (data == "engAnswer") else data
    data = "rus_answer" if (data == "rusAnswer") else data
    await state.set_state(EditQuest.quest_item)
    await state.update_data(quest_item=data)
    await call.message.edit_text("Введите измененный вариант:", parse_mode=ParseMode.HTML)


@router.message(EditQuest.quest_item)
async def edit_quest_item(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    qdata = data.get("quest") 
    qi = data.get("quest_item")

    updated_quest = {
        "eng": qdata.eng,
        "eng_answer": qdata.eng_answer,
        "rus": qdata.rus,
        "rus_answer": qdata.rus_answer,
    }

    replaced = updated_quest[qi]
    updated_quest[qi] = message.text

    text = get_text_quest(qdata).replace(replaced, message.text)    
    await state.update_data(updated=updated_quest)
    await bot.edit_message_text(
        chat_id=message.chat.id, message_id=data.get("edit_message"), 
        text=text, parse_mode=ParseMode.HTML, reply_markup=confirm_key
    )


@router.callback_query(EditQuest.quest_item, F.data.startswith("confirm_"))
async def edit_quest_item(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    confirm = call.data.split("_")[1]

    if(confirm == "false"): await call.message.edit_text("Отмена")
    else: 
        edit_quest(data.get("quest").id, data.get("updated"))        
        await call.message.edit_text("Изменения были применены", parse_mode=ParseMode.HTML)
    
    await state.clear()

#############
# Word edit #
#############
class EditWord(StatesGroup):
    word = State()
    updated = State()
    word_item = State()
    edit_message = State()

@router.message(Command(commands=["edit_word"]))
async def start_edit_word(message: Message, state: FSMContext):
    await state.set_state(EditWord.word)
    msg = await message.answer("Введите слово на английском:")
    await state.update_data(edit_message = msg.message_id)

@router.message(EditWord.word)
async def edit_word_find(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data() 
    await message.delete()

    wdata = get_word(message.text)     

    if wdata:
        text = get_text_word(wdata)
        await state.update_data(word=wdata)
        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=data.get("edit_message"), 
            text=text, parse_mode=ParseMode.HTML, reply_markup=confirm_key
        )

    else:
        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=data.get("edit_message"), 
            text="Слово не найдено, попробуйте ещё раз.", parse_mode=ParseMode.HTML
        )
    
@router.callback_query(EditWord.word, F.data.startswith("confirm_"))
async def word_item(call: CallbackQuery, state: FSMContext):
    confirm = call.data.split("_")[1]

    if(confirm == "false"): await call.message.edit_text("Введите слово на английском:")
    else:
        kb = edit_word_kb
        await call.message.edit_text("Выберите значение для изменения:", reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(EditWord.word, F.data.startswith("word_"))
async def edit_word_item_value(call: CallbackQuery, state: FSMContext):
    data = call.data.split("_")[1]
    data = "eng_def" if (data == "engDef") else data
    data = "rus_def" if (data == "rusDef") else data
    await state.set_state(EditWord.word_item)
    await state.update_data(word_item=data)
    await call.message.edit_text("Введите измененный вариант:", parse_mode=ParseMode.HTML)


@router.message(EditWord.word_item)
async def edit_word_item(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    wdata = data.get("word") 
    wi = data.get("word_item")

    updated_word = {
        "eng": wdata.eng,
        "eng_def": wdata.eng_def,
        "rus": wdata.rus,
        "rus_def": wdata.rus_def,
    }

    replaced = updated_word[wi]
    updated_word[wi] = message.text

    text = get_text_word(wdata).replace(replaced, message.text)    
    await state.update_data(updated=updated_word)
    await bot.edit_message_text(
        chat_id=message.chat.id, message_id=data.get("edit_message"), 
        text=text, parse_mode=ParseMode.HTML, reply_markup=confirm_key
    )   


@router.callback_query(EditWord.word_item, F.data.startswith("confirm_"))
async def edit_word_item(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    confirm = call.data.split("_")[1]

    if(confirm == "false"): await call.message.edit_text("Отмена")
    else: 
        edit_word(data.get("word").id, data.get("updated"))        
        await call.message.edit_text("Изменения были применены", parse_mode=ParseMode.HTML)
    
    await state.clear()

#################
# import router #
#################

async def set_admin_commands(dp: Dispatcher):
    dp.include_router(router)
