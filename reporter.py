# Report model outputs.
from typing import Dict

import requests
from fastapi.encoders import jsonable_encoder

from utils.constants import ENDPOINT_URL
from utils.message import Identifier, ClientMessage, ClientAction, ServerMessage, ServerAction


class Reporter:

    def __init__(self, url: str = ENDPOINT_URL):
        # TODO : Configs
        self.send_url = f"{url}/send/"

    def report_single(self, id: Identifier, idx: int, task_id: str, output: Dict):
        # TODO : Retries
        payload = ClientMessage(action=ClientAction.OUTPUT,
                                id=id,
                                data={
                                    "idx": idx,
                                    "task_id": task_id,
                                    "output": output
                                })
        r = requests.post(self.send_url, json=jsonable_encoder(payload))
        if r.status_code != 200:
            print(f"Report Single Error : {r.text}")
            return None
        body = r.json()
        msg = ServerMessage(**body)
        action = msg.action
        data = msg.data
        if action != ServerAction.ACK:
            print(f"Wrong action type : {body}")
            return None
        return data
