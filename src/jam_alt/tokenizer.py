import copy
from dataclasses import dataclass, field
import regex as re
import unicodedata

from sacremoses import MosesPunctNormalizer, MosesTokenizer


@dataclass
class Token:
    """A "rich" token (with a set of associated tags)."""

    text: str
    tags: set = field(default_factory=set)


WORD = "word"
PUNCT = "punctuation"
LINE = "line_break"
SECT = "section_break"
PAREN = "parenthesis"


def to_rich_tokens(tokens: list[str]) -> list[Token]:
    """Convert a list of plain (string) tokens to a list of rich tokens."""
    result: list[Token] = []
    for token in tokens:
        rich_token = Token(text=token)
        result.append(rich_token)

        # Tag as word / punctuation / line break
        if re.search(r"\w", token):
            rich_token.tags.add(WORD)
        elif token == "\n":
            rich_token.text = "<L>"
            rich_token.tags.add(LINE)
        elif "\n" in token:
            assert token == "\n\n"
            rich_token.text = "<S>"
            rich_token.tags.add(SECT)
        elif token in "()":
            rich_token.tags.add(PAREN)
        else:
            rich_token.tags.add(PUNCT)
            if rich_token.text == "@-@":
                rich_token.text = "-"

    return result


def tokens_as_words(tokens: list[Token]) -> list[Token]:
    """Process a list of rich tokens to filter out any non-word characters."""
    result: list[Token] = []
    for token in tokens:
        if WORD in token.tags:
            token = copy.deepcopy(token)
            token.text = re.sub(r"[^\w']", "", token.text)
            result.append(token)
    return result


class LyricsTokenizer:
    """A Moses-based tokenizer for lyrics.

    The tokenizer perfoms non-text character removal, Unicode normalization and punctuation
    normalization as pre-processing. Tokenization is done line by line and with special
    handling of apostrophes (elisions, contractions) and line breaks.
    """

    def __init__(self) -> None:
        self._tokenizers: dict[str, MosesTokenizer] = {}
        self._punct_normalizers: dict[str, MosesPunctNormalizer] = {}

        self._non_text_re = re.compile(r"[^\w\s\n\p{P}]")
        self._empty_line_re = re.compile(r"\n[^\S\n]+\n")
        self._newlines_re = re.compile(r"(\n+)")
        self._word_boundary_apos_re = re.compile(r"\b'\B|\B'\b")
        self._end_punctuation_re = re.compile(r"\W\s+$")
        self._contraction_de_re = re.compile(  # German contractions, e.g. geht's, wie'n
            r"(?P<a>)(?P<b>'s)\b|\b(?P<a>wie|für)(?P<b>'n)\b", flags=re.IGNORECASE
        )

    def __call__(self, text: str, language: str = "en") -> list[Token]:
        """
        Tokenize the given text.

        Args:
            text: A string to tokenize.
            language: A language code supported by `sacremoses`: either an ISO 639-1 language code,
                or "cjk" for Chinese, Japanese and Korean.

        Returns:
            A list of `Token` objects.
        """
        if language not in self._tokenizers:
            self._tokenizers[language] = MosesTokenizer(lang=language)
            self._punct_normalizers[language] = MosesPunctNormalizer(lang=language)
        tokenizer = self._tokenizers[language]
        punct_normalizer = self._punct_normalizers[language]

        text = self._non_text_re.sub(" ", text)
        text = unicodedata.normalize("NFC", text)
        text = text.rstrip("\n")
        text = self._empty_line_re.sub("\n\n", text)

        result = []
        for line in self._newlines_re.split(text):
            if self._newlines_re.match(line):
                result.append("\n")
                # >= 2 newlines are considered as a section break
                if line.count("\n") >= 2:
                    result.append("\n\n")
            elif line.strip():
                # Ensure the line ends with punctuation to make the tokenizer treat it as
                # a sentence
                remove_last = False
                if not self._end_punctuation_re.search(line):
                    remove_last = True
                    line += " ."

                line = punct_normalizer.normalize(line)

                if language in ["en", "fr", "it"]:
                    # Protect apostrophes at word boundaries to prevent the tokenizer from
                    # interpreting them as quotes
                    line = self._word_boundary_apos_re.sub("@@apos@@", line)
                else:
                    # For languages where the tokenizer doesn't handle apostrophes within words,
                    # protect all apostrophes
                    line = line.replace("'", "@@apos@@")

                line = tokenizer.tokenize(
                    line.strip(),
                    return_str=True,
                    escape=False,
                    aggressive_dash_splits=True,
                    protected_patterns=[r"\*+", r"@@apos@@"],
                )

                if remove_last:
                    assert line.endswith(" ."), line
                    line = line[:-2]

                # Post-process apostrophes
                line = line.replace("@@apos@@", "'")
                if language == "de":
                    # Split contractions
                    line = self._contraction_de_re.sub(r"\g<a> \g<b>", line)

                result.extend(line.strip().split())

        return to_rich_tokens(result)
