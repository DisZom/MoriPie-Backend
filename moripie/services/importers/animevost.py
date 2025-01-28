from .importer import BaseImporter, RawTranslation, VideoPlayer

from web.requests import WebClient, WebRequestMethods
from web.htmlparser import HTMLParser, HTMLNode

import asyncio
import orjson
import re


class AnimeVostImporter(BaseImporter):
    def __init__(self) -> None:
        super().__init__()

        self._mainURL = "https://v3.vost.pw"
        self._headers.update({ "content-type": "application/x-www-form-urlencoded; charset=UTF-8" })

        self.__namesRegex: re.Pattern = re.compile(r"^(.*)\s?/\s+([^А-Яа-яё]+)\s?\[")
        self.__episodesRegex: re.Pattern = re.compile(r"\[(0-|1-|)?(\d+)\s?из?\s?(\d+)(\+?)\]")
        self.__dataRegex: re.Pattern = re.compile(r"var data = {(.*),};");

    async def __createRaw(self, data: HTMLNode, href: str = None) -> RawTranslation:
        Href: str = data.attributes["href"] if not href else href
        TitleStr: str = data.text().strip()

        Names: tuple = self.__namesRegex.search(TitleStr).groups()
        Names = tuple(i.strip() for i in reversed(Names))

        IsReleased: bool = False
        if Episodes := self.__episodesRegex.search(TitleStr):
            EpisodeParts: tuple = tuple(i.strip() for i in Episodes.groups())
            IsReleased = not EpisodeParts[3] and int(EpisodeParts[1]) >= int(EpisodeParts[2])

        return RawTranslation(Names, IsReleased, self.Name, Href)

    async def __getTranslations(self, session: WebClient, url: str) -> list[RawTranslation]:
        AnimeNodes: list[HTMLNode] = []

        AnimeHTML: HTMLParser = await self._fetchHTML(session, url)
        AnimeNodes += AnimeHTML.css(".shortstoryHead > h2 > a")

        if PagesNode := AnimeHTML.css_first("td.block_4"):
            MaxPage: int = int(PagesNode.css_first("a:last-child").text())
            for Page in range(2, MaxPage + 1):
                AnimeHTML = await self._fetchHTML(session, f"{url}page/{Page}/")
                AnimeNodes += AnimeHTML.css(".shortstoryHead > h2 > a")

        return await asyncio.gather(*map(self.__createRaw, AnimeNodes))

    async def GetReleased(self, session: WebClient) -> list[RawTranslation]:
        URL: str = f"{self._mainURL}/"
        return [ i for i in (await self.__getTranslations(session, URL)) if i.Released ]

    async def GetOngoing(self, session: WebClient) -> list[RawTranslation]:
        URL: str = f"{self._mainURL}/ongoing/"
        return await self.__getTranslations(session, URL)

    async def GetPlayer(self, session: WebClient, raw: RawTranslation) -> VideoPlayer | None:
        async def getEpisodeURL(episode: str) -> str:
            return f"{self._mainURL}/frame5.php?play={episode}"
        
        SeriesNode: HTMLNode = (await self._fetchHTML(session, raw.Href)) \
            .css("#dle-content > .shortstory > .shortstoryContent > script")[-1]
        
        if SeriesData := self.__dataRegex.search(SeriesNode.text()):
            return await asyncio.gather(*map(getEpisodeURL, orjson.loads(f"{{ { SeriesData.group(1) } }}").values()))

        return None
