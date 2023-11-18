import warnings

import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM

from analyzer import Analyzer
from dataloader import LocalDataLoader
from runner import Runner

from utils.message import Task, Format

MODEL_NAME = "EleutherAI/polyglot-ko-1.3b"


def main():
    transformers.logging.set_verbosity_error()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

    def infer(prompt):
        input_ids = tokenizer(
            prompt, return_tensors="pt"
        ).input_ids
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gen_tokens = model.generate(
                input_ids,
                do_sample=True,
                temperature=0.1,
                max_length=100
            )
        return tokenizer.batch_decode(gen_tokens)[0]

    # init
    # loader = LocalDataLoader("./test.csv", format=Format.CSV)
    loader = LocalDataLoader("./test.jsonl", format=Format.JSONL)
    analyze = Analyzer()
    run = Runner(
        loader=loader,
        analyzer=analyze
    )
    result = run.execute(
        task=Task.CUSTOM,
        model=lambda _, prompt: infer(prompt),
        upload=False
    )
    print(result)


if __name__ == '__main__':
    main()
