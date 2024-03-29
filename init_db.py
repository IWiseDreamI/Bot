from sqlalchemy import select

from db.db import sql
from db.models import Base, Quest, Topic, Word, Example

from core.data.env import topics, data
from db.queries import get_topic, session

def init_topics():
    for topic in topics: session.add(Topic(eng=topic[0], rus=topic[1]))
    session.commit()


def init_words():
    for topic in data: 
        topic = get_topic(topic)
        for word in data[topic.eng.lower()]["words"]:
            session.add(Word(
                eng=word["eng"], rus=word["rus"],
                eng_def=word.get("eng_def"), rus_def=word.get("rus_def"),
                topic=topic, topic_id=topic.id
            ))

    session.flush()
    session.commit()


def init_quests():
    for topic in data:
        topic = get_topic(topic)
        for quest in data[topic.eng.lower()]["questions"]:
            session.add(Quest(
                eng=quest["eng"], rus=quest["rus"],
                eng_answer=quest.get("eng_answer"), rus_answer=quest.get("rus_answer"),
                quest_type=quest["quest_type"], difficulty=quest["difficulty"],
                topic=topic, topic_id=topic.id, 
            ))

    session.commit()


def init_examples():
    word_stmt = select(Word)
    words = session.execute(word_stmt).all()
    words = list(map(lambda word: word[0], words))
    words = list(filter(lambda word: word.eng_def, words))

    for word in words: 
        session.add(Example(
            eng=f"{word.eng} ({word.rus}) - {word.rus_def}",
            rus=f"{word.rus} ({word.eng}) - {word.eng_def}",
            topic=word.topic, topic_id=word.topic.id,
            word=word, word_id=word.id
        ))

    session.flush()
    session.commit()


def init_sentence_quests():
    for topic in data:
        topic = get_topic(topic)

        statement = select(Word).where(Word.topic_id == topic.id)
        words = session.execute(statement).all()
        words = list(map(lambda word: word[0], words))
        words = list(filter(lambda word: word.eng_def is not None, words))
        
        for word in words:
            session.add(Quest(
                eng=word.eng, rus=word.rus,
                eng_answer=word.eng_def, rus_answer=word.rus_def,
                quest_type="definition", difficulty="1",
                topic=topic, topic_id=topic.id, 
            ))
            session.add(Quest(
                eng=word.eng, rus=word.rus,
                quest_type="voice", difficulty="2",
                topic=topic, topic_id=topic.id, 
            ))

    session.commit()


def init_db():
    Base.metadata.drop_all(sql)
    Base.metadata.create_all(sql)        
    init_topics()
    init_quests()
    init_words()
    init_examples()
    init_sentence_quests()

if __name__ == '__main__':
    init_db()