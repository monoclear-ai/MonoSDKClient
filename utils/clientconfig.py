from pydantic import BaseModel
from utils.constants import ENDPOINT_URL


class ClientConfig(BaseModel):
    endpoint: str = ENDPOINT_URL


class PollConfig(ClientConfig):
    lazy: bool = False


class ReportConfig(ClientConfig):
    pretty: bool = False
