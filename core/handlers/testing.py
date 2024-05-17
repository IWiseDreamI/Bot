import re
import soundfile as sf
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core.data.env import get_progress
from core.middlewares.check import check_quest
from aiogram.enums import ParseMode
from aiogram.filters import Command

from core.middlewares.voice import get_text_from_audio
from db.queries import generate_test, get_test, get_user, get_user_progress
from core.markup.quests import quest_keyboard
from core.middlewares.texts import get_result, quest_text
from core.data.env import text, commands_list

router = Router()

class Test(StatesGroup):
    test = State()
    last = State()
    question = State()
    answer = State()
    message_id = State()
    quest_mode = State()
    voice = State()
    end = State()


search_rus = lambda text: bool(re.search('[а-яА-Я]', text))

async def set_qmode(quest, question, test, state):
    if(quest.quest_type in ["translate", "translate_select"]):
        if(search_rus(question)): await state.update_data(quest_mode="rus")
        else: await state.update_data(quest_mode="eng")

    else: await state.update_data(quest_mode=test.mode)


@router.message(Command(commands=["end_test"]))
async def end_test(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    if(data.get("test")):
        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=data["message_id"], 
            text="Тестирование было досрочно завершено.", parse_mode=ParseMode.HTML
        )
        await message.answer(text="Вы успешно завершили тестирование досрочно.")
    else: await message.answer(text="Не найдено тестирования для досрочного завершения.")


@router.message(F.text.lower() == "тестирование")
async def start_testing(message: Message, state: FSMContext):
    data = await state.get_data()
    user = get_user(message.from_user.id)
    mode = user.mode

    if(data.get("test") is not None): await message.answer(text=text["unfinished_test"][user.mode]); return
    if(data.get("lesson") is not None): await message.answer(text=text["unfinished_lesson"][user.mode]); return   

    await state.set_state(Test.test)
    test = generate_test(message.from_user.id)
    quest = test.quests[0]

    question = quest_text(quest, mode, 0)
    if(quest.quest_type == "translate_select"): mode = "eng" if search_rus(question) else "rus"
    kb = quest_keyboard(quest, mode)

    await set_qmode(quest, question, test, state)
    msg = await message.answer(text=question, reply_markup=kb, parse_mode=ParseMode.HTML)
    await state.update_data(test=test, last = 0, question=question, message_id=msg.message_id)



@router.callback_query(Test.end, F.data.startswith("answer"))
async def testing_end(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    test = data.get("test")
    last = data.get("last")
    mode = data.get("quest_mode")
    last_question = data.get("question")

    answer = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    check_quest(test.quests[last], test, mode, answer, last_question)

    test = get_test(data["test"].id)

    result = get_result(test)

    await call.message.edit_text(text=result, parse_mode=ParseMode.HTML)
    await state.clear()


@router.callback_query(F.data.startswith("answer"), Test.test)
async def testing(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    test = data.get("test")
    last = data.get("last")
    mode = data.get("quest_mode")
    last_question = data.get("question")

    answer = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    correct = check_quest(test.quests[last], test, mode, answer, last_question)
    await call.answer("Правильно" if correct else "Неправильно")

    mode = test.mode

    question = quest_text(test.quests[last + 1], mode, last + 1)
    if(test.quests[last + 1].quest_type == "translate_select"): mode = "eng" if search_rus(question) else "rus"
    
    kb = quest_keyboard(test.quests[last + 1], mode)

    await set_qmode(test.quests[last + 1], question, test, state)

    await call.message.edit_text(text=question, reply_markup=kb, parse_mode=ParseMode.HTML)
    await state.update_data(last = last + 1, question=question)
    await state.set_state(Test.test)

    if(last == len(test.quests) - 2): 
        await state.set_state(Test.end)
        return


@router.message(Test.end)
async def testing_end(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data["message_id"], text="Идет проверка...", parse_mode=ParseMode.HTML)

    test = data["test"]
    last = data["last"]
    mode = data["quest_mode"]
    question = data["question"]
    answer = ""

    if(not message.text and test.quests[last].quest_type != "voice"): return
    if(test.quests[last].quest_type == "voice" and message.voice is None): answer = False
    elif(test.quests[last].quest_type == "voice"):
        file = await bot.get_file(message.voice.file_id)
        filename = file.file_id
        await bot.download(message.voice.file_id, f"core/data/voice/ogg/{filename}.ogg")
        voice_data, samplerate = sf.read(f"core/data/voice/ogg/{filename}.ogg")
        sf.write(f"core/data/voice/wav/{filename}.wav", voice_data, samplerate)
        answer = get_text_from_audio(filename, mode)
    
    else: answer = message.text

    check_quest(test.quests[last], test, mode, answer, question)

    test = get_test(data["test"].id)
    result = get_result(test)

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data["message_id"], text=result, parse_mode=ParseMode.HTML)
    await state.clear()


@router.message(Test.test)
async def testing_text_answer(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()

    await message.delete()
    await bot.edit_message_text(
        chat_id=message.chat.id, message_id=data.get("message_id"), 
        text="Идет проверка...", parse_mode=ParseMode.HTML
    )

    test = data["test"]
    last = data["last"]
    mode = data["quest_mode"]
    last_question = data["question"]

    if(not message.text and test.quests[last].quest_type != "voice"): return
    if(test.quests[last].quest_type == "voice" and message.voice is None): answer = False
    elif(test.quests[last].quest_type == "voice"): 
        file = await bot.get_file(message.voice.file_id); filename = file.file_id
        await bot.download(message.voice.file_id, f"core/data/voice/ogg/{filename}.ogg")
        voice_data, samplerate = sf.read(f"core/data/voice/ogg/{filename}.ogg")
        sf.write(f"core/data/voice/wav/{filename}.wav", voice_data, samplerate)
        answer = get_text_from_audio(filename, mode)
    else: answer = message.text

    check_quest(test.quests[last], test, mode, answer, last_question)

    mode = test.mode

    question = quest_text(test.quests[last + 1], mode, last + 1)
    if(test.quests[last + 1].quest_type == "translate_select"): mode = "eng" if search_rus(question) else "rus"
    kb = quest_keyboard(test.quests[last + 1], mode)
    await set_qmode(test.quests[last + 1], question, test, state)

    await bot.edit_message_text(
        chat_id=message.chat.id, 
        message_id=data.get("message_id"), 
        text=question, reply_markup=kb, parse_mode=ParseMode.HTML
    )
    await state.update_data(last = last + 1, question=question)
    await state.set_state(Test.test)

    if(last == len(test.quests) - 2): 
        await state.set_state(Test.end)
        return

async def set_options(dp: Dispatcher):
    dp.include_router(router)