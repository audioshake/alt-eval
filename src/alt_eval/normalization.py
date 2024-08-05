import regex as re


def normalize_lyrics(text: str) -> str:
    """Normalize lyrics to improve adherence to the Jam-ALT annotation guide.

    Unwanted end-of-line punctuation is removed and the first letter of each line is uppercased.

    This is a relatively crude normalization method that should generally improve the results at
    least for languages that use the Latin script. However, it may make the results worse if the
    line break predictions are not accurate.
    """
    # Remove unwanted trailing punctuation if not on a line on its own
    text = re.sub(r"(?<!^)[^\w\n!?'´‘’\"“”»)]+ *$", "", text, flags=re.MULTILINE)
    # Uppercase the first letter of each line
    text = re.sub(r"^([^\w\n]*\w)", lambda m: m.group(1).upper(), text, flags=re.MULTILINE)
    return text
