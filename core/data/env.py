from math import ceil
import os
import json

from db.models import Progress
from db.queries import bot_stats, bot_users_stats, get_topic, get_topic_stats, get_user_stats

path = f"{os.path.dirname(os.path.abspath(__file__))}/data.json"
data = {}

with open(path, "r") as file: data = json.loads(file.read()) 

topics = {
    
    "wrestling": {
        "eng": "Wrestling",
        "rus": "Борьба",
        "free-style": {
            "eng": "Free-style wrestling",
            "rus": "Вольная борьба"
        },
        "greco-roman": {
            "eng": "Greco-roman wrestling",
            "rus": "Греко-римская борьба"
        },
        "kurash": {
            "eng": "Kurash",
            "rus": "Кураш"
        },
        "khapsagai": {
            "eng": "Khapsagai",
            "rus": "Хапсагай"
        },
        "alysh": {
            "eng": "Alysh",
            "rus": "Алыш"
        },
    },

    "martial arts": {
        "eng": "Matrial arts",
        "rus": "Единоборства",
        "box": {
            "eng": "Box",
            "rus": "Бокс"
        },
        "judo": {
            "eng": "Judo",
            "rus": "Дзюдо"
        },
        "kickboxing": {
            "eng": "Kickboxing",
            "rus": "Кикбоксинг"
        },
        "sambo": {
            "eng": "Sambo",
            "rus": "Самбо"
        },
        "taekwondo": {
            "eng": "Taekwondo",
            "rus": "Тэкводно"
        },
    },
    "with a ball": {
        "eng": "With a ball",
        "rus": "С мячом",
        "basketball": {
            "eng": "Basketball",
            "rus": "Баскетбол"        
        },
        "volleyball": {
            "eng": "Volleyball",
            "rus": "Волейбол"        
        },
        "table_tennis": {
            "eng": "Table tennis",
            "rus": "Настольный теннис"        
        },
        "mini_football": {
            "eng": "Mini football",
            "rus": "Минифутбол"        
        },
    },

    "shooting": {
        "eng": "Shooting",
        "rus": "Стрельба",
        "shooting": {
            "eng": "Shooting",
            "rus": "Пулевая стрельба"
        },
        "trap_shooting": {
            "eng": "Trap shooting",
            "rus": "Стрельба по тарелочкам"
        },
        "archery": {
            "eng": "Archery",
            "rus": "Стрельба из лука"
        }
    },
    "yakut": {
        "eng": "Yakut",
        "rus": "Якутские",
        "yakut_jumps": {
            "eng": "Yakut jumps",
            "rus": "Якутские прыжки"
        },
        "mas_wrestling": {
            "eng": "Mas wrestling",
            "rus": "Мас рестлинг"
        }
    },
    "desktop": {
        "eng": "Desktop",
        "rus": "Настольные",
        "chess": {
            "eng": "Chess",
            "rus": "Шахматы",
        },
        "go": {
            "eng": "Go game",
            "rus": "Го"
        }
    },
    "athletic": {
        "eng": "Athletic",
        "rus": "Атлетические",
        "swimming": {
            "eng": "Swimming",
            "rus": "Плавание"
        },
        "rock_climbing": {
            "eng": "Rock climbing",
            "rus": "Скалолазание"
        },
        "athletics": {
            "eng": "Athletics",
            "rus": "Легкая атлетика"
        }
    },
    "artistic": {
        "eng": "Artistic",
        "rus": "Артистичные",
        "dance_sport": {
            "eng": "Dance sport",
            "rus": "Танцевальный спорт"
        },
        "rhytmic_gymnastics": {
            "eng": "Rhytmic gymnastics",
            "rus": "Художественная гимнастика"
        }
    }
}

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
    },
    "translate_select": {
        "eng": "Select the correct translation option",
        "rus": "Выберите правильный вариант перевода"
    }
}

