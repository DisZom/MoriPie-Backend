from contextlib import asynccontextmanager
from typing import AsyncGenerator, Annotated

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from utils import Config
from .models import BaseItem

from fastapi import Depends


class DBHelper:
    def __init__(self) -> None:
        print(Config.DB_URI)
        self.__engine: AsyncEngine = create_async_engine(Config.DB_URI)
        self.__maker: async_sessionmaker[AsyncSession] = async_sessionmaker(self.__engine)

    async def Prepare(self) -> None:
        async with self.__engine.begin() as Connection:
            await Connection.run_sync(BaseItem.metadata.create_all)

    async def Dispose(self):
        await self.__engine.dispose()

    @asynccontextmanager
    async def GetSession(self) -> AsyncGenerator[AsyncSession, None]:
        Session: AsyncSession = self.__maker()
        try:
            yield Session
            await Session.commit()
        except:
            await Session.rollback()
        finally:
            await Session.close()

    async def SessionDep(self) -> AsyncGenerator[AsyncSession, None]:
        yield await self.GetSession()


Helper: DBHelper = DBHelper()
SessionDepend = Annotated[AsyncSession, Depends(Helper.SessionDep)]
