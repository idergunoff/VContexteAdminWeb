import asyncio
from email.policy import default

from sqlalchemy import (create_engine, Column, Integer, BigInteger, String, Float, Boolean, DateTime,
                        ForeignKey, Date, Text, text, literal_column, or_, func, desc)
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager

from connect import AsyncSessionLocal

@asynccontextmanager
async def get_session():
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger)
    username = Column(String)
    date_register = Column(DateTime)
    date_last = Column(DateTime)
    score = Column(Integer, default=0)

    tryings = relationship('Trying', back_populates='user')
    remind = relationship('UserRemind', back_populates='user')
    block = relationship('UserBlock', back_populates='user')
    ttt = relationship('TryingTopTen', back_populates='user')
    coin = relationship('UserCoin', back_populates='user')
    transaction = relationship('UserTransaction', back_populates='user')
    every_day = relationship('UserEveryDay', back_populates='user')
    alpha = relationship('UserAlpha', back_populates='user')
    referral_code = relationship('ReferralCode', back_populates='user')
    referral_user = relationship('ReferralUser', back_populates='user')


class UserCoin(Base):
    __tablename__ = 'user_coin'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    coin = Column(Integer, default=0)

    user = relationship('User', back_populates='coin')


class UserTransaction(Base):
    __tablename__ = 'user_transaction'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    amount = Column(Integer)
    description = Column(String)
    date_trans = Column(DateTime)

    user = relationship('User', back_populates='transaction')


class UserBlock(Base):
    __tablename__ = 'user_block'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))

    user = relationship('User', back_populates='block')


class Word(Base):
    __tablename__ = 'word'

    id = Column(Integer, primary_key=True)
    word = Column(String)
    context = Column(String)
    order = Column(Integer)
    current = Column(Boolean, default=False)
    date_play = Column(Date)
    played = Column(Boolean, default=False)
    hard = Column(Boolean, default=False)

    tryings = relationship('Trying', back_populates='word')
    facts = relationship('WordFact', back_populates='word')
    stats = relationship('WordStat', back_populates='word')
    pixel = relationship('HintPixel', back_populates='word')
    crash = relationship('HintCrash', back_populates='word')
    results = relationship('ResultControl', back_populates='word')


class WordStat(Base):
    __tablename__ = 'word_stat'

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('word.id'))
    count_reg = Column(Integer)
    count_try = Column(Integer)
    count_done = Column(Integer)
    count_vers = Column(Integer)
    count_done_vers = Column(Integer)
    all_time = Column(Integer)
    all_done_time = Column(Integer)

    word = relationship('Word', back_populates='stats')



class Trying(Base):
    __tablename__ = 'trying'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    word_id = Column(Integer, ForeignKey('word.id'))
    date_trying = Column(DateTime)
    done = Column(Boolean, default=False)
    date_done = Column(DateTime)
    position = Column(Integer, default=0)
    hint = Column(Integer, default=0)
    skip = Column(Boolean, default=False)
    hard = Column(Boolean, default=False)

    user = relationship('User', back_populates='tryings')
    word = relationship('Word', back_populates='tryings')
    versions = relationship('Version', back_populates='trying')
    userscore = relationship('UserScore', back_populates='trying')
    hints_main_word = relationship('HintMainWord', back_populates='trying')
    results = relationship('ResultControl', back_populates='trying')
    crash_trying = relationship('HintCrashTrying', back_populates='trying')


class TryingTopTen(Base):
    __tablename__ = 'trying_top_ten'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    word_id = Column(Integer, ForeignKey('word.id'))
    date_start = Column(DateTime)
    done = Column(Boolean, default=False)
    date_done = Column(DateTime)
    count_word = Column(Integer, default=0)
    skip = Column(Boolean, default=False)
    hard = Column(Boolean, default=False)

    user = relationship('User', back_populates='ttt')
    vtt = relationship('VersionTopTen', back_populates='ttt')
    userscore_top_ten = relationship('UserScoreTopTen', back_populates='ttt')
    hints_top_ten = relationship('HintTopTen', back_populates='ttt')


class VersionTopTen(Base):
    __tablename__ = 'version_top_ten'

    id = Column(Integer, primary_key=True)
    ttt_id = Column(Integer, ForeignKey('trying_top_ten.id'))
    text = Column(Text)
    index = Column(Integer)
    date_version = Column(DateTime)
    hard = Column(Boolean, default=False)

    ttt = relationship('TryingTopTen', back_populates='vtt')


class UserScore(Base):
    __tablename__ = 'userscore'

    id = Column(Integer, primary_key=True)
    trying_id = Column(Integer, ForeignKey('trying.id'))
    versions = Column(Integer)
    score_vers = Column(Integer)
    time_sec = Column(Integer)
    score_time = Column(Integer)
    position = Column(Integer)
    score_pos = Column(Integer)
    score = Column(Integer)
    place = Column(Integer)

    trying = relationship('Trying', back_populates='userscore')


