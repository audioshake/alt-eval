import html

from .tokenizer import LINE, SECT, Token


class ErrorVisualizer:
    def __init__(self) -> None:
        self._ht_list: list[str] = []

    def process_chunk(
        self, chunk_ref: list[Token], chunk_hyp: list[Token], chunk_type: str
    ) -> None:
        if chunk_type == "equal":
            for token_ref, token_hyp in zip(chunk_ref, chunk_hyp):
                if token_ref.text != token_hyp.text:
                    assert token_ref.text.lower() == token_hyp.text.lower()
                    self._process_token(token_ref, "ref-case")
                    self._process_token(token_hyp, "hyp-case")
                else:
                    self._process_token(token_ref, "hit")
        else:
            for token_hyp in chunk_hyp:
                self._process_token(token_hyp, "hyp")
            for token_ref in chunk_ref:
                self._process_token(token_ref, "ref")

    def _process_token(self, token: Token, class_: str) -> None:
        classes = " ".join(["token", class_] + ["token-" + tag for tag in token.tags])
        self._ht_list.append(f'<span class="{classes}">{html.escape(token.text)}</span>')
        if class_[:3] in ["ref", "hit"] and {LINE, SECT} & token.tags:
            self._ht_list.append("<br>")

    def get_html(self) -> str:
        return " ".join(self._ht_list)
