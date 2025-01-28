from .searcher import BaseSearcher, AnimeTitle
from web.requests import WebClient

import re
from datetime import date

import asyncio


class Anime365Searcher(BaseSearcher):
    def __init__(self) -> None:
        super().__init__()

        self._mainURL = "https://smotret-anime.org"
        self.__japaneseRegex: re.Pattern = re.compile(r"[\u3041-\u3096\u30a0-\u30ff\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A]")
        self.__currentYear: int = date.today().year

    async def __fetchJSON(self, session: WebClient, url: str) -> list[dict]:
        return (await self._fetchJSON(session, url))["data"]

    async def __createTitle(self, anime: dict) -> AnimeTitle | None:
        AnimeID: int = int(anime["myAnimeListId"])
        if AnimeID == 0:
            return None

        Synonyms: tuple = tuple(i for i in anime["allTitles"] if i and not self.__japaneseRegex.findall(i))
        IsReleased: bool = anime["isAiring"] == 0 and int(anime["year"]) <= self.__currentYear

        return AnimeTitle(AnimeID, self.Name, await self._clearName(anime["titles"]["romaji"]), IsReleased, Synonyms)

    async def GetAnimeByID(self, session: WebClient, malID: int) -> AnimeTitle | None:
        URL: str = f"{self._mainURL}/api/series?myAnimeListId={malID}"
        if Anime := await self.__fetchJSON(session, URL):
            return await self.__createTitle(Anime[0])

        return None

    async def GetAnimesByName(self, session: WebClient, name: str) -> list[AnimeTitle]:
        URL: str = f"{self._mainURL}/api/series?limit={self._searchLimit}&query={name}"
        Animes: list[AnimeTitle] = await asyncio.gather(*map(self.__createTitle, await self.__fetchJSON(session, URL)))

        return list(filter(None, Animes))
