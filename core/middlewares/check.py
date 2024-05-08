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

    user_answer = variants[answers.get(answer)] if answers.get(answer) else "False"    
    if(user_answer.lower() == correct_answer.lower()): correct = True

    return correct


def check_translate(quest: Quest, mode: str, answer: str):
    check = False
    correct_answer = quest.eng if mode == "eng" else quest.rus
    if(quest.quest_type == "translate_select"): correct_answer = quest.eng if mode == "rus" else quest.rus
    if(len(answer.split(" ")) > 2): check = check_translate_ai(correct_answer, answer, quest.topic.eng)
    else: 
        counter = 0
        min_len = len(answer) if(len(answer) < len(correct_answer)) else len(correct_answer)
        for i in range(min_len): counter += 1 if(answer[i] == correct_answer[i]) else 0
        if(counter > len(correct_answer) * 0.7): check = True

    return check


def check_voice(quest: Quest, mode: str, answer: str):
    check = False
    if(not answer): return False
    correct = quest.eng.replace(" ", "").lower() if mode == "eng" else quest.rus.replace(" ", "").lower()
    answer = answer.replace(".", "").replace(",", "").replace(" ", "").lower()
    min_len = len(answer) if len(answer) < len(correct) else len(correct)
    counter = 0

    for i in range(min_len): counter += 1 if(answer[i] == correct[i]) else 0

    if(counter > len(correct) * 0.6): check = True
    if(answer in correct): check = True

    return check


def check_quest(quest: Quest, test: Test, mode: str, answer: str, question=""):
    result = False
    qt = quest.quest_type
    if(answer is None): return result
    if(qt == "missing"): result = check_missing(quest, mode, answer)
    if(qt in ["knowledge", "boolean"]): result = check_knowledge(quest, mode, answer)
    if(qt == "definition"): result = check_word(quest, mode, answer, question)
    if(qt in ["translate", "translate_select"]): result = check_translate(quest, mode, answer)
    if(qt == "voice"): result = check_voice(quest, mode, answer)
    add_answer(answer, result, quest, test)    

    return result


def check_example(quest: Quest, lesson: Lesson, answer: str, question=""):
    result = False
    qt = quest.quest_type
    if(qt == "missing"): result = check_missing(quest, lesson.mode, answer)
    elif(qt == "knowledge"): result = check_knowledge(quest, lesson.mode, answer)
    elif(qt == "definition"): result = result = check_word(quest, lesson.mode, answer, question)

    return result