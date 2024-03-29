from math import ceil
import os
import json

from db.models import Progress
from db.queries import bot_stats, get_user_stats

path = f"{os.path.dirname(os.path.abspath(__file__))}/data.json"
data = {}

with open(path, "r") as file: data = json.loads(file.read()) 

topics = [
    ["Tennis", "Теннис"], 
    ["Archery", "Стрельба из лука"], 
    ["Boxing", "Бокс"], 
    ["Basketball", "Баскетбол"], 
    ["Hockey", "Хоккей"], 
    ["Volleyball", "Волейбол"]
]

user_already_exist = "Вы уже зарегистрированы. \n\nЧтобы изменить информацию, режим или тематику выберите \"Опции\" на клавиатуре."

quest_type_text = {
    "missing": {
        "eng": "Select the missing word:",
        "rus": "Выберите пропущенное слово:"
    },
    "shuffled": {
        "eng": "Match the words:",
        "rus": "Сопоставьте слова:"
    },
    "knowledge": {
        "eng": "Choose correct answer:",
        "rus": "Выберите соответсвующий ответ:"
    },
    "boolean": {
        "eng": "True or false?",
        "rus": "Правда или ложь?"
    },
    "definition": {
        "eng": "Choose a definition that matches the term:",
        "rus": "Выберите определение, соответствующее термину:"
    },
    "translate": {
        "eng": "Translate",
        "rus": "Переведите"
    },
    "voice": {
        "eng": "Send a voice message of the text",
        "rus": "Отправьте голосовое сообщение текста который вы видите"
    }
}

text = {
    "greeting": {
        "rus": "Hi! 🌐 Welcome to our language bot.\n\nHere you can improve your Russian in sports!\n\nTo start learning, click on \"Study\"\nTo start testing, click on \"Test\"\n\nTo fully complete a course in one of the topics you need 10,000 points.You can view your points by clicking on \"Progress\". Enjoy!",
        "eng": "Привет! 🌐 Добро пожаловать в нашего языкового бота.\n\nЗдесь ты можешь подтянуть свой английский в спортивной сфере!\n\nЧтобы начать изучение материала - нажми кнопку \"уроки\"\nЧтобы начать тестирование - нажми \"Тестирование\"\n\nЧтобы полностью завершить курс по одной из тематик нужно набрать 10.000 очков.\nСвои очки ты можешь посмотреть нажав на \"Прогресс\"\n\nПриятного использования!"
    },
    "options": {
        "rus": "<code>Available options:\n\n</code>/change_mode<code> - Switch the language of study\n</code>/change_topic<code> - Change the topic of the assignments</code>/stats<code> - Statistics</code>",
        "eng": "<code>Доступные опции:\n\n</code>/change_mode<code> - Переключить язык изучения\n</code>/change_topic<code> - Сменить тематику заданий</code>/stats<code> - Статистика</code>"    
    },
    "change_mode": {
        "rus": "You're succesfully switched learning language, now you will learn russian.",
        "eng": "Вы сменили язык изучения, теперь материал будет на английском."
    },
    "change_topic": {
        "rus": "Select new topic to learn:",
        "eng": "Выберите тематику изучения:"
    },
    "unfinished_test": {
        "rus": "Complete the test to continue.\nOr use the /end_test command to end it.",
        "eng": "Завершите тестирование, чтобы продолжить.\nИли воспользуйтесь командой /end_test чтобы его завершить."
    },
    "contacts": {
        "rus": "Контакты:\nТелефон: +7-914-167-45-99\nEmail: email@gmail.com",
        "eng": "Contacts:\nPhone: +7-914-167-45-99\nEmail: email@gmail.com"
    },
    "unfinished_lesson": {
        "rus": "Complete the lesson to continue 🔚.\nOr use the /end_lesson command to end it.",
        "eng": "Завершите урок, чтобы продолжить 🔚.\nИли воспользуйтесь командой /end_lesson чтобы его завершить."
    },
    "admin_options": "<code>Доступные опции:\n\n</code>/change_mode<code> - Переключить язык изучения\n</code>/change_topic<code> - Сменить тематику заданий</code>\n/stats<code> - Ваша статистика</code>\n/day_stats<code> - Статистика бота за день</code>\n/all_stats<code> - Статистика за всё время</code>\n/add_word<code> - Добавить слово</code>\n/add_quest<code> - Добавить вопрос</code>"        
}

commands_list = ["тестирование", "уроки", "/end_test", "/end_lesson", "прогресс", "опции", "контакты"]

def get_progress(progress: Progress):
    pb = "[" + "-" * 12 + "]"
    gp = ceil(ceil(progress.exp / 100) / 8)
    um = progress.user.mode

    while(gp > 0): 
        pb = pb.replace("-", "@", 1)
        gp -= 1

    if(um == "eng"): return f"<code>Пользователь: {progress.user.fullname}\nВыбранная тематика: {progress.topic.rus.capitalize()}\nЯзык изучения: Английский\n\nПрогресс: {pb} ({progress.exp / 100}%)\nОчков опыта: {f'{progress.exp:,}'.replace(',', '.')} / 10.000</code>"
    else: return f"<code>User: {progress.user.fullname}\nCurrent topic: {progress.topic.rus.capitalize()}\nLearning language: Russian\n\nProgress: {pb} ({progress.exp / 100}%)\nExp: {f'{progress.exp:,}'.replace(',', '.')} / 10.000</code>"


def get_stats(id):
    stats = get_user_stats(id)
    return f"<code>Статистика на сегодня:\n\nПользователь: {stats['user'].fullname}\nТекущая тематика: {stats['user'].topic.eng}\n\nУроков пройдено: {stats['lessons']}\nПройденных тестов: {stats['tests']}\nПравильных ответов: {stats['correct']}</code>"


def get_bot_stats_today():
    stats = bot_stats(True)
    return f"<code>Статистика бота за сегодня:\n\nУникальных пользователей: {stats['users']}\nПройдено тестирований: {stats['tests']}\nПройдено уроков: {stats['lessons']}\nПравильных ответов: {stats['correct']}</code>"


def get_bot_stats():
    stats = bot_stats()
    return f"<code>Статистика бота за всё время:\n\nУникальных пользователей: {stats['users']}\nПройдено тестирований: {stats['tests']}\nПройдено уроков: {stats['lessons']}\nПравильных ответов: {stats['correct']}</code>"


def word_confirm(data): 
    return f"В бд будет добавлено слово:\n\nТематика: {data['topic']}\n\nRus: {data['rword']}\nRusDef: {data['rdef']}\n\nEng: {data['eword']}\nEngDef: {data['edef']}"