text = {
    "greeting": {
        "rus": "Hi! 🌐 Welcome to our language bot.\n\nHere you can improve your Russian in sports!\n\nTo start learning, click on \"Study\"\nTo start testing, click on \"Test\"\n\nTo fully complete a course in one of the topics you need 10,000 points.You can view your points by clicking on \"Progress\". Enjoy!",
        "eng": "Привет! 🌐 Добро пожаловать в нашего языкового бота.\n\nЗдесь ты можешь подтянуть свой английский в спортивной сфере!\n\nЧтобы начать изучение материала - нажми кнопку \"уроки\"\nЧтобы начать тестирование - нажми \"Тестирование\"\n\nЧтобы полностью завершить курс по одной из тематик нужно набрать 10.000 очков.\nСвои очки ты можешь посмотреть нажав на \"Прогресс\"\n\nПриятного использования!"
    },
    "options": {
        "rus": "<code>Available options:\n\n</code>/change_mode<code> - Switch the language of study\n</code>/change_topic<code> - Change the topic of the assignments\n</code>/stats<code> - Statistics</code>",
        "eng": "<code>Доступные опции:\n\n</code>/change_mode<code> - Переключить язык изучения\n</code>/change_topic<code> - Сменить тематику заданий\n</code>/stats<code> - Статистика</code>"    
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
        "rus": "Контакты:\nВасильев Василий Васильевич\nТелефон: +7 (965) 993-99-98\n",
        "eng": "Contacts:\nВасильев Василий Васильевич\nPhone: +7 (965) 993-99-98\n"
    },
    "unfinished_lesson": {
        "rus": "Complete the lesson to continue 🔚.\nOr use the /end_lesson command to end it.",
        "eng": "Завершите урок, чтобы продолжить 🔚.\nИли воспользуйтесь командой /end_lesson чтобы его завершить."
    },
    "admin_options": "<code>Доступные опции:\n\n</code>/change_mode<code> - Переключить язык изучения\n</code>/change_topic<code> - Сменить тематику заданий</code>\n/stats<code> - Ваша статистика</code>\n/day_stats<code> - Статистика бота за день</code>\n/all_stats<code> - Статистика за всё время</code>\n/add_word<code> - Добавить слово</code>\n/add_quest<code> - Добавить вопрос</code>\n/gen_quest<code> - Сгенерировать вопрос</code>\n/edit_quest<code> - Изменить вопрос</code>\n/edit_word<code> - Изменить слово</code>\n/all_users_stats<code> - Общая статистика с пользователями\n</code>/topic_stats<code> - Статистика по тематике\n</code>/today_topic_stats<code> - Статистика по тематике за сегодня</code>"        
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


def get_topic_statistic(topic: str):
    stats = get_topic_stats(topic)
    topic = get_topic(topic)
    return f"<code>Статистика по теме {topic.rus}:\n\nУникальных пользователей: {stats['users']}\nПройдено тестирований: {stats['tests']}\nПройдено уроков: {stats['lessons']}\nПравильных ответов: {stats['correct']}</code>"


def get_today_topic_statistic(topic: str):
    stats = get_topic_stats(topic, True)
    topic = get_topic(topic)
    return f"<code>Статистика по теме {topic.rus} за сегодня:\n\nУникальных пользователей: {stats['users']}\nПройдено тестирований: {stats['tests']}\nПройдено уроков: {stats['lessons']}\nПравильных ответов: {stats['correct']}</code>"


def word_confirm(data): 
    return f"В бд будет добавлено слово:\n\nТематика: {data['topic']}\n\nРусский: {data['rword']}\nОпределение: {data['rdef']}\n\nEnglish: {data['eword']}\nDefinition: {data['edef']}"

def get_bot_users_stats():
    data = bot_users_stats()
    text = f"<code>Статистика бота за всё время:\n\nУникальных пользователей: {data['users_count']}\nПройдено тестирований: {data['tests']}\nПройдено уроков: {data['lessons']}\n\n</code>"

    for user_data in data["users_data"]:
        text += f"<code>{data['users_data'][user_data]['name']} - Тестов: {data['users_data'][user_data]['tests']}; Уроков: {data['users_data'][user_data]['lessons']};\n</code>"

    return text