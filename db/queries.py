import datetime
import random
import re
import time
from sqlalchemy import inspect, select, update
from sqlalchemy.orm import Session

from db.db import sql
from db.models import Answer, Example, Lesson, Progress, User, Topic, Quest, Test, Word

session = Session(sql, expire_on_commit=True)
#######
# GET #
#######

def get_day_time():
    ctime = int(time.time())
    dtime = ctime - ctime % (3600 * 24)
    return dtime

def get_topic(topic_str: str):
    ts = select(Topic).where(Topic.eng == topic_str.capitalize())
    topic = session.execute(ts).first()
    if(topic): topic = topic[0]
    return topic

def get_user(id):
    us = select(User).where(User.id == id)
    user = session.execute(us).first()
    if(user): user = user[0]
    return user

def get_quest(id):
    qs = select(Quest).where(Quest.id == id)
    quest = session.execute(qs).first()
    if(quest): quest = quest[0]
    return quest

def get_word(word):
    ws = select(Word).where(Word.eng == word)
    word = session.execute(ws).first()
    if(word): word = word[0]
    return word

def get_user_progress(id):
    user = get_user(id)
    topic = get_topic(user.topic.eng)

    stmt = select(Progress).where((Progress.user_id == id) & (Progress.topic_id == topic.id))
    progress = session.execute(stmt).first()

    if(progress): progress = progress[0]
    return progress

def get_test(test_id: int):
    ts = select(Test).where(Test.id == test_id)
    test = session.execute(ts).first()
    if(test): test = test[0]
    return test

def select_quests(user: User, count: int):    
    topic = get_topic(user.topic.eng)

    stmt = select(Quest).where(Quest.topic_id == topic.id)
    quests = session.execute(stmt).all()

    quests = list(map(lambda quest: quest[0], quests))
    random.shuffle(quests)
    quests = quests[:count]

    return quests

def select_examples(user: User):    
    topic = get_topic(user.topic.eng)

    stmt = select(Example).where(Example.topic_id == topic.id)
    examples = session.execute(stmt).all()

    examples = list(map(lambda example: example[0], examples))
    random.shuffle(examples)

    return examples

def get_topic_words(topic: str):
    topic = get_topic(topic)

    stmt = select(Word).where(Word.topic_id == topic.id)
    words = session.execute(stmt).all()
    words = list(map(lambda word: word[0], words))

    return words

def quest_word(quest: Quest):
    qt = quest.quest_type
    word = None

    if(qt in ["missing", "knowledge"]): 
        word_stmt = select(Word).where(Word.eng == quest.eng_answer.capitalize())
        word = session.execute(word_stmt).first()
    
    elif(qt == "definition"):
        word_stmt = select(Word).where(Word.eng == quest.eng.capitalize())
        word = session.execute(word_stmt).first()

    return word[0] if word else None

def get_examples_quests(examples):
    quests_examples = []

    words = []
    for example in examples: words.append(example.word_id)

    statement = select(Quest).where(Quest.topic_id == examples[0].topic_id)
    quests = session.execute(statement).all()
    quests = list(map(lambda quest: quest[0], quests))

    for quest in quests:
        word = quest_word(quest)
        if(word is None): continue
        if(word.id in words):
            example = list(filter(lambda example: example.word_id == word.id, examples))[0]
            quests_examples.append([quest, example])

    random.shuffle(quests_examples)
    quests_examples = quests_examples[:10]

    return quests_examples

def get_random_words(topic: str, mode: str, count: int):
    words = get_topic_words(topic)
    random.shuffle(words)
    words = words[:count]
    result = []
    for word in words:
        if(mode == "eng"): result.append(word.eng)
        else: result.append(word.rus)
    
    return result

def get_definitions(topic: str, mode: str, count: int):
    words = get_topic_words(topic)
    words = list(filter(lambda word: word.eng_def is not None, words))
    random.shuffle(words)
    words = words[:count]
    result = []

    for word in words:
        if(mode == "eng"): result.append(word.eng_def)
        else: result.append(word.rus_def)
    
    return result

def check_test_success(test: Test):
    test_len = len(test.answers)
    counter = 0
    for answer in test.answers:
        if(type(answer) is list): answer = answer[0]
        if(answer.correct): counter += 1

    return counter >= test_len * 0.7

########
# POST #
########

def add_user(user):
    topic = get_topic(user["topic"])

    if(get_user(user["user_id"]) != None): return "User already exist."

    user = User(
        id=user["user_id"], username=user["username"],
        fullname=user["fullname"], mode=user["mode"],
        topic=topic, topic_id=topic.id
    )

    progress = Progress(
        user = user, user_id = user.id,
        topic=topic, topic_id=topic.id, exp = 0
    )

    session.add(user)

    session.flush()
    session.commit()

    session.add(progress)

    session.flush()
    session.commit()



