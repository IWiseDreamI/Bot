from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu = ReplyKeyboardMarkup(keyboard=[
    [   
        KeyboardButton(text="Обучение"),
        KeyboardButton(text="Тестирование"),

    ],
    [   
        KeyboardButton(text="Прогресс"),
        KeyboardButton(text="Опции"),
        KeyboardButton(text="Контакты"),
    ]
], input_field_placeholder="Выберите опцию:", resize_keyboard=True)
