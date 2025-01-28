# -*- coding: utf-8 -*
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON


class BaseItem(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key = True)

class TranslationItem(BaseItem):
    __tablename__ = "translations"

    mal_id: Mapped[int] =  mapped_column()
    name: Mapped[str] = mapped_column()

    dub_team: Mapped[str] = mapped_column()
    released: Mapped[bool] = mapped_column()

    href: Mapped[str] = mapped_column()
    player: Mapped[dict] = mapped_column(JSON(True))

    def __eq__(self, obj) -> bool:
        if isinstance(obj, TranslationItem):
            return self.mal_id == obj.mal_id and self.dub_team == obj.dub_team

        return False

    def __repr__(self) -> str:
        return f"TranslationItem(MAL ID: {self.mal_id}, Name: {self.name}, DUB Team: {self.dub_team}, Released: {self.released}, Href: {self.href})"
