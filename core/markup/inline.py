from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.data.env import topics

quest_confirmation_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="Добавить",
        callback_data="new_quest_true"
    ), 
    InlineKeyboardButton(
        text="🔄",
        callback_data="new_quest_regenerate"
    ),
    InlineKeyboardButton(
        text="Отклонить",
        callback_data="new_quest_false"
    )]
])

confirm_key = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="Да",
        callback_data="confirm_true"
    ), 
    InlineKeyboardButton(
        text="Нет",
        callback_data="confirm_false"
    )]
])

user_mode = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="Eng",
        callback_data="mode_eng"
    ), 
    InlineKeyboardButton(
        text="Rus",
        callback_data="mode_rus"
    )]
])

quest_type_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="Knowledge",
        callback_data="type_knowledge"
    ), 
    InlineKeyboardButton(
        text="Missing",
        callback_data="type_missing"
    )],
    [InlineKeyboardButton(
        text="Translate",
        callback_data="type_translate"
    ), 
    InlineKeyboardButton(
        text="Boolean",
        callback_data="type_boolean"
    )],
])

def get_topics_kb(mode: str):
    buttons = []
    row = []

    for topic in topics:
        row.append(InlineKeyboardButton(
            text=topic[0] if mode == "eng" else topic[1],
            callback_data=f"topic_{topic[0].lower()}"
        ))

        if(len(row) == 2): 
            buttons.append(row) 
            row = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)