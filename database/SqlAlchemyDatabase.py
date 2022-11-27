import os
import time

from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy import inspect


# noinspection PyUnresolvedReferences
def load_models():
    import database.models.User


load_dotenv()
if os.environ.get("PRODUCTION") == "true":
    time.sleep(10)
engine: AsyncEngine = create_async_engine(os.environ.get("DATABASE_URL"))
SqlAlchemyBase = declarative_base()
async_session_maker = sessionmaker(engine, class_=AsyncSession,
                                   expire_on_commit=False)
load_models()


async def init_models(create=False) -> None:
    """create tables if create=True or database is clear"""
    async with engine.connect() as conn:
        tables_count = len(await conn.run_sync(lambda sync_conn:
                                               inspect(sync_conn).get_table_names()))
    if create or tables_count == 0:
        async with engine.begin() as conn:
            await conn.run_sync(SqlAlchemyBase.metadata.drop_all)
            await conn.run_sync(SqlAlchemyBase.metadata.create_all)


async def get_session() -> AsyncSession:
    """
    Create async session for work with database
    :return: AsyncSession
    """
    async with async_session_maker() as session:
        yield session
