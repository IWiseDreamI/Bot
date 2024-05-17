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

edit_word_kb =  InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="English",
        callback_data="word_eng"
    )], 
    [InlineKeyboardButton(
        text="Русский",
        callback_data="word_rus"
    )],
    [InlineKeyboardButton(
        text="Definition",
        callback_data="word_engDef"
    )],
    [InlineKeyboardButton(
        text="Определение",
        callback_data="word_rusDef"
    )]
])

def get_edit_quest_kb(qt: str): 
    if(qt in ["translate", "translate_select"]):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="English",
                callback_data="quest_eng"
            )], 
            [InlineKeyboardButton(
                text="Русский",
                callback_data="quest_rus"
            )]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="English",
                callback_data="quest_eng"
            )], 
            [InlineKeyboardButton(
                text="Русский",
                callback_data="quest_rus"
            )]
            [InlineKeyboardButton(
                text="English",
                callback_data="quest_engAnswer"
            )], 
            [InlineKeyboardButton(
                text="Русский",
                callback_data="quest_rusAnswer"
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
    )]
])

def get_topics_types_kb(mode: str):
    buttons = []
    row = []

    for topictype in topics:
        row.append(InlineKeyboardButton(
            text=topics[topictype]["eng"] if mode == "eng" else topics[topictype]["rus"],
            callback_data=f"topictype_{topics[topictype]['eng'].lower()}"
        ))

        if(len(row) == 2): 
            buttons.append(row) 
            row = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_topics_kb(mode: str, topictype: str):
    buttons = []

    for topic in topics[topictype]:
        if(topic in ["eng", "rus"]): continue

        buttons.append([InlineKeyboardButton(
            text=topics[topictype][topic]["eng"] if mode == "eng" else topics[topictype][topic]["rus"],
            callback_data=f"topic_{topics[topictype][topic]['eng'].lower()}"
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)