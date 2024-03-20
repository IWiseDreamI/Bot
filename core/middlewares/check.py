import json
import re
from core.middlewares.ai import check_translate_ai
from core.middlewares.texts import missing
from db.models import Lesson, Quest, Test
from db.queries import add_answer

def check_missing(quest: Quest, mode: str, answer: str):
    correct_answer = quest.eng_answer if mode == "eng" else quest.rus_answer
    quest_text = quest.eng if mode == "eng" else quest.rus 
    answer = missing(quest_text, correct_answer).replace("...", answer.replace("_", " ")).lower()
    correct = quest_text.lower() == answer

    return correct


def check_knowledge(quest: Quest, mode: str, answer: str):
    correct_answer = quest.eng_answer if mode == "eng" else quest.rus_answer
    correct = correct_answer.lower() == answer.lower().replace("_", " ")

    return correct


def check_word(quest: Quest, mode: str, answer: str, question: str):
    correct = False
    correct_answer = quest.eng_answer if mode == "eng" else quest.rus_answer
    variants = question.split(")")[1:]
    variants = list(map(lambda variant: re.findall(r'[^\n]*', variant.strip())[0], variants))
    answers = {"a": 0, "b": 1, "c": 2, "d": 3}
    if(variants[answers[answer]].lower() == correct_answer.lower()): correct = True

    return correct


def check_translate(quest: Quest, mode: str, answer: str):
    print(mode)
    correct_answer = quest.eng if mode == "eng" else quest.rus
    check = check_translate_ai(correct_answer, answer, quest.topic.eng)
    return check


def check_quest(quest: Quest, test: Test, mode: str, answer: str, question=""):
    result = False

    if(quest.quest_type == "missing"): result = check_missing(quest, mode, answer)
    if(quest.quest_type == "knowledge" or quest.quest_type == "boolean"): result = check_knowledge(quest, mode, answer)
    if(quest.quest_type == "definition"): result = check_word(quest, mode, answer, question)
    if(quest.quest_type == "translate"): result = check_translate(quest, mode, answer)
    add_answer(answer, result, quest, test)    

    return result


def check_example(quest: Quest, lesson: Lesson, answer: str, question=""):
    result = False
    qt = quest.quest_type
    if(qt == "missing"): result = check_missing(quest, lesson.mode, answer)
    elif(qt == "knowledge"): result = check_knowledge(quest, lesson.mode, answer)
    elif(qt == "definition"): result = result = check_word(quest, lesson.mode, answer, question)

    return result