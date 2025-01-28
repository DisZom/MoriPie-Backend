from abc import ABC, abstractmethod
from dataclasses import dataclass

from services.service import BaseService
from web.requests import WebClient


@dataclass(frozen = True)
class AnimeTitle:
    MalID: int
    SearcherName: str

    Name: str
    Released: bool
    Synonyms: tuple[str]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(MAL ID: {self.MalID}, Name: {self.Name}, Released: {self.Released}, Searcher: {self.SearcherName})"

class BaseSearcher(BaseService, ABC):
    def __init__(self) -> None:
        super().__init__()
        self.Name = self.Name.replace("Searcher", "")
        self._searchLimit: int = 10

    async def _clearName(self, name: str) -> str:
        return name.encode("ascii", "ignore").decode().strip()

    @abstractmethod
    async def GetAnimeByID(self, session: WebClient, malID: int) -> AnimeTitle | None:
        pass

    @abstractmethod
    async def GetAnimesByName(self, session: WebClient, name: str) -> list[AnimeTitle]:
        pass
