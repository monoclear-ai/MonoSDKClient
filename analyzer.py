# Analyze and display outcomes
from typing import Dict

import requests
from fastapi.encoders import jsonable_encoder

from utils.constants import ENDPOINT_URL
from utils.message import Identifier, ClientMessage, ClientAction, ServerMessage, ServerAction


class Analyzer:
    def __init__(self, url: str = ENDPOINT_URL):
        # TODO : Configs
        self.send_url = f"{url}/send/"

    def request_final_report(self, id: Identifier, init_data: Dict):
        if not id:
            return None
        payload = ClientMessage(action=ClientAction.ANALYZE, id=id, data=init_data)
        r = requests.post(self.send_url, json=jsonable_encoder(payload))
        if r.status_code != 200:
            print(f"Analyzer Final Error : {r.text}")
            return None
        body = r.json()
        msg = ServerMessage(**body)
        action = msg.action
        data = msg.data
        if action != ServerAction.ANALYZE_ACK:
            print(f"Wrong action type : {body}")
            return None
        return data

    # Paginated
    def request_samples(self, id: Identifier, wrong_only: bool, page: int):
        if not id:
            return None
        data = {
            "wrong_only": wrong_only, "page": page
        }
        payload = ClientMessage(action=ClientAction.SAMPLES, id=id, data=data)
        r = requests.post(self.send_url, json=jsonable_encoder(payload))
        if r.status_code != 200:
            print(f"Analyzer Sample Error : {r.text}")
            return None
        body = r.json()
        msg = ServerMessage(**body)
        action = msg.action
        data = msg.data
        if action != ServerAction.SAMPLE_ACK:
            print(f"Wrong action type : {body}")
            return None
        return data
