from dataclasses import dataclass

from services.searchers import AnimeTitle, AvailableSearchers
from services.importers import RawTranslation, VideoPlayer, AvailableImporters

from web.requests import WebClient

from utils import Logger
from cache import AnimeCache

from rapidfuzz import fuzz
from random import shuffle
from math import ceil

import asyncio


@dataclass(frozen = True)
class TranslationTitle:
    ID: int
    Name: str

    DubTeam: str
    Released: bool

    Href: str
    Player: VideoPlayer

    def __eq__(self, obj) -> bool:
        if not isinstance(obj, TranslationTitle):
            return False

        return self.ID == obj.ID and self.DubTeam == obj.DubTeam
    
    def __hash__(self) -> int:
        return hash((self.ID, self.DubTeam))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(MAL ID: {self.ID}, Name: {self.Name}, DUB Team: {self.DubTeam}, Released: {self.Released}, Href: {self.Href})"

class ParserEngine:
    def __init__(self, chunkSize: int = 10, scorePass: int = 80) -> None:
        self.ChunkSize: int = chunkSize
        self.ScorePass: int = scorePass

        Logger.info(f"Available Searchers({len(AvailableSearchers)}): {tuple(AvailableSearchers.keys())}")
        Logger.info(f"Available Importers({len(AvailableImporters)}): {tuple(AvailableImporters.keys())}")

    async def __getBestAnime(self, name: str, animes: list[AnimeTitle]) -> AnimeTitle | None:
        NameKey: str = await AnimeCache.MakeKey(name)
        AnimeScores: list[tuple[int, AnimeTitle]] = []

        for Anime in animes:
            for Synonym in Anime.Synonyms:
                SynonymKey: str = await AnimeCache.MakeKey(Synonym)
                AnimeScores.append((ceil(fuzz.ratio(NameKey, SynonymKey)), Anime))

        AnimeScores = [ i for i in AnimeScores if i[0] >= self.ScorePass ]
        if not AnimeScores:
            return None

        if len(AnimeScores) > 1:
            AnimeScores = sorted(AnimeScores, key = lambda x: x[0], reverse = True)

        return AnimeScores[0][1]

    async def GetTitleByID(self, session: WebClient, malID: int, searcherName: str | None = None) -> AnimeTitle | None:
        if CachedAnime := await AnimeCache.GetAnime(malID):
            return CachedAnime

        if searcherName in AvailableSearchers:
            if Anime := await AvailableSearchers[searcherName].GetAnimeByID(session, malID):
                await AnimeCache.AddAnime(malID, Anime)
                return Anime

        for Searcher in AvailableSearchers.values():
            if Anime := await Searcher.GetAnimeByID(session, malID):
                await AnimeCache.AddAnime(malID, Anime)
                return Anime

        return None

    async def GlobalSearch(self, session: WebClient, raw: RawTranslation) -> AnimeTitle | None:
        IDKey: str = await AnimeCache.MakeKey(raw.Names[0])
        if await AnimeCache.IsNotFounded(IDKey):
            return None

        if AnimeID := await AnimeCache.GetID(IDKey):
            SearcherName, SearcherID = AnimeID.split(":")
            if Anime := await self.GetTitleByID(session, int(SearcherID), SearcherName):
                return Anime

        for Name in raw.Names:
            for Searcher in AvailableSearchers.values():
                FoundedAnimes: list[AnimeTitle] = await Searcher.GetAnimesByName(session, Name)
                if not FoundedAnimes:
                    continue

                if RightAnime := await self.__getBestAnime(Name, FoundedAnimes):
                    await AnimeCache.AddID(IDKey, f"{RightAnime.SearcherName}:{RightAnime.MalID}")
                    await AnimeCache.AddAnime(RightAnime.MalID, RightAnime)
                    return RightAnime

        await AnimeCache.AddNotFounded(IDKey, raw)
        return None

    async def __createTitle(self, session: WebClient, raw: RawTranslation) -> TranslationTitle | None:
        Player: VideoPlayer = await AvailableImporters[raw.DubTeam].GetPlayer(session, raw)
        if not Player:
            Logger.warning(f'Can\'t Get Player! For: {raw.Names} By "{raw.DubTeam}"')
            return None
        
        Anime: AnimeTitle = await self.GlobalSearch(session, raw)
        if not Anime:
            Logger.warning(f'Can\'t Find ID! For: {raw.Names} By "{raw.DubTeam}"')
            return None

        if Anime.Released < raw.Released:
            return None

        return TranslationTitle(Anime.MalID, Anime.Name, raw.DubTeam, raw.Released, raw.Href, Player)

    async def __createTranstations(self, session: WebClient, raws: list[RawTranslation]) -> list[TranslationTitle]:
        shuffle(raws)

        RawsLen: int = len(raws)
        MaxChunks: int = ceil(RawsLen / self.ChunkSize)

        Translations: list[TranslationTitle] | set[TranslationTitle]  = []
        for ChunkRange in range(0, RawsLen, self.ChunkSize):
            Chunk: list[RawTranslation] = raws[ChunkRange:ChunkRange + self.ChunkSize]
            Translations += await asyncio.gather(*(self.__createTitle(session, i) for i in Chunk))

            Logger.info(f"Translations Chunk {int(ChunkRange / self.ChunkSize) + 1}/{MaxChunks} Loaded!")

        Translations = set(Translations)
        Translations.discard(None)

        return list(Translations)

    async def GetReleased(self) -> list[TranslationTitle]:
        async with WebClient() as Session:
            Translations: list[TranslationTitle] = await asyncio.gather(
                *(i.GetReleased(Session) for i in AvailableImporters.values())
            )

            return await self.__createTranstations(Session, sum(Translations, []))

    async def GetOngoing(self) -> list[TranslationTitle]:
        async with WebClient() as Session:
            Translations: list[TranslationTitle] = await asyncio.gather(
                *(i.GetOngoing(Session) for i in AvailableImporters.values())
            )

            return await self.__createTranstations(Session, sum(Translations, []))

Parser: ParserEngine = ParserEngine()
