from .searcher import BaseSearcher, AnimeTitle
from web.requests import WebClient

import asyncio


class KitsuSearcher(BaseSearcher):
    def __init__(self) -> None:
        super().__init__()

        self.MainURL = "https://kitsu.io"

    async def __getSynonyms(self, attrs: dict) -> tuple:
        Titles: dict = attrs["titles"]
        if "ja_jp" in Titles:
            del Titles["ja_jp"]

        Synonyms: tuple = (*Titles.values(), *attrs["abbreviatedTitles"], attrs["canonicalTitle"])
        Synonyms = tuple(filter(None, Synonyms))

        return Synonyms

    async def __createTitle(self, data: dict, includeData: list[dict]) -> AnimeTitle | None:
        if MappingsData := data.get("relationships", {}).get("mappings", {}).get("data"):
            Indexes: list[str] = [str(x["id"]) for x in MappingsData]

            for Included in includeData:
                IncludedAttributes: dict = Included["attributes"]

                if str(Included["id"]) in Indexes and IncludedAttributes["externalSite"].startswith("myanimelist"):
                    Attributes: dict = data["attributes"]
                    Synonyms: tuple = await self.__getSynonyms(Attributes)

                    return AnimeTitle(int(IncludedAttributes["externalId"]), self.Name, await self._clearName(Attributes["canonicalTitle"]), Attributes["status"] == "finished", Synonyms)

        return None

    async def GetAnimeByID(self, session: WebClient, malID: int) -> AnimeTitle | None:
        URL: str = f"{self.MainURL}/api/edge/mappings?filter[externalSite]=myanimelist%2Fanime&filter[externalId]={malID}&include=item"
        AnimeData: dict = await self._fetchJSON(session, URL)

        IncludedData: list[dict] = AnimeData.get("included")
        if not IncludedData:
            return None
    
        if Attributes := IncludedData[0].get("attributes"):
            Synonyms: tuple = await self.__getSynonyms(Attributes)
            return AnimeTitle(malID, self.Name, await self._clearName(Attributes["canonicalTitle"]), Attributes["status"] == "finished", Synonyms)

        return None

    async def GetAnimesByName(self, session: WebClient, name: str) -> list[AnimeTitle]:
        URL: str = f"{self.MainURL}/api/edge/anime?page[limit]=10&fields[anime]=titles,canonicalTitle,abbreviatedTitles,status,mappings&include=mappings&fields[mappings]=externalSite,externalId&filter[text]={name}"
        AnimeData: dict = await self._fetchJSON(session, URL)
        if not AnimeData:
            return []

        Data: list[dict] = AnimeData.get("data")
        IncludedData: list[dict] = AnimeData.get("included")
        if not (Data and IncludedData):
            return []

        Animes: list[AnimeTitle] = await asyncio.gather(*[self.__createTitle(x, IncludedData) for x in Data])
        return list(filter(None, Animes))
