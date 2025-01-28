# -*- coding: utf-8 -*-
from .importer import BaseImporter, RawTranslation, VideoPlayer

from .anidub import AniDUBImporter
from .anifilm import AniFilmImporter
#from .anilibria import AniLibriaImporter
from .animevost import AnimeVostImporter
from .dreamcast import DreamCastImporter 


AvailableImporters: dict[str, BaseImporter] = { 
    i.Name: i for i in [
        AniDUBImporter(),
        AniFilmImporter(),
        #AniLibriaVideo(),
        AnimeVostImporter(),
        DreamCastImporter()
    ]
    if i.IsOnline() 
}
