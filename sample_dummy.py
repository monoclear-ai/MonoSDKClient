import warnings

import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM

from analyzer import Analyzer
from dataloader import ServerDataLoader
from runner import Runner

from utils.message import Task

MODEL_NAME = "EleutherAI/polyglot-ko-1.3b"


def main():
    transformers.logging.set_verbosity_error()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

    def infer(prompt):
        return "2) 질답"

    # init
    loader = ServerDataLoader()
    analyze = Analyzer()
    run = Runner(
        loader=loader,
        analyzer=analyze
    )
    result = run.execute(
        task=Task.HAERAE,
        model=lambda _, prompt: infer(prompt),
        upload=True
    )
    print(result)


if __name__ == '__main__':
    main()
