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

@app.get("/")
async def Test(session: SessionDepend):
    Query: Select = select(TranslationItem).order_by(TranslationItem.mal_id)
    return { "data": (await session.scalars(Query)).all() }
