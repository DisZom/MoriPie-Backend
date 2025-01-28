from .importer import BaseImporter, RawTranslation, VideoPlayer

from web.requests import WebClient
from web.htmlparser import HTMLParser, HTMLNode

import asyncio
import re


class AniFilmImporter(BaseImporter):
    def __init__(self) -> None:
        super().__init__()

        self._mainURL = "https://anifilm.net"

        self.__animesURL: str = f"{self._mainURL}/releases/status"
        self.__animePlayers: tuple = ["sibnet", "myvi", "vk", "mail"] 

        self.__EpisodesRegex: re.Pattern = re.compile(r"^(\d+)\s?эп$")
        self.__AltEpisodesRegex: re.Pattern = re.compile(r"(\d+)\s?из?\s?([0-9~]+)\s?эп")

    async def __isReleased(self, data: HTMLNode) -> bool:
        EpisodesParts: tuple = tuple(data.text().replace("1-", "").strip().split(".,"))

        if len(EpisodesParts) == 1:
            return True
        elif "~" in EpisodesParts[0]:
            return False
        elif self.__EpisodesRegex.search(EpisodesParts[0]):
            return True

        EpisodesParts = self.__AltEpisodesRegex.search(EpisodesParts[0]).groups()

        return int(EpisodesParts[0]) >= int(EpisodesParts[1])

    async def __createRaw(self, data: HTMLNode) -> RawTranslation:
        RuNode: HTMLNode = data.css_first(".releases__title-russian")
        Names: tuple = (
            data.css_first(".releases__title-original").text().strip(),
            RuNode.text().strip()
        )

        IsReleased: bool = await self.__isReleased(data.css_first("ul > li:nth-child(2) > span.table-list__value"))
    
        return RawTranslation(Names, IsReleased, self.Name, f"{self._mainURL}{RuNode.attributes['href']}")

    async def __getTranslations(self, session: WebClient, url: str) -> list[RawTranslation]:
        AnimeNodes: list[HTMLNode] = []

        AnimeHTML: HTMLParser = await self._fetchHTML(session, url)
        AnimeNodes += AnimeHTML.css(".releases__item")

        if PagesNode := AnimeHTML.css_first(".pagination__items"):
            MaxPage: int = int(PagesNode.last_child.text())
            for Page in range(2, MaxPage + 1):
                AnimeHTML = await self._fetchHTML(session, f"{url}/page/{Page}")
                AnimeNodes += AnimeHTML.css(".releases__item")

        return await asyncio.gather(*map(self.__createRaw, AnimeNodes))

    async def GetReleased(self, session: WebClient) -> list[RawTranslation]:
        URL: str = f"{self.__animesURL}/completed"
        return await self.__getTranslations(session, URL)

    async def GetOngoing(self, session: WebClient) -> list[RawTranslation]:
        URL: str = f"{self.__animesURL}/ongoing"
        return await self.__getTranslations(session, URL)

    async def GetPlayer(self, session: WebClient, raw: RawTranslation) -> VideoPlayer | None:
        async def getEpisodeURL(episode: dict) -> str:
            return episode["iframe"]

        PlayerNode: HTMLNode = (await self._fetchHTML(session, raw.Href)).css_first(".release__content > player-component")
        if not PlayerNode:
            return None

        EpisodesURL: str = f'{self._mainURL}/releases/api:online:{PlayerNode.attributes[":releases_id"]}'
        for PlayerName in self.__animePlayers:
            if EpisodesJson := await self._fetchJSON(session, f"{EpisodesURL}:{PlayerName}"):
                return await asyncio.gather(*map(getEpisodeURL, EpisodesJson))

        return None
