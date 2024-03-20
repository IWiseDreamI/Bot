import datetime
import random
import re
import time
from sqlalchemy import inspect, select, update
from sqlalchemy.orm import Session

from db.db import sql
from db.models import Answer, Example, Lesson, Progress, User, Topic, Quest, Test, Word

session = Session(sql, expire_on_commit=True)

def get_topic(topic_str: str):
    topic_statement = select(Topic).where(Topic.eng == topic_str.capitalize())
    topic = session.execute(topic_statement).first()
    if(topic): topic = topic[0]
    return topic


def get_user(id):
    user_statement = select(User).where(User.id == id)
    user = session.execute(user_statement).first()
    if(user): user = user[0]
    return user


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


def get_user_progress(id):
    user = get_user(id)
    print(user.fullname)
    topic = get_topic(user.topic.eng)

    statement = select(Progress).where((Progress.user_id == id) & (Progress.topic_id == topic.id))
    progress = session.execute(statement).first()

    if(progress): progress = progress[0]
    print(progress.user.fullname)
    return progress


def select_quests(user: User, count: int):    
    topic = get_topic(user.topic.eng)

    statement = select(Quest).where(Quest.topic_id == topic.id)
    quests = session.execute(statement).all()

    quests = list(map(lambda quest: quest[0], quests))
    random.shuffle(quests)
    quests = quests[:count]

    return quests


def select_examples(user: User):    
    topic = get_topic(user.topic.eng)

    statement = select(Example).where(Example.topic_id == topic.id)
    examples = session.execute(statement).all()

    examples = list(map(lambda example: example[0], examples))
    random.shuffle(examples)

    return examples


def get_topic_words(topic: str):
    topic = get_topic(topic)

    statement = select(Word).where(Word.topic_id == topic.id)
    words = session.execute(statement).all()
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


def get_test(test_id: int):
    test_statement = select(Test).where(Test.id == test_id)
    test = session.execute(test_statement).first()
    if(test): test = test[0]
    return test


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

    session.flush()
    session.commit()

    return new_answer


def add_progress(test: Test):
    test_statement = update(Progress).where(Progress.user_id == test.user_id and Progress.topic_id == test.topic_id).values(exp=Progress.exp + 50)
    session.execute(test_statement)


def check_test_success(test: Test):
    test_len = len(test.answers)
    counter = 0
    for answer in test.answers:
        if(type(answer) is list): answer = answer[0]
        if(answer.correct): counter += 1

    return counter >= test_len * 0.7


def get_general_info():
    data = {"tests_num": "", "answers_num": "", "success_tests": "", "correct_answer": ""}
    
    tests_stmt = select(Test).where(Test.created_date >= time.time() - 24 * 3600)
    answers_stmt = select(Answer).where(Answer.created_date >= time.time() - 24 * 3600)
    
    tests = session.execute(tests_stmt).all()
    answers = session.execute(answers_stmt).all()
    
    data["tests_num"] = len(tests)
    data["answers_num"] = len(tests)

    data["success_tests"] = len(list(filter(lambda test: check_test_success(test[0]), tests)))
    data["correct_answers"] = len(list(filter(lambda answer: answer[0].correct, answers)))

    return data


def get_user_info(id):
    pass


def change_language(id) -> User:
    user = get_user(id)
    mode = "rus" if user.mode == "eng" else "eng"
    user_stmt = update(User).where(User.id == int(id)).values(mode=mode)
    session.execute(user_stmt)
    return get_user(id)


def change_topic(id, topic) -> User:
    topic = get_topic(topic)
    user_stmt = update(User).where(User.id == int(id)).values(topic_id=topic.id)
    session.execute(user_stmt)
    return get_user(id)


def get_topic_random_word(topic) -> Word:
    topic = get_topic(topic)
    user_stmt = select(Word).where(Word.topic_id == topic.id)
    words = session.execute(user_stmt).all()
    words = list(map(lambda word: word[0], words))
    random.shuffle(words)

    return words[0]


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