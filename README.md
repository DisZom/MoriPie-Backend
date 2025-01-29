# MoriPie Parser Engine
Parser for automatic collection animes from the websites of dubbing teams (AniFilm, AniDUB, etc)

# Building
```bash
cp .env.example .env
# fill values in .env 
docker build -t parser .
```

# Running
```bash
docker compose up
```


# Structure
```bash
services
       │   service.py
       │
       ├───importers
       │       __init__.py
       │       importer.py
       │       ...
       │
       └───searchers
               searcher.py
               __init__.py
               ...

```
**Service** is the base class from which all importers and searchers are inherited.
 - **Importer** is a class that parsing RawTranslation's from dubbing team website and implements the GetReleased, GetOngoing, and GetPlayer methods.
 - **Searchers** is a class that parsing AnimeTitle's from search engines for future comparison with RawTranslation's and implements the GetAnimeByID and GetAnimesByName methods.