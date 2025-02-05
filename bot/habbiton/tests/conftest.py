import pytest
import pytest_asyncio
import asyncio
import sys
from habbiton import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, Base
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from habbiton.models.habit import Habit, HabitCompletion
from habbiton.models.state import Level, Message, Button
from habbiton.models.user import User
from datetime import date

@pytest.fixture(scope="function")
def db_session():
    engine = create_async_engine(f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@habbiton_db_test/{POSTGRES_DB}")
    session = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session

@pytest_asyncio.fixture(scope="function", autouse = True)
async def set_session_for_classes(db_session):
    Habit.set_session(db_session)
    User.set_session(db_session)
    Level.set_session(db_session)

@pytest_asyncio.fixture(scope="function", autouse = True)
async def create_tables():
    engine = create_async_engine(f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@habbiton_db_test/{POSTGRES_DB}")
    session = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with session() as ses:
        ses.add(Level(name="main"))
        ses.add(User(id=123))
        await ses.commit()
        ses.add(Habit(id = 1001, user_id = 123, name = 'Test', period = "Daily", created_date = date(year = 2024, month =1, day = 1)))
        await ses.commit()
    
