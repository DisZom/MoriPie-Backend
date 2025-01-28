from .config import Config
from .logger import Logger

import orjson as __orjson
import base64 as __base64


async def EncodeItem(item) -> str:
    return __base64.b64encode(__orjson.dumps(item)).decode()

async def DecodeItem(data: str) -> dict:
    return __orjson.loads(__base64.b64decode(data))