def generate_test(user_id: int):
    user = get_user(user_id)

    quests = select_quests(user, 10)

    generated = Test(
        user_id=user.id, user=user, mode = user.mode,
        topic_id=user.topic.id, topic=user.topic, 
    )

    for quest in quests: generated.quests.append(quest)

    session.add(generated)

    session.flush()
    session.commit()

    return generated


def generate_lesson(user_id: int):
    user = get_user(user_id)

    examples = select_examples(user)
    data = get_examples_quests(examples)

    generated = Lesson(
        user_id=user.id, user=user, mode = user.mode,
        topic_id=user.topic.id, topic=user.topic, 
    )

    for item in data: 
        generated.quests.append(item[0])
        generated.examples.append(item[1])

    session.add(generated)

    session.commit()

    return generated




def add_answer(answer: str, correct: bool, quest: Quest, test: Test):
    if(correct): add_progress(test)

    new_answer = Answer(
        answer=answer, correct=correct,
        quest=quest, quest_id=quest.id,
        test=test, test_id=test.id,
        mode=test.mode
    )

    test.answers.append(new_answer)

    session.add(new_answer)
    session.add(test)

    session.commit()

    return new_answer


def add_progress(test: Test):
    test_statement = update(Progress).where((Progress.user_id == test.user_id) & (Progress.topic_id == test.topic_id)).values(exp=Progress.exp + 50)
    session.execute(test_statement)

def add_questions(questions):
    topic = get_topic(questions[0]["topic"])

    for quest in questions:
        if (quest["quest_type"] == "missing"):
            quest["rus"] = re.sub(r"_+", quest["rus_answer"], quest["rus"])
            quest["eng"] = re.sub(r"_+", quest["eng_answer"], quest["eng"])

        session.add(Quest(
            eng=quest["eng"], rus=quest["rus"],
            eng_answer=quest.get("eng_answer"), rus_answer=quest.get("rus_answer"),
            quest_type=quest["quest_type"], difficulty=quest["difficulty"],
            topic=topic, topic_id=topic.id, 
        ))

    session.flush()
    session.commit()


def add_word(word):
    topic = get_topic(word['topic'])

    session.add(Word(
        eng=word["eword"], rus=word["rword"],
        eng_def=word.get("edef"), rus_def=word.get("rdef"),
        topic=topic, topic_id=topic.id, 
    ))
    
    session.add(Quest(
        eng=word["eword"], rus=word["rword"],
        eng_answer=word.get("edef"), rus_answer=word.get("rdef"),
        quest_type="definition", difficulty="1",
        topic=topic, topic_id=topic.id, 
    ))

    session.add(Quest(
        eng=word["eword"], rus=word["rword"],
        quest_type="voice", difficulty="2",
        topic=topic, topic_id=topic.id, 
    ))

    session.commit()

#########
# Stats #
#########

def get_topic_stats(topic: str, today: bool = False):
    topic = get_topic(topic)
    dtime = get_day_time()
    users = []; correct = []

    if(today):
        lessons = select(Lesson).where((Topic.id == topic.id) & (Lesson.created_date >= dtime))
        tests = select(Test).where((Topic.id == topic.id) & (Test.created_date >= dtime))
    
    else: 
        lessons = select(Lesson).where(Lesson.topic_id == topic.id)
        tests = select(Test).where(Test.topic_id == topic.id)

    lessons = list(map(lambda lesson: lesson[0], session.execute(lessons).all()))
    tests = list(map(lambda test: test[0], session.execute(tests).all()))

    for lesson in lessons: users.append(lesson.user_id)
    for test in tests: users.append(test.user_id)

    for test in tests:
        for answer in test.answers:
            if(answer.correct): correct.append(answer) 

    data = {
        "users": 0,
        "tests": 0,
        "lessons": 0,
        "correct": 0,
    }

    data["users"] = len(list(set(users)))
    data["tests"] = len(tests)
    data["lessons"] = len(lessons)
    data["correct"] = len(correct)

    return data



def get_user_stats(id):
    user = get_user(id)
    dtime = get_day_time()

    correct = []

    data = {
        "user": user, 
        "tests": 0,
        "lessons": 0, 
        "correct": 0
    }

    lessons = select(Lesson).where((Lesson.user_id == id) & (Lesson.created_date >= dtime))
    tests = select(Test).where((Test.user_id == id) & (Test.created_date >= dtime))
    lessons = list(map(lambda lesson: lesson[0], session.execute(lessons).all()))
    tests = list(map(lambda test: test[0], session.execute(tests).all()))

    data["lessons"] = len(lessons); data["tests"] = len(tests)
    
    for test in tests:
        for answer in test.answers:
            if(answer.correct): correct.append(answer)

    data["correct"] = len(correct)

    return data


