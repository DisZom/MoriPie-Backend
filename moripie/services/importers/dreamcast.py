from .importer import BaseImporter, RawTranslation, VideoPlayer

from web.requests import WebClient, WebRequestMethods

import asyncio
import re


class DreamCastImporter(BaseImporter):
    def __init__(self) -> None:
        super().__init__()

        self._mainURL = "https://dreamerscast.com"
        self._headers.update({ "content-type": "application/x-www-form-urlencoded; charset=UTF-8" })

        self.__idRegex: re.Pattern = re.compile(r"/(\d+)-")

    async def __fetchJson(self, session: WebClient, status: int, page: int) -> list[dict]:
        return (await self._fetchJSON(
            session, self._mainURL, method = WebRequestMethods.POST,
            data = { "status": status, "pageNumber": page }
        ))["releases"]

    async def __createRaw(self, data: dict) -> RawTranslation:
        Names: tuple = (data["original"], data["russian"])
        IsReleased: bool = int(data["series"]) >= int(data["currentSeries"])

        return RawTranslation(Names, IsReleased, self.Name, f'{self._mainURL}{data["url"]}')

    async def __getTranslations(self, session: WebClient, status: int) -> list[RawTranslation]:
        AnimeData: list[dict] = []
        CurrentPage: int = 1

        while True:
            AnimeJson: list[dict] = await self.__fetchJson(session, status, CurrentPage)
            if not AnimeJson:
                break

            AnimeData += AnimeJson
            CurrentPage += 1

        return await asyncio.gather(*map(self.__createRaw, AnimeData))

    async def GetReleased(self, session: WebClient) -> list[RawTranslation]:
        return await self.__getTranslations(session, 2)

    async def GetOngoing(self, session: WebClient) -> list[RawTranslation]:
        return await self.__getTranslations(session, 1)

    async def GetPlayer(self, session: WebClient, raw: RawTranslation) -> VideoPlayer | None:
        return f"https://player.dreamerscast.com/playlist/{self.__idRegex.search(raw.Href).group(1)}"
