import json

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel


def fastapi_encode(model: BaseModel):
    json_comp = jsonable_encoder(model)
    return json.dumps(json_comp)