def bot_stats(today: bool = False):
    dtime = get_day_time()
    users = []; correct = []
    lesson = []; tests = []
    data = {
        "users": 0,
        "tests": 0,
        "lessons": 0,
        "correct": 0,
    }

    if(today):
        lessons = select(Lesson).where(Lesson.created_date >= dtime)
        tests = select(Test).where(Test.created_date >= dtime)
    else: 
        lessons = select(Lesson)
        tests = select(Test)
        
    lessons = list(map(lambda lesson: lesson[0], session.execute(lessons).all()))
    tests = list(map(lambda test: test[0], session.execute(tests).all()))

    for test in tests:
        for answer in test.answers:
            if(answer.correct): correct.append(answer) 

    for lesson in lessons: users.append(lesson.user_id)
    for test in tests: users.append(test.user_id)

    data["users"] = len(list(set(users)))
    data["tests"] = len(tests)
    data["lessons"] = len(lessons)
    data["correct"] = len(correct)

    return data


def bot_users_stats(today: bool = False):
    dtime = get_day_time()
    users = []
    lesson = []; tests = []
    users_data = {}
    data = {
        "users": 0,
        "tests": 0,
        "lessons": 0,
        "users_data": {},
        "users_count": 0,
    }

    if(today):
        lessons = select(Lesson).where(Lesson.created_date >= dtime)
        tests = select(Test).where(Test.created_date >= dtime)
    
    else: 
        lessons = select(Lesson)
        tests = select(Test)
        
    lessons = list(map(lambda lesson: lesson[0], session.execute(lessons).all()))
    tests = list(map(lambda test: test[0], session.execute(tests).all()))

    for lesson in lessons: 
        if(users_data.get(lesson.user_id) is None): 
            users_data[lesson.user_id] = {}
            users_data[lesson.user_id]["lessons"] = 0

        users_data[lesson.user_id]["lessons"] += 1    
        users.append(lesson.user_id)

    for test in tests: 
        if(users_data.get(test.user_id) is None): 
            users_data[test.user_id] = {}
            users_data[test.user_id]["tests"] = 0

        if(not users_data[test.user_id].get("tests")): 
            users_data[test.user_id]["tests"] = 0
            
        users_data[test.user_id]["tests"] += 1
        users.append(test.user_id)

    users_id = list(set(users))
    users = []

    data["users_count"] = len(users_id)
    data["tests"] = len(tests)
    data["lessons"] = len(lessons)

    for user_id in users_id:
        user = select(User).where(User.id == int(user_id))
        user = session.execute(user).first()
        users.append(user[0])

    data["users"] = users

    for user_data in users_data:
        for user in users:
            if(int(user_data) == user.id):
                users_data[user.id]["name"] = user.username
                if(users_data[user.id].get("lessons") is None): users_data[user.id]["lessons"] = 0
                if(users_data[user.id].get("tests") is None): users_data[user.id]["tests"] = 0

    data["users_data"] = users_data

    return data

#########
# PATCH #
#########

def change_language(id) -> User:
    user = get_user(id)
    mode = "rus" if user.mode == "eng" else "eng"
    user_stmt = update(User).where(User.id == int(id)).values(mode=mode)
    session.execute(user_stmt)
    return get_user(id)

def change_topic(id, topic) -> User:
    user = get_user(id)
    topic = get_topic(topic)
    user_stmt = update(User).where(User.id == int(id)).values(topic_id=topic.id)
    
    progress = Progress(
        user = user, user_id = user.id,
        topic=topic, topic_id=topic.id, exp = 0
    )

    session.add(progress)
    
    session.commit()
    session.execute(user_stmt)

    return get_user(id)


def edit_quest(quest_id: int, quest_fields):
    qs = update(Quest).where(Quest.id == int(quest_id)).values(
        eng = quest_fields["eng"], rus = quest_fields["rus"],
        eng_answer = quest_fields["eng_answer"], rus_answer = quest_fields["rus_answer"],
    )

    session.execute(qs)
    return get_quest(quest_id)


def edit_word(word_id: int, word_fields):
    w_stmt = select(Word).where(Word.id == int(word_id))
    words = session.execute(w_stmt).first()

    ws = update(Word).where(Word.id == int(word_id)).values(
        eng = word_fields["eng"], rus = word_fields["rus"],
        eng_def = word_fields["eng_def"], rus_def = word_fields["rus_def"],
    )

    session.execute(ws)
    return get_word(word_fields["eng"])


def get_topic_random_word(topic) -> Word:
    topic = get_topic(topic)
    user_stmt = select(Word).where(Word.topic_id == topic.id)
    words = session.execute(user_stmt).all()
    words = list(map(lambda word: word[0], words))
    random.shuffle(words)

    return words[0]