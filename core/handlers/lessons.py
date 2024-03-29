import re
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core.middlewares.check import check_example
from aiogram.enums import ParseMode
from aiogram.filters import Command

from core.markup.quests import example_quest_kb
from core.middlewares.texts import get_example_text

router = Router()

class Lesson(StatesGroup):
    lesson = State()
    lesson_last = State()
    lesson_answer = State()
    question = State()
    message_id = State()
    end = State()


@router.message(Command(commands=["end_lesson"]))
async def end_lesson(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    
    if(data.get("lesson")):
        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=data["message_id"], 
            text="Урок был досрочно завершен.",
            parse_mode=ParseMode.HTML
        )
        await message.answer(text="Вы завершили уроки досрочно.")

    else:
        await message.answer(text="Не найдено урока для досрочного завершения.")


@router.callback_query(F.data.startswith("next"))
async def start_lesson(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quest = data["lesson"].quests[0]
    mode = data["lesson"].user.mode

    qt = get_example_text(quest, mode)    
    kb = example_quest_kb(quest, mode)
    
    await state.set_state(Lesson.lesson)
    await call.message.edit_text(text=qt, reply_markup=kb)
    await state.update_data(lesson_last = 0, question = qt)


@router.callback_query(Lesson.end)
async def lesson_end(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quests = data["lesson"].quests
    last = data["lesson_last"]
    quest = quests[last]

    answer = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    correct = check_example(quest, data["lesson"], answer, data["question"])
    
    await state.clear()
    await call.answer("Правильно" if correct else "Неправильно")
    await call.message.edit_text(text="Вы успешно завершили урок")


@router.callback_query(F.data.startswith("example"))
async def example_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    quests = data["lesson"].quests
    mode = data["lesson"].user.mode
    last = data["lesson_last"]
    quest = quests[last + 1]

    answer = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    correct = check_example(quests[last], data["lesson"], answer, data["question"])

    qt = get_example_text(quest, mode)    
    kb = example_quest_kb(quest, mode)

    await call.answer("Правильно" if correct else "Неправильно")
    await call.message.edit_text(text=qt, reply_markup=kb)
    await state.update_data(lesson_last = last + 1, question=qt)

    await state.set_state(Lesson.lesson)

    if(last == len(quests) - 2): 
        await state.set_state(Lesson.end)
        return


@router.callback_query(F.data.startswith("answer"), Lesson.lesson)
async def example_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    quests = data["lesson"].quests
    mode = data["lesson"].user.mode
    last = data["lesson_last"]
    quest = quests[last + 1]

    answer = call.data.replace(re.findall(r"[^_]*_", call.data)[0], "")
    correct = check_example(quests[last], data["lesson"], answer, data["question"])

    qt = get_example_text(quest, mode)    
    kb = example_quest_kb(quest, mode)

    await call.answer("Правильно" if correct else "Неправильно")
    await call.message.edit_text(text=qt, reply_markup=kb)
    await state.update_data(lesson_last = last + 1, question=qt)

    await state.set_state(Lesson.lesson)

    if(last == len(quests) - 2): 
        await state.set_state(Lesson.end)
        return


async def set_lessons(dp: Dispatcher):
    dp.include_router(router)