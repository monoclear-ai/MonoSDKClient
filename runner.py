# Poll for messages.
from typing import Callable, Dict, Optional
from time import sleep
import requests

from reporter import Reporter
from analyzer import Analyzer

from fastapi.encoders import jsonable_encoder
from utils.constants import ENDPOINT_URL
from utils.message import ClientMessage, ServerAction, Identifier, ServerMessage, ClientAction, Task


class Runner:
    def __init__(self, reporter: Reporter, analyzer: Analyzer,
                 interval: int = 0.1, url: str = ENDPOINT_URL):
        # TODO : Long poll
        self.send_url = f"{url}/send/"
        self.read_url = f"{url}/read/"
        self.interval = interval
        self.reporter = reporter
        self.analyzer = analyzer

    def execute(self, task: Task,
                model: Callable[[Identifier, str], Dict]
                ) -> Optional[Dict]:
        initated = False
        success = False

        init_data = {"task": task}
        payload = ClientMessage(action=ClientAction.RUN, data=init_data)
        r = requests.post(self.send_url, json=jsonable_encoder(payload))
        if r.status_code != 200:
            print(f"Run Send Error : {r.text}")
            return None
        body = r.json()
        msg = ServerMessage(**body)
        action = msg.action
        new_id = msg.id
        if action != ServerAction.RUN_ACK:
            print(f"Run Ack Error : {r.text}")
            return None
        id = new_id

        while True:
            r = requests.get(self.read_url, json=jsonable_encoder(id))
            if r.status_code != 200:
                print(f"Run Read Error : {r.text}")
                break
            body = r.json()
            msg = ServerMessage(**body)
            action = msg.action
            new_id = msg.id
            data = msg.data
            if action == ServerAction.ERROR:
                print(f"Run Execute Error : {msg}")
                break
            elif action == ServerAction.END:
                print(f"Run End : {msg}")
                success = True
                break

            elif action == ServerAction.START:
                print(f"Run Start : {msg}")
                initated = True
                id = new_id
                continue

            elif action == ServerAction.INPUT:
                if not initated:
                    continue
                if not id:
                    continue
                if id != new_id:
                    continue
                output = model(new_id, data["prompt"])
                eval = self.reporter.report_single(new_id, data["idx"], data["task_id"], output)
                if not eval:
                    print(f"Run Input Error : {eval}")
                    continue
                print(f"Eval : {eval}")
            elif action == ServerAction.EMPTY:
                print("Empty queue")
                pass
            elif action == ServerAction.NOT_INIT:
                print("Unitialized queue")
                pass
            sleep(self.interval)
        if not success:
            return None
        return self.analyzer.request_final_report(id, init_data)
