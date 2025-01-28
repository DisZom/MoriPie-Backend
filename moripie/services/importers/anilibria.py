from .importer import BaseImporter, RawTranslation, VideoPlayer

from web.requests import WebClient
from web.htmlparser import HTMLParser, HTMLNode

import asyncio


class AniLibriaImporter(BaseImporter):
    def __init__(self) -> None:
        super().__init__()

        self._mainURL = "dl-20240503-7.anilib.one"

    async def __createRaw(self, data: HTMLNode) -> RawTranslation | None:
        TitleID: str = f'{self._mainURL}{data.attributes["href"]}'
        TitleName: str = data.css_first(".torrent_pic").attributes["alt"].split("/")[1].strip()

        return RawTranslation((TitleName, "fdf"), True, self.Name, f'{self._mainURL}{data.attributes["href"]}')

    async def __getTranslations(self, session: WebClient, url: str) -> list[RawTranslation]:
        AnimeNodes: list[HTMLNode] = []

        AnimeHTML: HTMLParser = await self._fetchHTML(session, url)
        AnimeNodes += AnimeHTML.css("#dle-content > .th-item > .th-in")

        if PagesNode := AnimeHTML.css_first(".navigation"):
            MaxPage: int = int(PagesNode.last_child.text())
            for Page in range(2, MaxPage + 1):
                AnimeHTML = await self._fetchHTML(session, f"{url}/pages/catalog.php#page-{Page}")
                AnimeNodes += AnimeHTML.css("tr > td > a")

        return list(filter(None, await asyncio.gather(*map(self.__createRaw, AnimeNodes))))

    async def GetReleased(self) -> list[RawTranslation]:
        return None

    async def GetOngoing(self) -> list[RawTranslation]:
        return None

    async def GetPlayer(self, session: WebClient, raw: RawTranslation) -> VideoPlayer | None:
        return None
