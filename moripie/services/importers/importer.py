from typing import TypeAlias

from abc import ABC, abstractmethod
from dataclasses import dataclass

from services.service import BaseService
from web.requests import WebClient


@dataclass(frozen = True)
class RawTranslation():
    Names: tuple[str, str]
    Released: bool

    DubTeam: str
    Href: str

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(Names: {" | ".join(self.Names)}, DUB Team: {self.DubTeam}, Released: {self.Released}, Href: {self.Href})'

VideoPlayer: TypeAlias = str | list[str]

class BaseImporter(BaseService, ABC):
    def __init__(self) -> None:
        super().__init__()
        self.Name = self.Name.replace("Importer", "")

    @abstractmethod
    async def GetReleased(self, session: WebClient) -> list[RawTranslation]:
        pass

    @abstractmethod
    async def GetOngoing(self, session: WebClient) -> list[RawTranslation]:
        pass

    @abstractmethod
    async def GetPlayer(self, session: WebClient, raw: RawTranslation) -> VideoPlayer | None:
        pass