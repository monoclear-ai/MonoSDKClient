# Poll for messages.
from typing import Callable, Dict, Optional
from time import sleep

from dataloader import _DataLoader
from analyzer import Analyzer

from utils.constants import ENDPOINT_URL, MONOCLEAR_SDK_KEY
from utils.message import ServerAction, Identifier, Task, TaskPayload


class Runner:
    def __init__(self, loader: _DataLoader, analyzer: Analyzer,
                 interval: int = 0.05, url: str = ENDPOINT_URL):
        # TODO : Long poll
        self.send_url = f"{url}/send/"
        self.read_url = f"{url}/read/"
        self.interval = interval
        self.loader = loader
        self.analyzer = analyzer

    def execute(self, task: Task,
                model: Callable[[Identifier, str], Dict],
                eval_key: str = MONOCLEAR_SDK_KEY,
                model_tag: str = "TEST_TAG",
                upload: bool = False
                ) -> Optional[Dict]:
        initiated = False
        success = False

        init_data = TaskPayload(
            task=task, eval_key=eval_key, upload=upload, model_tag=model_tag
        )

        new_id = self.loader.initStart(init_data=init_data)
        if new_id is None:
            return
        id = new_id

        while True:
            msg = self.loader.nextMessage()
            if msg is None:
                # Error Scenario currently
                break

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
                initiated = True
                id = new_id
                continue

            elif action == ServerAction.INPUT:
                if not initiated:
                    continue
                if not id:
                    continue
                if id != new_id:
                    continue
                output = model(new_id, data["prompt"])

                eval = self.loader.nextOutcome(new_id, data["idx"], data["task_id"], data["prompt"], output)
                if not eval:
                    print(f"Run Input Error : {eval}")
                    continue
                print(f"Eval : {eval}")
            elif action == ServerAction.EMPTY:
                print("Loading data ...")
                pass
            elif action == ServerAction.NOT_INIT:
                print("Initializing system ...")
                pass
            sleep(self.interval)
        if not success:
            return None
        return self.loader.rawResult(id, init_data)
