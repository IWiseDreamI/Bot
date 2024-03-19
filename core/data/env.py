from math import ceil
import os
import json

from db.models import Progress

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

admin_commands = f"<code>Доступные команды: \n\n</code>/stats<code> - Отображение общей статистики бота за день.\n</code>/info<code> \"username\" - Отображение прогресса пользователя.\n</code>/add_word<code> - Добавить слово в бд.\n</code>/add_question<code> - Добавить вопрос.</code>"
user_commands = f"<code>Доступные команды: \n\n/stats - Отображение вашей статистики за день.</code>"

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
        "eng": "Привет! 🌐 Добро пожаловать в нашего языкового бота.\n\nЗдесь ты можешь подтянуть свой английский в спортивной сфере!\n\nЧтобы начать изучение материала - нажми кнопку \"Обучение\"\nЧтобы начать тестирование - нажми \"Тестирование\"\n\nЧтобы полностью завершить курс по одной из тематик нужно набрать 10.000 очков.\nСвои очки ты можешь посмотреть нажав на \"Прогресс\"\n\nПриятного использования!"
    },
    "options": {
        "rus": "<code>Available options:\n\n</code>/change_mode<code> - Switch the language of study\n</code>/change_topic<code> - Change the topic of the assignments</code>",
        "eng": "<code>Доступные опции:\n\n</code>/change_mode<code> - Переключить язык изучения\n</code>/change_topic<code> - Сменить тематику заданий</code>"    
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
        "rus": "Complete the previous test to continue.\nOr use the /end_test command to end it.",
        "eng": "Завершите предыдущее тестирование, чтобы продолжить.\nИли воспользуйтесь командой /end_test чтобы его завершить."
    },
    "contacts": {
        "rus": "Контакты",
        "eng": "Контакты"
    },
    "unfinished_lesson": {
        "rus": "Complete the previous test to continue 🔚.\nOr use the /end_lesson command to end it.",
        "eng": "Завершите обучение, чтобы продолжить 🔚.\nИли воспользуйтесь командой /end_lesson чтобы его завершить."
    },
}

commands_list = ["тестирование", "обучение", "/end_test", "/end_lesson", "прогресс", "опции", "контакты"]

def get_progress(progress: Progress):
    pb = "[" + "-" * 20 + "]"
    gp = ceil(ceil(progress.exp / 100) / 5)
    um = progress.user.mode

    while(gp > 0): 
        pb = pb.replace("-", "@", 1)
        gp -= 1

    if(um == "eng"): return f"<code>Пользователь: {progress.user.fullname}\nВыбранная тематика: {progress.topic.rus.capitalize()}\nЯзык изучения: Английский\n\nПрогресс: {pb} - ({progress.exp / 100}%)\nОчков опыта: {f'{progress.exp:,}'.replace(',', '.')} / 10.000</code>"
    else: return f"Current topic: {progress.topic.rus.capitalize()}\n\nPoints: {progress.exp}"