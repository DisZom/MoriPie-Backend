from typing import Self

import asyncio
from enum import Enum

from urllib.parse import ParseResult, urlparse
from ssl import TLSVersion, SSLContext, create_default_context

from aiohttp import ClientSession, ClientResponse, TCPConnector
from aiohttp import ClientConnectionError, ConnectionTimeoutError

from urllib.request import urlopen
from urllib.error import URLError, HTTPError


def Ping(url: str) -> bool:
    try:
        urlopen(url, timeout = 2.0)
    except HTTPError as e:
        return e.status != 500
    except URLError:
        return False

    return True

WebErrors: tuple = (ConnectionTimeoutError, ClientConnectionError)

class WebRequestMethods(Enum):
    GET = "GET"
    POST = "POST"

class WebClient:
    def __init__(self) -> None:
        self.__context: SSLContext = create_default_context()
        self.__context.maximum_version = TLSVersion.TLSv1_2
        self.__connector = TCPConnector(ssl_context = self.__context)

        self.__session: ClientSession = None

    async def __aenter__(self) -> Self:
        self.__session = ClientSession(connector = self.__connector)
        return self
    
    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.__session.close()

    async def Fetch(self, url: str, *, method: WebRequestMethods = WebRequestMethods.GET, **kwargs) -> bytes | None:
        async with self.__session.request(method.value, url, **kwargs) as Response:
            if Response.status in (429, 503):
                await asyncio.sleep(float(Response.headers.get("Retry-After", 0.5)))
                return await self.Fetch(url, method = method, **kwargs)

            elif Response.status in (301, 302, 303, 307, 308) and "Location" in Response.headers:
                Location: str = Response.headers["Location"]
                if not Location.startswith("http"):
                    URLParts: ParseResult = urlparse(url)
                    Location = f"{URLParts.scheme}://{URLParts.netloc}{Location}"

                return await self.Fetch(Location, method = method, **kwargs)

            elif Response.status in (400, 404):
                return None

            return await Response.read()
    