class UserScoreTopTen(Base):
    __tablename__ = 'userscore_top_ten'

    id = Column(Integer, primary_key=True)
    ttt_id = Column(Integer, ForeignKey('trying_top_ten.id'))

    word_1 = Column(Integer, default=0)
    word_2 = Column(Integer, default=0)
    word_3 = Column(Integer, default=0)
    word_4 = Column(Integer, default=0)
    word_5 = Column(Integer, default=0)
    word_6 = Column(Integer, default=0)
    word_7 = Column(Integer, default=0)
    word_8 = Column(Integer, default=0)
    word_9 = Column(Integer, default=0)
    word_10 = Column(Integer, default=0)

    word_all = Column(Integer, default=0)

    total = Column(Integer, default=0)

    ttt = relationship('TryingTopTen', back_populates='userscore_top_ten')


class Version(Base):
    __tablename__ = 'version'

    id = Column(Integer, primary_key=True)
    trying_id = Column(Integer, ForeignKey('trying.id'))
    text = Column(Text)
    index = Column(Integer)
    date_version = Column(DateTime)
    hard = Column(Boolean, default=False)

    trying = relationship('Trying', back_populates='versions')
    hints = relationship('Hint', back_populates='version')
    hints_main_vers = relationship('HintMainVers', back_populates='version')


class Hint(Base):
    __tablename__ = 'hint'

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('version.id'))

    version = relationship('Version', back_populates='hints')


class HintMainVers(Base):
    __tablename__ = 'hint_main_vers'

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('version.id'))
    hint_type = Column(String)

    version = relationship('Version', back_populates='hints_main_vers')


class HintMainWord(Base):
    __tablename__ = 'hint_main_word'

    id = Column(Integer, primary_key=True)
    trying_id = Column(Integer, ForeignKey('trying.id'))
    date_hint = Column(DateTime)
    hint_type = Column(String)

    trying = relationship('Trying', back_populates='hints_main_word')


class HintPixel(Base):
    __tablename__ = 'hint_pixel'

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('word.id'))
    pixel = Column(Text)
    picture = Column(Text)

    word = relationship('Word', back_populates='pixel')


class HintCrash(Base):
    __tablename__ = 'hint_crash'

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('word.id'))
    text = Column(Text)

    word = relationship('Word', back_populates='crash')
    crash_trying = relationship('HintCrashTrying', back_populates='crash')


class HintCrashTrying(Base):
    __tablename__ = 'hint_crash_trying'

    id = Column(Integer, primary_key=True)
    crash_id = Column(Integer, ForeignKey('hint_crash.id'))
    trying_id = Column(Integer, ForeignKey('trying.id'))
    date_hint = Column(DateTime)

    crash = relationship('HintCrash', back_populates='crash_trying')
    trying = relationship('Trying', back_populates='crash_trying')


class HintTopTen(Base):
    __tablename__ = 'hint_top_ten'

    id = Column(Integer, primary_key=True)
    ttt_id = Column(Integer, ForeignKey('trying_top_ten.id'))
    hint_type = Column(String)
    index_word = Column(Integer)
    date_hint = Column(DateTime)

    ttt = relationship('TryingTopTen', back_populates='hints_top_ten')


class Mode(Base):
    __tablename__ = 'mode'

    id = Column(Integer, primary_key=True)
    spy = Column(Boolean, default=False)


class UpdateMode(Base):
    __tablename__ = 'update_mode'

    id = Column(Integer, primary_key=True)
    update = Column(Boolean, default=False)


class WordFact(Base):
    __tablename__ = 'word_fact'

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('word.id'))
    type = Column(String)
    fact = Column(Text)

    word = relationship('Word', back_populates='facts')


class StartTimer(Base):
    __tablename__ = 'start_timer'

    id = Column(Integer, primary_key=True)
    timer = Column(Boolean, default=False)


class UserRemind(Base):
    __tablename__ = 'user_remind'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    date_remind = Column(DateTime)

    user = relationship('User', back_populates='remind')


class UpdateTime(Base):
    __tablename__ = 'update_time'

    id = Column(Integer, primary_key=True)
    hour = Column(Integer)


class UserEveryDay(Base):
    __tablename__ = 'user_every_day'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    count_coin = Column(Integer, default=1)

    user = relationship('User', back_populates='every_day')


class ResultControl(Base):
    __tablename__ = 'result_control'

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('word.id'))
    trying_id = Column(Integer, ForeignKey('trying.id'))
    done = Column(Boolean, default=False)
    result = Column(Boolean)
    probability = Column(Float)

    word = relationship('Word', back_populates='results')
    trying = relationship('Trying', back_populates='results')


class UserAlpha(Base):
    __tablename__ = 'user_alpha'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))

    user = relationship('User', back_populates='alpha')


class ReferralCode(Base):
    __tablename__ = 'referral_code'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    code = Column(String, unique=True)
    date_create = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Связь с пользователем, которому принадлежит код
    user = relationship("User", back_populates="referral_code")
    referral_user = relationship("ReferralUser", back_populates="referral_code")


class ReferralUser(Base):
    __tablename__ = 'referral_user'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    referral_code_id = Column(Integer, ForeignKey('referral_code.id'))

    user = relationship('User', back_populates='referral_user')
    referral_code = relationship('ReferralCode', back_populates='referral_user')


# Base.metadata.create_all(engine)
# Асинхронная функция для создания таблиц
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Функция для запуска инициализации
def init_db():
    asyncio.run(init_models())


