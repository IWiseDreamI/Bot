import time
from sqlalchemy import BigInteger, ForeignKey, Table, Column, Integer, MetaData, Enum
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import mapped_column, Mapped, relationship, DeclarativeBase
from typing import List

mode = Enum("eng", "rus", name="mode")
quest_type = Enum("translate", "voice", "boolean", "missing", "knowledge", "definition", "translate_select", name="quest_type")

class Base(DeclarativeBase):
    pass

metadata = MetaData()

tests_quests = Table(
    "tests_quests", Base.metadata,
    Column("tests", Integer, ForeignKey("tests.id")),
    Column("quests", Integer, ForeignKey("quests.id")),
)

tests_answers = Table(
    "tests_answers", Base.metadata,
    Column("tests", ForeignKey("tests.id")),
    Column("answers", ForeignKey("answers.id")),
)

lessons_examples = Table(    
    "lessons_examples", Base.metadata,
    Column("lessons", ForeignKey("lessons.id")),
    Column("examples", ForeignKey("examples.id")),
)

lessons_quests = Table(    
    "lessons_quests", Base.metadata,
    Column("lessons", ForeignKey("lessons.id")),
    Column("examples", ForeignKey("quests.id")),
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True) #BIGINT
    username: Mapped[str] = mapped_column(unique=True, nullable=True)
    fullname: Mapped[str]
    mode: Mapped[str] = mapped_column(mode)

    topic: Mapped["Topic"] = relationship()
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))

    created_date: Mapped[int] = mapped_column(default=int(time.time()))


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    eng: Mapped[str] = mapped_column(unique=True)
    rus: Mapped[str] = mapped_column(unique=True)


class Progress(Base):
    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    exp: Mapped[int]

    user: Mapped["User"] = relationship()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    topic: Mapped["Topic"] = relationship()
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    eng: Mapped[str]
    rus: Mapped[str]
    eng_answer: Mapped[str] = mapped_column(nullable=True)
    rus_answer: Mapped[str] = mapped_column(nullable=True)
    quest_type: Mapped[str] = mapped_column(quest_type)
    difficulty: Mapped[int]

    topic: Mapped["Topic"] = relationship()
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    answer: Mapped[str]
    correct:  Mapped[bool]
    mode: Mapped[str] = mapped_column(mode)
    
    test: Mapped["Test"] = relationship()
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))

    quest: Mapped["Quest"] = relationship()
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id"))
    
    created_date: Mapped[int] = mapped_column(default=int(time.time()))


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    mode: Mapped[str] = mapped_column(mode)

    quests: Mapped[List["Quest"]] = relationship(secondary=lambda: tests_quests)
    answers: Mapped[List["Answer"]] = relationship(secondary=lambda: tests_answers)

    user: Mapped["User"] = relationship()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    topic: Mapped["Topic"] = relationship()
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))

    created_date: Mapped[int] = mapped_column(default=int(time.time()))


class Word(Base): 
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    eng: Mapped[str]
    rus: Mapped[str]

    eng_def: Mapped[str] = mapped_column(nullable=True)
    rus_def: Mapped[str] = mapped_column(nullable=True)

    topic: Mapped["Topic"] = relationship()
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    mode: Mapped[str] = mapped_column(mode)

    examples: Mapped[List["Example"]] = relationship(secondary=lambda: lessons_examples)
    quests: Mapped[List["Quest"]] = relationship(secondary=lambda: lessons_quests)

    user: Mapped["User"] = relationship()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    topic: Mapped["Topic"] = relationship()
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    
    created_date: Mapped[int] = mapped_column(default=int(time.time()))


class Example(Base):
    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    eng: Mapped[str]
    rus: Mapped[str]

    word: Mapped["Word"] = relationship()
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"), nullable=True)

    topic: Mapped["Topic"] = relationship()
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
