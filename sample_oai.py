import warnings

import os
import openai

from analyzer import Analyzer
from runner import Runner
from reporter import Reporter
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
    report = Reporter()
    analyze = Analyzer()
    run = Runner(
        reporter=report,
        analyzer=analyze
    )
    result = run.execute(
        task=Task.KOBEST,
        model=lambda _, prompt: infer(prompt)
    )
    print(result)


if __name__ == '__main__':
    main()
