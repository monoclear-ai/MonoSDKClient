import os
import openai

from analyzer import Analyzer
from dataloader import ServerDataLoader
from runner import Runner
from utils.message import Task

API_KEY = os.getenv("OPENAI_API_KEY")


def main():
    def infer(prompt):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message["content"]

    # init
    loader = ServerDataLoader()
    analyze = Analyzer()
    run = Runner(
        loader=loader,
        analyzer=analyze
    )
    result = run.execute(
        task=Task.HAERAE,
        model=lambda _, prompt: infer(prompt)
    )
    print(result)


if __name__ == '__main__':
    main()
