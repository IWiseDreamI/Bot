import random
import re
from typing import TypedDict
from db.models import Quest, Test
from core.data.env import quest_type_text
from db.queries import get_definitions


def missing(quest: str, answer: str):
    answer = re.compile(re.escape(answer), re.IGNORECASE)
    quest = answer.sub("...", quest)

    return quest


def word(quest: Quest, mode: str):
    variants = get_definitions(quest.topic.eng, mode, 4)
    answer = quest.eng_answer if mode == "eng" else quest.rus_answer
    if(not answer in variants): variants.append(answer)
    if(len(variants) > 4): variants = variants[1:] 
    random.shuffle(variants)

    termin = quest.eng if mode == "eng" else quest.rus

    return f"{termin} \n\n A) {variants[0]}\n\nB) {variants[1]}\n\nC) {variants[2]}\n\nD) {variants[3]}"

    
def get_quest(quest: Quest, mode: str):
    qt = quest.quest_type 
    if(mode == "rus"):
        if(qt == "definition"): return word(quest, mode)
        if(qt == "translate"): return list(set([quest.eng, quest.rus]))[0]
        if(qt != "missing"): return quest.rus
        else: return missing(quest.rus, quest.rus_answer)

    if(mode == "eng"): 
        if(qt == "definition"): return word(quest, mode)
        if(qt in "translate" ): return list(set([quest.eng, quest.rus]))[0]
        if(qt != "missing"): return quest.eng
        else: return missing(quest.eng, quest.eng_answer)


def quest_text(quest: Quest, mode: str, current: int):
    question = get_quest(quest, mode)
    question_head = quest_type_text[quest.quest_type][mode]
    return f"<b>#{current + 1} {question_head}</b>\n\n{question}"


def get_result(test: Test):
    counter = 0
    correct = 0
    result = ""

    for i in range(len(test.answers)):
        answer = test.answers[i]
        if(answer.correct): correct += 1     
        emojis = ["\U0001F3AF", "❗️"]
        result += f"#{counter+1} Ваш ответ: {answer.answer.capitalize().replace('_', ' ')} {emojis[0] if answer.correct else emojis[1]}\n"
        counter += 1


    return f"<code>Правильных ответов {correct} из 10:\n\n{result}</code>"


def get_lesson_text(lesson):
    result = ""

    for example in lesson.examples:
        text = example.eng if lesson.user.mode == "eng" else example.rus
        result += f"{text}\n\n"

    return result


def get_example_text(quest: Quest, mode: str):
    answer = quest.eng_answer if mode == "eng" else quest.rus_answer
    quest_text = quest.eng if mode == "eng" else quest.rus
    
    if(quest.quest_type == "missing"): quest_text = missing(quest_text, answer)
    if(quest.quest_type == "definition"): return word(quest, mode)

    return quest_text


def get_new_quests(data):
    counter = 1
    result = "<code>"
    result += "Сгенерированные вопросы:\n\n"
    
    for quest in data:
        if(type(quest) is str or quest is None): return False
        if not(quest.get('eng') and quest.get('rus') and quest.get('eng_answer') and quest.get('rus_answer')): return False
        result += f"Вопрос #{counter} | Тип вопроса: {quest.get('quest_type').capitalize()}\n\n🇬🇧 English: {quest.get('eng')}\nAnswer: {quest.get('eng_answer')}\n\n🇷🇺 Русский: {quest.get('rus')}\nОтвет: {quest.get('rus_answer')}\n\n\n"
        counter += 1
    result += "</code>"
    return result