# Monoclear SDK

Supports HAE-RAE for now. Look forward to more features!

## Examples

See `sample_*.py` for running sample code.

Only `infer` method needs to be changed per model.

```Python
from analyzer import Analyzer
from runner import Runner
from reporter import Reporter
from utils.message import Task

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
```

### HuggingFace Transformers

```Python
import warnings

import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "EleutherAI/polyglot-ko-1.3b"

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
```

### OpenAI

```Python
import openai

def infer(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message["content"]
```