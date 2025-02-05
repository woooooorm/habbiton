from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from os import getenv

class Base(AsyncAttrs, DeclarativeBase):
    pass

#Pulling sensitive info from env. variables
TOKEN = getenv("TG_BOT_TOKEN")
POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
POSTGRES_DB = getenv("POSTGRES_DB")
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@habbiton_db/{POSTGRES_DB}"

#Session factory, used for db access
engine = create_async_engine(DATABASE_URL)
session = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)