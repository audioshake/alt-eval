# alt-eval
An automatic lyrics transcription (ALT) evaluation toolkit, released with the [Jam-ALT benchmark](https://audioshake.github.io/jam-alt/).

The package implements metrics designed to work well with lyrics formatted according to music industry standards (see the [Jam-ALT annotation guide](https://huggingface.co/datasets/audioshake/jam-alt/blob/main/GUIDELINES.md)), namely:
- A **word error rate** (WER) computed on text tokenized in a way that accounts for elisions and non-standard contractions, which are common in song lyrics.
- A **case error rate**, measuring the rate of incorrectly predicted letter case.
- **Precision**, **recall** and **F-score** for symbols important for written lyrics:
  - Punctuation
  - Parentheses (used to delimit background vocals)
  - Line breaks
  - Section breaks (i.e. double line breaks)

## Usage
Install the package with `pip install alt-eval`.

To compute the metrics:
```python
from alt_eval import compute_metrics
compute_metrics(references, hypotheses)
```
where `references` and `hypotheses` are lists of strings. To specify the language (English by default), use the `languages` parameter, passing either a single language code, or a list of language codes corresponding to individual examples.

For JamALT, use:
```python
from datasets import load_dataset
dataset = load_dataset("audioshake/jam-alt")["test"]
compute_metrics(dataset["text"], transcriptions, languages=dataset["language"])
```

Use `visualize_errors=True` to also get a list of HTML snippets that can be used to visualize the errors in each transcript.
