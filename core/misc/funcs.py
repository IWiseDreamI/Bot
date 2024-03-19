from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def inline_kb(arr, arrType):
    buttons = []
    row = []

    for item in arr:
        callback = item.replace(" ", "_").lower()
        row.append(InlineKeyboardButton(
            text=item ,
            callback_data=f"{arrType}_{callback}"
        ))

        if(len(row) == 2): 
            buttons.append(row) 
            row = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)