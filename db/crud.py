from doctest import Example
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from db.models import Answer, Lesson, Progress, Quest, Test, Topic, User, Word

models = {
    "user": User,
    "topic": Topic,
    "progress": Progress,
    "quest": Quest,
    "answer": Answer,
    "test": Test,
    "word": Word,
    "lesson": Lesson,
    "example": Example
}

class CRUD: 

    async def get_all(self, model: str):
        pass