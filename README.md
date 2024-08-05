# alt-eval
An automatic lyrics transcription (ALT) evaluation toolkit, released with the [Jam-ALT benchmark](https://audioshake.github.io/jam-alt/).

The package implements metrics designed to work well with lyrics formatted according to music industry standards (see the [Jam-ALT annotation guide](https://huggingface.co/datasets/audioshake/jam-alt/blob/main/GUIDELINES.md)), namely:
- A **word error rate** (WER) computed on text tokenized in a way that accounts for non-standard spellings common in song lyrics.
- A **case-sensitive WER**.
- **Precision**, **recall** and **F-score** for symbols important for written lyrics:
  - Punctuation
  - Parentheses (used to delimit background vocals)
  - Line breaks
  - Section breaks (i.e. double line breaks)

Under the hood, the text is pre-processed using the [`sacremoses`](https://github.com/hplt-project/sacremoses) tokenizer and punctuation normalizer.
Note that apostrophes and single quotes are never treated as quotation marks, but as part of a word, marking an elision or a contraction.

## Usage
Install the package with `pip install alt-eval`.

To compute the metrics:
```python
from alt_eval import compute_metrics
compute_metrics(references, hypotheses)
```
where `references` and `hypotheses` are lists of strings. To specify the language (English by default), use the `languages` parameter, passing either a single language code, or a list of language codes corresponding to individual examples.

For Jam-ALT, use:
```python
from datasets import load_dataset
dataset = load_dataset("audioshake/jam-alt")["test"]
compute_metrics(dataset["text"], transcriptions, languages=dataset["language"])
```

If you are only interested in WER, you may skip formatting- and punctuation-related metrics by passing `include_other=False`.

Use `visualize_errors=True` to also get a list of HTML snippets that can be used to visualize the errors in each transcript.

## Language support
The package implements language-specific tokenization via `sacremoses`, enhanced with custom rules. Support is well tested for English, Spanish, German, and French.

For writing systems that do not use spaces to separate words (Chinese, Japanese, Thai, Lao, Burmese, …), each character is considered as a separate word, as per [Radford et al. (2022)](https://arxiv.org/abs/2212.04356), making the WER equivalent to CER (character error rate).

See the [test cases](./tests/test_tokenizer.py) for examples of how different languages are tokenized.
Contributions adding support for additional languages are welcome.

## Optional lyrics normalization
The [Jam-ALT annotation guide](https://huggingface.co/datasets/audioshake/jam-alt/blob/main/GUIDELINES.md) forbids certain end-of-line punctuation and requires the first letter of each line to be uppercase.
For transcription systems that do not respect these rules, the results on Jam-ALT can be improved by normalizing the transcripts using the `normalize_lyrics()` function, which fixes these specific issues.
Note, however, that this relies on the line break predictions being correct. Moreover, other datasets may follow different rules.
For these reasons, this normalization is **not** included as a fixed pre-processing step in `compute_metrics()`, and instead made optional.
