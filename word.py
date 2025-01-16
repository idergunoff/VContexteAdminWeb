from fastapi import APIRouter, Depends
from sqlalchemy.testing.suite.test_reflection import users

from model import *

router = APIRouter()


@router.get("/")
async def get_words():
    async with get_session() as session:
        result = await session.execute(select(Word.id, Word.word))
        words = result.all()

        result_u = await session.execute(select(User))
        users = result_u.scalars().all()
    return {"words": [{"id": word_id, "word": word} for word_id, word in words],
            "users": [{"id": user.id, "username": user.username, "tg_id": user.tg_id} for user in users]}