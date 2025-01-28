# -*- coding: utf-8 -*
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from utils import Config
from utils import EncodeItem, DecodeItem

from services.searchers import AnimeTitle
from services.importers import RawTranslation

import valkey.asyncio as valkey
import re


class Cache():
    def __init__(self) -> None:
        self.__RemoveTVPattern: re.Pattern = re.compile(r"(?:tv|тв)(?:[\-_⁓‐‑‒–—―]|\s*)(\d+)")

    @asynccontextmanager
    async def __getSession(self) -> AsyncGenerator[valkey.Valkey, None]:
        async with valkey.from_url(Config.CACHE_URI) as Session:
            yield Session

    async def MakeKey(self, name: str) -> str:
        Name: str = name.lower()
        if RemoveTV := self.__RemoveTVPattern.search(Name):
            Name = f'{self.__RemoveTVPattern.sub("", Name).strip()} {RemoveTV.group(1).strip()}'

        return "".join([i for i in Name.strip() if i.isalpha() or i.isdigit()])

    async def GetID(self, key: str) -> str | None:
        async with self.__getSession() as Client:
            if AnimeID := await Client.get(f"animeid:{key}"):
                return AnimeID.decode()

        return None

    async def AddID(self, key: str, malID: str) -> None:
        async with self.__getSession() as Client:
            await Client.set(f"animeid:{key}", malID)

    async def GetAnime(self, malID: int) -> AnimeTitle | None:
        async with self.__getSession() as Client:
            if AnimeData := await Client.get(f"anime:{malID}"):
                Anime: dict = await DecodeItem(AnimeData)
                return AnimeTitle(*Anime.values())

        return None

    async def AddAnime(self, malID: int, title: AnimeTitle) -> None:
        async with self.__getSession() as Client:
            await Client.set(f"anime:{malID}", await EncodeItem(title), ex = 86400)

    async def IsNotFounded(self, key: str) -> bool:
        async with self.__getSession() as Client:
            return not not (await Client.get(f"notfounded:{key}"))

    async def AddNotFounded(self, key: str, raw: RawTranslation) -> None:
        async with self.__getSession() as Client:
            await Client.set(f"notfounded:{key}", await EncodeItem(raw))

AnimeCache: Cache = Cache()
