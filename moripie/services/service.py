from web.requests import WebRequestMethods, WebClient, WebErrors, Ping
from web.htmlparser import HTMLParser
import orjson

import asyncio
from utils import Logger


class BaseService:
    def __init__(self) -> None:
        self.Name: str = self.__class__.__name__
        self._mainURL: str = "https://example.com"
        self._headers: dict =  {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36"
        }
    
    def IsOnline(self):
        return Ping(self._mainURL)

    async def _fetchRAW(self, session: WebClient, url: str, *, method: WebRequestMethods = WebRequestMethods.GET, **kwargs: dict) -> bytes | None:
        kwargs.setdefault("headers", self._headers)

        try:
            return await session.Fetch(url, method = method, **kwargs)
        except WebErrors as e:
            Logger.error(f"{e.__class__.__name__}! {self.Name} Waiting 2 Min To Rerty Request To {url}")
            await asyncio.sleep(120)
            return await self._fetchRAW(session, url, method = method, **kwargs)
    
    async def _fetchHTML(self, session: WebClient, url: str, *, method: WebRequestMethods = WebRequestMethods.GET, **kwargs) -> HTMLParser | None:
        if Raw := await self._fetchRAW(session, url, method = method, **kwargs):
            return HTMLParser(Raw.decode())

        return None
    
    async def _fetchJSON(self, session: WebClient, url: str, *, method: WebRequestMethods = WebRequestMethods.GET, **kwargs) -> dict | list | None:
        if Raw := await self._fetchRAW(session, url, method = method, **kwargs):
            return orjson.loads(Raw)

        return None
