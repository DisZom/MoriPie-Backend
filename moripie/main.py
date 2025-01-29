from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from database import Helper, SessionDepend, TranslationItem
from schedule import Scheduler

from sqlalchemy import Select, select


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Helper.Prepare()
    await Scheduler.Start()

    yield

    await Scheduler.Dispose()
    await Helper.Dispose()

app: FastAPI = FastAPI(lifespan = lifespan, default_response_class = ORJSONResponse)


@app.get("/anime/{mal_id}", description = "Get translations by MAL ID")
async def Test(session: SessionDepend, mal_id: int):
    Query: Select = select(TranslationItem).where(TranslationItem.mal_id == mal_id).order_by(TranslationItem.dub_team)
    return { "data": (await session.scalars(Query)).all() }

@app.get("/team/{dub_team}", description = "Get translations by dubbing team")
async def Test(session: SessionDepend, dub_team: str, limit: int | None = None, page: int | None = None):
    Query: Select = select(TranslationItem).where(TranslationItem.dub_team == dub_team) \
                    .limit(max(5, min(limit, 20))).offset(page).order_by(TranslationItem.mal_id)

    return { "data": (await session.scalars(Query)).all() }
