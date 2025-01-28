from .importer import BaseImporter, RawTranslation, VideoPlayer

from web.requests import WebClient
from web.htmlparser import HTMLParser, HTMLNode

import asyncio
import base64
import re


class AniDUBImporter(BaseImporter):
    def __init__(self) -> None:
        super().__init__()

        self._mainURL = "https://anime.anidub.vip"

        self.__nameRegex: re.Pattern = re.compile(r"\[(\d+)\s?из?\s?(\d+).*\]$")
        self.__episodesRegex: re.Pattern = re.compile(r"^.*\[(\d+)\s?из?\s?(\d+).*\]$")
        self.__episodeIDRegex: re.Pattern = re.compile(r"/big(.*)\.jpg")

    async def __isReleased(self, nameEpisode: str) -> bool:
        if EpisodesRegex := self.__episodesRegex.search(nameEpisode):
            return int(EpisodesRegex.group(1)) >= int(EpisodesRegex.group(2))

        return True

    async def __createRaw(self, data: HTMLNode) -> RawTranslation | None:
        EngName: str = data.css_first(".th-subtitle").text().strip()
        if not EngName:
            return None

        RuNameWithEpisodes: str = data.css_first(".th-title").text().strip()
        Names: tuple = (
            EngName,
            self.__nameRegex.sub("", RuNameWithEpisodes).strip()
        )

        IsReleased: bool = await self.__isReleased(RuNameWithEpisodes)

        return RawTranslation(Names, IsReleased, self.Name, data.attributes["href"])

    async def __getTranslations(self, session: WebClient, url: str) -> list[RawTranslation]:
        AnimeNodes: list[HTMLNode] = []

        AnimeHTML: HTMLParser = await self._fetchHTML(session, url)
        AnimeNodes += AnimeHTML.css("#dle-content > .th-item > .th-in")

        if PagesNode := AnimeHTML.css_first(".navigation"):
            MaxPage: int = int(PagesNode.last_child.text())
            for Page in range(2, MaxPage + 1):
                AnimeHTML = await self._fetchHTML(session, f"{url}/page/{Page}")
                AnimeNodes += AnimeHTML.css("#dle-content > .th-item > .th-in")

        return list(filter(None, await asyncio.gather(*map(self.__createRaw, AnimeNodes))))

    async def GetReleased(self, session: WebClient) -> list[RawTranslation]:
        URL: str = f"{self._mainURL}/f/p.cat=2,3,4/r.year=1973;2024/sort=rating/order=desc/"
        return [i for i in (await self.__getTranslations(session, URL)) if i.Released]

    async def GetOngoing(self, session: WebClient) -> list[RawTranslation]:
        URL: str = f"{self._mainURL}/anime/anime_ongoing/"
        return await self.__getTranslations(session, URL)

    async def GetPlayer(self, session: WebClient, raw: RawTranslation) -> VideoPlayer | None:
        async def getEpisodeURL(data: HTMLNode) -> str:
            EpisodeID: str = self.__episodeIDRegex.search(data.attributes["href"]).group(1)
            EpisodeIDBase64: str = base64.b64encode(EpisodeID.encode()).decode()
            return f'{self._mainURL}/player/index.php?vid={EpisodeIDBase64}&url={raw.Href.replace(self._mainURL, "")}&ses=ff&id=-1'

        if AnimeHTML := await self._fetchHTML(session, raw.Href):
            return await asyncio.gather(*map(getEpisodeURL, AnimeHTML.css(".fscreens.fx-row > a")))

        return None
