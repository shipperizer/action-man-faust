from os import environ

import asyncpg
from asyncpg.pool import Pool
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


session = scoped_session(sessionmaker())
Base = declarative_base()


async def db_pool() -> Pool:
    return await asyncpg.create_pool(
        dsn=environ.get('DB_CNX_STRING', 'postgresql://postgres:postgres@postgres:5432/actions')
    )
