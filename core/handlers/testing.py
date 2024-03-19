import re
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core.data.env import get_progress
from core.middlewares.check import check_quest
from aiogram.enums import ParseMode
from aiogram.filters import Command

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


async def set_tmode(quest, question, test, state):
    if(quest.quest_type == "translate"):
        rus = bool(re.search('[а-яА-Я]', question))
        if(rus): await state.update_data(quest_mode="rus")
        else: await state.update_data(quest_mode="eng")
    else: 
        await state.update_data(quest_mode=test.user.mode)


@router.message(Command(commands=["end_test"]))
async def end_test(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    
    if(data.get("test")):
        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=data["message_id"], 
            text="Тестирование было досрочно завершено.",
            parse_mode=ParseMode.HTML
        )
        await message.answer(text="Вы успешно завершили тестирование досрочно.")
    else:
        await message.answer(text="Не найдено тестирования для досрочного завершения.")


@router.message(F.text.lower() == "тестирование")
async def start_testing(message: Message, state: FSMContext):
    data = await state.get_data()
    user = get_user(message.from_user.id)

    if(data.get("test") is not None):
        await message.answer(text=text["unfinished_test"][user.mode])
        return

    if(data.get("lesson") is not None):
        await message.answer(text=text["unfinished_lesson"][user.mode])
        return   
    
    await state.set_state(Test.test)
    test = generate_test(message.from_user.id)
    quest = test.quests[0]

    question = quest_text(quest, test.user.mode, 0)
    kb = quest_keyboard(quest, test.user.mode)

    await set_tmode(quest, question, test, state)
    msg = await message.answer(text=question, reply_markup=kb, parse_mode=ParseMode.HTML)
    await state.update_data(test=test, last = 0, question=question, message_id=msg.message_id)



@router.callback_query(Test.end, F.data.startswith("answer"))
async def testing_end(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    test = data["test"]
    last = data["last"]
    mode = data["quest_mode"]
    question = data["question"]
    
    answer = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    check_quest(test.quests[last], test, mode, answer, question)

    test = get_test(data["test"].id)

    result = get_result(test)

    await call.message.edit_text(text=result, parse_mode=ParseMode.HTML)
    await state.clear()


@router.callback_query(F.data.startswith("answer"), Test.test)
async def testing(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    test = data["test"]
    last = data["last"]
    mode = data["quest_mode"]
    question = data["question"]

    answer = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    
    kb = quest_keyboard(test.quests[last + 1], mode)
    correct = check_quest(test.quests[last], test, mode, answer, question)
    await set_tmode(test.quests[last + 1], question, test, state)

    await call.answer("Правильно" if correct else "Неправильно")
    question = quest_text(test.quests[last + 1], mode, last + 1)
    await call.message.edit_text(text=question, reply_markup=kb, parse_mode=ParseMode.HTML)
    await state.update_data(last = last + 1, question=question)
    await state.set_state(Test.test)

    if(last == len(test.quests) - 2): 
        await state.set_state(Test.end)
        return


@router.message(Test.test, F.text.lower() != "обучение")
async def testing_text_answer(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data["message_id"], text="Идет проверка...", parse_mode=ParseMode.HTML)

    test = data["test"]
    last = data["last"]
    mode = data["quest_mode"]
    question = data["question"]

    answer = message.text

    await message.delete()

    kb = quest_keyboard(test.quests[last + 1], mode)
    check_quest(test.quests[last], test, mode, answer, question)
    await set_tmode(test.quests[last + 1], question, test, state)

    question = quest_text(test.quests[last + 1], mode, last + 1)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data["message_id"], text=question, reply_markup=kb, parse_mode=ParseMode.HTML)
    await state.update_data(last = last + 1, question=question)

    await state.set_state(Test.test)

    if(last == len(test.quests) - 2): 
        await state.set_state(Test.end)
        return


async def set_options(dp: Dispatcher):
    dp.include_router(router)