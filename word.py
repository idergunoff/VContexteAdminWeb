from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from model import *

router = APIRouter()


class MoveWordRequest(BaseModel):
    word_id: int
    new_order: int
    include_words: bool = False


def _build_fact_icons(word: Word) -> str:
    types = {fact.type for fact in word.facts}
    text_fact = next((fact.fact for fact in word.facts if fact.type == 'text'), '')

    fact_icon = '🤖' if text_fact == '🤖' else ('📜' if text_fact else '')
    photo_icon = '🖼' if 'photo' in types else ''
    pixel_icon = '🖌' if word.pixel else ''

    return ''.join([fact_icon, photo_icon, pixel_icon])


@router.get("/")
async def get_words():
    async with get_session() as session:
        result = await session.execute(select(Word.id, Word.word))
        words = result.all()

        result_u = await session.execute(select(User))
        users = result_u.scalars().all()
    return {"words": [{"id": word_id, "word": word} for word_id, word in words],
            "users": [{"id": user.id, "username": user.username, "tg_id": user.tg_id} for user in users]}


@router.post("/move")
async def move_word(request: MoveWordRequest):
    async with get_session() as session:
        word = await session.get(Word, request.word_id)
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")

        if not word.order or word.order == 0:
            return {"status": "skipped", "reason": "order_zero"}

        max_order_result = await session.execute(select(func.max(Word.order)).where(Word.order != 0))
        max_order = max_order_result.scalar() or 0

        if max_order == 0:
            return {"status": "skipped", "reason": "no_words"}

        new_order = max(1, min(request.new_order, max_order))
        current_order = word.order

        if new_order != current_order:
            if new_order < current_order:
                result = await session.execute(
                    select(Word)
                    .where(
                        Word.order >= new_order,
                        Word.order < current_order,
                        Word.order != 0,
                        Word.id != word.id
                    )
                    .order_by(Word.order)
                )
                for other_word in result.scalars().all():
                    other_word.order += 1
            else:
                result = await session.execute(
                    select(Word)
                    .where(
                        Word.order <= new_order,
                        Word.order > current_order,
                        Word.order != 0,
                        Word.id != word.id
                    )
                    .order_by(Word.order)
                )
                for other_word in result.scalars().all():
                    other_word.order -= 1

            word.order = new_order

        await session.flush()

        response = {"status": "success", "word": {"id": word.id, "order": word.order}}

        if request.include_words:
            result_words = await session.execute(
                select(Word)
                .options(selectinload(Word.facts), selectinload(Word.pixel))
                .where(Word.order != 0)
                .order_by(Word.order)
            )
            words = result_words.scalars().unique().all()
            response["words"] = [
                {
                    "id": item.id,
                    "word": item.word,
                    "order": item.order,
                    "fact": _build_fact_icons(item)
                }
                for item in words
            ]

        return response


@router.get("/{word_id}/delete-check")
async def check_delete_word(word_id: int):
    async with get_session() as session:
        word = await session.get(Word, word_id)
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")

        if word.current:
            return JSONResponse(status_code=400, content={
                "can_delete": False,
                "message": "Нельзя удалить текущее слово",
            })

        if word.played or word.date_play:
            return JSONResponse(status_code=400, content={
                "can_delete": False,
                "message": "Слово уже сыграно и не может быть удалено",
            })

        tryings_count = await session.scalar(
            select(func.count()).select_from(Trying).where(Trying.word_id == word_id)
        )
        if tryings_count and tryings_count > 0:
            return JSONResponse(status_code=400, content={
                "can_delete": False,
                "message": "Слово уже использовалось в попытках и не может быть удалено",
            })

        return {"can_delete": True, "confirmation": f"Точно удалить слово '{word.word}' вместе с контекстом?"}


@router.delete("/{word_id}/delete")
async def delete_word(word_id: int):
    async with get_session() as session:
        word = await session.get(Word, word_id)
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")

        if word.current:
            raise HTTPException(status_code=400, detail="Нельзя удалить текущее слово")

        if word.played or word.date_play:
            raise HTTPException(status_code=400, detail="Слово уже сыграно и не может быть удалено")

        tryings_count = await session.scalar(
            select(func.count()).select_from(Trying).where(Trying.word_id == word_id)
        )
        if tryings_count and tryings_count > 0:
            raise HTTPException(status_code=400, detail="Слово уже использовалось в попытках и не может быть удалено")

        await session.execute(delete(WordFact).where(WordFact.word_id == word_id))
        await session.execute(delete(WordStat).where(WordStat.word_id == word_id))
        await session.execute(delete(HintPixel).where(HintPixel.word_id == word_id))
        await session.execute(delete(HintCrash).where(HintCrash.word_id == word_id))
        await session.execute(delete(HintEmojik).where(HintEmojik.word_id == word_id))
        await session.execute(delete(ResultControl).where(ResultControl.word_id == word_id))
        await session.execute(delete(Duel).where(Duel.word_id == word_id))

        await session.delete(word)

    return {"message": f"Слово '{word.word}' удалено"}
