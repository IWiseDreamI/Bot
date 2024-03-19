from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from core.markup.inline import user_mode, confirm_key, get_topics_kb
from core.markup.reply import menu
from core.data.env import get_progress, text, user_already_exist

from db.queries import add_user, change_topic, get_user, get_user_progress

class User(StatesGroup):
    username = State()
    user_id = State()
    fullname = State()
    confirm = State()
    mode = State()
    topic = State()

router = Router()

@router.message(Command(commands=["start"]))
async def start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    username = message.from_user.username
    if(user):
        await message.answer(text=user_already_exist, reply_markup=menu)
        return False
    
    await state.set_state(User.confirm)
    await message.answer(f"Добро пожаловать{f', {username}' if username else None}! 🌟\nДавайте познакомимся поближе – введите своё ФИО 😊")
    

@router.message(User.confirm)
async def confirm(message: Message, state: FSMContext):
    await state.update_data(confirm=message.text)
    await state.update_data(user_id=message.from_user.id)
    await state.update_data(username=message.from_user.username)
    await state.set_state(User.mode)
    await message.answer(f"Ваше ФИО: {message.text}?", reply_markup=confirm_key)


@router.callback_query(F.data.startswith("confirm"), User.mode)
async def fullname(call: CallbackQuery, state: FSMContext):
    confirm = call.data.split("_")[1]
    data = await state.get_data()

    if(confirm == "false" or data.get("confirm") is None or len(data.get("confirm")) > 255):
        await state.set_state(User.confirm)
        await call.answer("Введите ФИО ещё раз")
        await call.message.edit_text("Введите ФИО:")
        return
    
    await state.set_state(User.mode)
    await state.update_data(fullname=data["confirm"])
    await call.answer(f"ФИО: {data['confirm']}")
    await call.message.edit_text("Выберите язык изучения:", reply_markup=user_mode)


@router.callback_query(F.data.startswith("mode"), User.mode)
async def mode(call: CallbackQuery, state: FSMContext):
    mode = call.data.split("_")[1]
    await state.set_state(User.topic)
    await state.update_data(mode=mode)
    await call.answer(f"Выбран режим: {mode.capitalize()}")
    await call.message.edit_text("Выберите тематику изучения:", reply_markup=get_topics_kb(mode))


@router.callback_query(F.data.startswith("topic_"), User.topic)
async def topic(call: CallbackQuery, state: FSMContext):
    topic = call.data.split("_")[1]
    await state.update_data(topic=topic)
    await call.answer(f"Выбрана тема: {topic}")

    data = await state.get_data()

    add_user(data)
    await call.message.edit_text(f"Выбранная тематика изучения: {topic.capitalize()}.\n")
    await call.message.answer(text["greeting"][data["mode"]], reply_markup=menu)


@router.message(F.text.lower() == "опции")
async def options(message: Message):
    user = get_user(message.from_user.id)
    await message.answer(
        text=text["options"][user.mode], 
        parse_mode=ParseMode.HTML
    )


@router.message(F.text.lower() == "контакты")
async def options(message: Message):
    user = get_user(message.from_user.id)
    await message.answer(text=text["contacts"][user.mode])


@router.message(F.text.lower() == "прогресс")
async def show_progress(message: Message):
    progress = get_user_progress(message.from_user.id)
    await message.answer(
        get_progress(progress), 
        parse_mode=ParseMode.HTML
    )


async def set_start(dp: Dispatcher):
    dp.include_router(router)