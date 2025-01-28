from .searcher import BaseSearcher, AnimeTitle
from web.requests import WebClient

import asyncio


class MALSearcher(BaseSearcher):
    def __init__(self) -> None:
        super().__init__()

        self._mainURL = "https://api.myanimelist.net"
        self._headers.update({ "X-MAL-Client-ID": "6114d00ca681b7701d1e15fe11a4987e" })

    async def __fetchJSON(self, session: WebClient, url: str) -> dict | list:
        if Response := await self._fetchJSON(session, url):
            if "data" in Response:
                return [ i["node"] for i in Response["data"] ]

            return Response

        return []

    async def __createTitle(self, anime: dict) -> AnimeTitle:
        Titles: dict = anime["alternative_titles"]
        Synonyms: tuple = (anime["title"], Titles["en"], *Titles["synonyms"])

        return AnimeTitle(int(anime["id"]), self.Name, await self._clearName(anime["title"]), anime["status"] == "finished_airing", Synonyms)

    async def GetAnimeByID(self, session: WebClient, malID: int) -> AnimeTitle | None:
        URL: str = f"{self._mainURL}/v2/anime/{malID}?fields=alternative_titles,status"
        if Anime := await self.__fetchJSON(session, URL):
            return await self.__createTitle(Anime)

        return None

    async def GetAnimesByName(self, session: WebClient, name: str) -> list[AnimeTitle]:
        URL: str = f"{self._mainURL}/v2/anime?limit={self._searchLimit}&fields=alternative_titles,status&q={name[0:80]}"
        return await asyncio.gather(*map(self.__createTitle, await self.__fetchJSON(session, URL)))
