import csv
import json

import uuid
from typing import Dict

import requests
from fastapi.encoders import jsonable_encoder

from utils.constants import ENDPOINT_URL
from utils.message import ServerMessage, ClientMessage, ClientAction, Identifier, ServerAction, TaskPayload, Task, Format


def _parse_upload(result: Dict) -> Dict:
    res = {}
    for task, output in result.items():
        res[task] = output["accuracy"]
    return res


class _DataLoader:
    def __init__(self, local_only: bool = True):
        self.local_only = local_only

    def initStart(self, init_data: TaskPayload):
        raise NotImplementedError()

    def nextMessage(self):
        raise NotImplementedError()

    def nextOutcome(self, id: Identifier, idx: int, task_id: str, prompt: str, output: Dict):
        raise NotImplementedError()

    def rawResult(self, id: Identifier, init_data: TaskPayload):
        raise NotImplementedError()


class LocalDataLoader(_DataLoader):
    # TODO : More configurations
    def __init__(self, data_path: str, format: Format, url: str = ENDPOINT_URL):
        super().__init__(local_only=True)
        self.send_url = f"{url}/send/"
        self.data_path = data_path

        self.id = None
        # Current format is :
        # input prompt, desired outcome, eval method
        # TODO : Add augmentation format, prompt listing etc.
        self.format = format
        self.nextIdx = -1
        self.totalLength = 0
        self.prompts = {}
        self.answers = {}
        self.evalTypes = {}
        self.task = Task.CUSTOM
        self.evals = 0
        self.matches = 0

    def initStart(self, init_data: TaskPayload):
        if init_data.task != Task.CUSTOM:
            raise ValueError(f"Wrong task type : {init_data.task}")
        self.task = init_data.task

        # Maybe pandas loader to consolidate?
        with open(self.data_path, newline='') as file:
            if self.format == Format.CSV:
                reader = csv.reader(file, delimiter=',')
                for idx, row in enumerate(reader):
                    # TODO: Separate to a method
                    self.totalLength = idx + 1
                    self.evalTypes[idx] = row[-1]
                    if row[-1] == "numeral":
                        prompt = row[0]
                        answer = row[1]
                        self.prompts[idx] = prompt
                        self.answers[idx] = answer
                    else:
                        raise NotImplementedError(f"Wrong type : {row[-1]}")
            elif self.format == Format.JSONL:
                for idx, row in enumerate(file):
                    # TODO: Separate to a method
                    self.totalLength = idx + 1
                    data = json.loads(row)

                    eval = data["eval"]
                    self.evalTypes[idx] = eval
                    if eval == "numeral":
                        prompt = data["prompt"]
                        answer = data["answer"]
                        self.prompts[idx] = prompt
                        self.answers[idx] = answer
                    else:
                        raise NotImplementedError(f"Wrong type : {eval}")
            else:
                raise ValueError(f"Wrong format : {self.format}")
        print(self.prompts)
        new_id = Identifier(task=self.task, uid=str(uuid.uuid4()))
        self.id = new_id
        return new_id

    def nextMessage(self):
        print(f"MESSAGE CALL : {self.nextIdx}")
        if self.nextIdx == -1:
            self.nextIdx = 0
            return ServerMessage(action=ServerAction.START, id=self.id)
        if self.nextIdx >= self.totalLength:
            # End traffic
            return ServerMessage(action=ServerAction.END, id=self.id)
        # TODO : Prompt augmentation
        prompt = self.prompts[self.nextIdx]
        msg = ServerMessage(action=ServerAction.INPUT, id=self.id,
                            data={"idx": self.nextIdx, "task_id": self.task,
                                  "prompt": prompt})
        self.nextIdx += 1
        return msg

    def nextOutcome(self, id: Identifier, idx: int, task_id: str, prompt: str, output: Dict):
        label = self.answers[idx]
        if 'output' not in output or not output['output']:
            pred = ""
            is_match = False
        else:
            print(f"LOG : {output['output'][-5:]} & {label}")
            pred = output['output']
            is_match = pred[0] == label[0]
        self.evals += 1
        self.matches += 1 if is_match else 0
        return ServerMessage(action=ServerAction.ACK, id=self.id,
                             data={"idx": idx, "result": is_match,
                                   "pred": pred, "label": label})

    def rawResult(self, id: Identifier, init_data: TaskPayload):
        res = {}
        res["custom_overall"] = {
            "matches": self.matches,
            "evals": self.evals,
            "accuracy": self.matches / self.evals
        }

        # TODO : Actually calls server!
        if init_data.upload:
            data_load = dict(init_data)
            data_load = {**data_load, "result": res}
            payload = ClientMessage(action=ClientAction.UPLOAD_ONLY,
                                    id=id, data=data_load)
            print(f"Payload : {payload}")
            r = requests.post(self.send_url, json=jsonable_encoder(payload))
            if r.status_code != 200:
                print(f"Upload Error : {r.text}")
        return ServerMessage(action=ServerAction.ANALYZE_ACK, id=self.id,
                             data=res)


# TODO : Caching mechanism?
class ServerDataLoader(_DataLoader):
    def __init__(self, url: str = ENDPOINT_URL):
        super().__init__(local_only=False)
        self.send_url = f"{url}/send/"
        self.read_url = f"{url}/read/"

    def initStart(self, init_data: TaskPayload):
        payload = ClientMessage(action=ClientAction.RUN, data=dict(init_data))
        r = requests.post(self.send_url, json=jsonable_encoder(payload))
        if r.status_code != 200:
            print(f"Run Send Error : {r.text}")
            return None
        body = r.json()
        msg = ServerMessage(**body)

        action = msg.action
        new_id = msg.id
        self.id = new_id
        if action != ServerAction.RUN_ACK:
            print(f"Run Ack Error : {r.text}")
            return None
        return new_id

    def nextMessage(self):
        r = requests.get(self.read_url, json=jsonable_encoder(self.id))
        if r.status_code != 200:
            print(f"Run Read Error : {r.text}")
            return None
        body = r.json()
        msg = ServerMessage(**body)
        return msg

    def nextOutcome(self, id: Identifier, idx: int, task_id: str, prompt: str, output: Dict):
        payload = ClientMessage(action=ClientAction.OUTPUT,
                                id=id,
                                data={
                                    "idx": idx,
                                    "task_id": task_id,
                                    "prompt": prompt,
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

    def rawResult(self, id: Identifier, init_data: TaskPayload):
        if not id:
            return None
        payload = ClientMessage(action=ClientAction.ANALYZE, id=id, data=dict(init_data))
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
