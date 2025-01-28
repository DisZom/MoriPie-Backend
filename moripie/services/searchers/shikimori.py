from .searcher import BaseSearcher, AnimeTitle
from web.requests import WebClient

import asyncio


class ShikimoriSearcher(BaseSearcher):
    def __init__(self) -> None:
        super().__init__()
        self._mainURL = "https://shikimori.one"

    async def __createTitle(self, anime: dict) -> AnimeTitle:
        Synonyms: list[str] = [ anime["name"] ]
        if anime["russian"]:
            Synonyms.append(anime["russian"])

        return AnimeTitle(int(anime["id"]), self.Name, await self._clearName(anime["name"]), anime["status"] == "released", tuple(Synonyms))

    async def GetAnimeByID(self, session: WebClient, malID: int) -> AnimeTitle | None:
        URL: str = f"{self._mainURL}/api/animes/{malID}"
        if AnimeJson := await self._fetchJSON(session, URL):
            return await self.__createTitle(AnimeJson)

        return None

    async def GetAnimesByName(self, session: WebClient, name: str) -> list[AnimeTitle]:
        URL: str = f"{self._mainURL}/api/animes?limit={self._searchLimit}&search={name}"
        if AnimeJson := await self._fetchJSON(session, URL):
            return await asyncio.gather(*map(self.__createTitle, AnimeJson))

        return None
