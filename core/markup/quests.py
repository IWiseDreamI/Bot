import random
from core.misc.funcs import inline_kb

from db.models import Quest

from db.queries import get_random_words


def quest_keyboard(quest: Quest, mode: str):
    if(quest.quest_type == "knowledge"): return False
    
    buttons = []
    topic = quest.topic.eng
    qt = quest.quest_type

    if(qt in ["missing", "knowledge", "translate_select"]):
        words = get_random_words(topic, mode, 6)
        answer = quest.eng_answer if mode == "eng" else quest.rus_answer
        if(qt == "translate_select"): answer = quest.rus if mode == "rus" else quest.eng
        answer = answer.capitalize()
        if(not answer in words): words.append(answer)
        if(len(words) > 6): words = words[1:]
        random.shuffle(words)
        buttons = inline_kb(words, "answer")
    
        return buttons

    if(qt == "boolean"):
        answers = ["True", "False"] if mode == "eng" else ["Правда", "Ложь"]
        buttons = inline_kb(answers, "answer")
    
        return buttons


    if(qt == "definition"):
        answers = ["A", "B", "C", "D"]
        buttons = inline_kb(answers, "answer")
    
        return buttons

    return None

def example_quest_kb(quest: Quest, mode: str):
    topic = quest.topic.eng
    qt = quest.quest_type 
    buttons = []


    if(qt in ["missing", "knowledge"]):
        words = get_random_words(topic, mode, 6)
        answer = quest.eng_answer if mode == "eng" else quest.rus_answer
        answer = answer.capitalize()
        if(not answer in words): words.append(answer)
        if(len(words) > 6): words = words[1:]
        random.shuffle(words)
        buttons = inline_kb(words, "example")

    elif(qt == "definition"):
        answers = ["A", "B", "C", "D"]
        buttons = inline_kb(answers, "answer")
 

    return buttons