# -*- coding: utf-8 -*-
from .searcher import BaseSearcher, AnimeTitle

from .shikimori import ShikimoriSearcher
from .anime365 import Anime365Searcher
from .myanimelist import MALSearcher
from .kitsu import KitsuSearcher


AvailableSearchers: dict[str, BaseSearcher] = { 
    i.Name: i for i in [
        Anime365Searcher(), 
        ShikimoriSearcher(),
        MALSearcher(), 
        KitsuSearcher()
    ] 
    if i.IsOnline() 
}
