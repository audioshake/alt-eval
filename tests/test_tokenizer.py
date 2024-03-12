import pytest

from alt_eval.tokenizer import LyricsTokenizer


# fmt: off
@pytest.mark.parametrize(
    "language, text, expected_tokens",
    [
        (
            "en",
            "I ain't got nothin' but the blues",
            ["I", "ain", "'t", "got", "nothin'", "but", "the", "blues"],
        ),
        (
            "en",
            "It 'll be fun (ha!)",
            ["It", "'ll", "be", "fun", "(", "ha", "!", ")"]
        ),
        (
            "de",
            "Sei's Melancholie",
            ["Sei", "'s", "Melancholie"]
        ),
        (
            "de",
            "Könnt' ich dir Schmerz erspar'n",
            ["Könnt'", "ich", "dir", "Schmerz", "erspar'n"],
        ),
        (
            "fr",
            "T'avais fait l'amour deux fois sans penser qu'avec cette fille-là",
            ["T'", "avais", "fait", "l'", "amour", "deux", "fois", "sans", "penser", "qu'", "avec", "cette", "fille", "-", "là"],
        ),
        (
            "ja",
            "私は日本語を話せません(ラララ)",
            ["私", "は", "日本", "語", "を", "話せ", "ませ", "ん", "(", "ラララ", ")"],
        ),
        (
            "zh",
            "我不会说中文。(哈哈)",
            ["我", "不", "会", "说", "中", "文", "。", "(", "哈", "哈", ")"],
        )
    ],
)
# fmt: on
def test_lyrics_tokenizer(language, text, expected_tokens):
    tokenizer = LyricsTokenizer()
    tokens = [t.text for t in tokenizer(text, language=language)]
    assert tokens == expected_tokens
