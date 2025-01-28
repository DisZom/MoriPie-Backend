from typing import Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sqlalchemy import Select, select
from database import TranslationItem, Helper
from engine import TranslationTitle, Parser

import asyncio
from datetime import datetime


class Schedule:
    def __init__(self) -> None:
        self.__scheduler: AsyncIOScheduler = AsyncIOScheduler()
        self.__scheduler.add_job(
            self.__updateTranslations,
            args = [Parser.GetReleased],
            trigger = "cron",
            next_run_time = datetime.now(),
            week = "*"
        )
        self.__scheduler.add_job(
            self.__updateTranslations,
            args = [Parser.GetOngoing],
            trigger = "cron",
            next_run_time = datetime.now(),
            day = "*"
        )
    
    async def __createItem(self, translation: TranslationTitle) -> TranslationItem:
        return TranslationItem(
            mal_id = translation.ID,
            name = translation.Name,

            dub_team = translation.DubTeam,
            released = translation.Released,

            href = translation.Href,
            player = { "player": translation.Player }
        )

    async def __updateItem(self, translation: TranslationTitle) -> None:
        async with Helper.GetSession() as Session:
            Query: Select = select(TranslationItem).where(TranslationItem.mal_id == translation.ID, TranslationItem.dub_team == translation.DubTeam)
            Item: TranslationItem = (await Session.scalars(Query)).first()
            if not Item:
                Session.add(await self.__createItem(translation))
                return

            Item.released = translation.Released
            Item.href = translation.Href
            Item.player = { "player": translation.Player }
    
    async def __updateTranslations(self, func: Callable) -> None:
        await asyncio.gather(*map(self.__updateItem, await func()))

    async def Start(self) -> None:
        self.__scheduler.start()

    async def Dispose(self) -> None:
        self.__scheduler.shutdown()

Scheduler: Schedule = Schedule()
