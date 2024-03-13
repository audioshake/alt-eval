import collections
from dataclasses import dataclass
from typing import Any, Optional, Union

import iso639
import jiwer

from .error_visualizer import ErrorVisualizer
from .tokenizer import LINE, PAREN, PUNCT, SECT, LyricsTokenizer, Token, tokens_as_words

IDENTITY_TRANSFORM = jiwer.Compose([])


@dataclass
class EditOpCounts:
    """A counter for edit operations (hits, substitutions, deletions, insertions)."""

    H: int = 0
    S: int = 0
    D: int = 0
    I: int = 0


def process_alignment_chunk(
    reference: list[Token],
    hypothesis: list[Token],
    chunk_type: str,
    counts: dict[Any, EditOpCounts],
    count_substitutions: bool = True,
) -> None:
    """Count tag-specific edit operations in a chunk of an alignment."""
    if chunk_type == "delete":
        assert len(hypothesis) == 0
        for token in reference:
            for tag in token.tags:
                counts[tag].D += 1
    elif chunk_type == "insert":
        assert len(reference) == 0
        for token in hypothesis:
            for tag in token.tags:
                counts[tag].I += 1
    elif chunk_type in ["substitute", "equal"]:
        assert len(reference) == len(hypothesis)
        for token_ref, token_hyp in zip(reference, hypothesis):
            common_tags = token_ref.tags & token_hyp.tags if count_substitutions else set()
            for tag in token_ref.tags - common_tags:
                counts[tag].D += 1
            for tag in token_hyp.tags - common_tags:
                counts[tag].I += 1
            if chunk_type == "substitute":
                for tag in common_tags:
                    counts[tag].S += 1
            elif chunk_type == "equal":
                for tag in common_tags:
                    counts[tag].H += 1
    else:
        assert False, f"Unhandled chunk type: {chunk_type}"


def process_alignments(
    references: list[list[Token]],
    hypotheses: list[list[Token]],
    alignments: list[list[jiwer.AlignmentChunk]],
    count_substitutions: bool = True,
    visualize_errors: bool = False,
) -> tuple[dict[Any, EditOpCounts], dict[str, int], Optional[list[str]]]:
    """Count tag-specific edit operations in a list of alignments."""
    edit_counts = collections.defaultdict(EditOpCounts)
    error_counts = collections.defaultdict(int)
    vis_htmls = [] if visualize_errors else None

    for i in range(len(references)):
        visualizer = ErrorVisualizer() if visualize_errors else None
        for chunk in alignments[i]:
            chunk_hyp = hypotheses[i][chunk.hyp_start_idx : chunk.hyp_end_idx]
            chunk_ref = references[i][chunk.ref_start_idx : chunk.ref_end_idx]
            process_alignment_chunk(
                chunk_ref,
                chunk_hyp,
                chunk.type,
                edit_counts,
                count_substitutions=count_substitutions,
            )
            if visualize_errors:
                visualizer.process_chunk(chunk_ref, chunk_hyp, chunk.type)

            if chunk.type == "equal":
                for token_ref, token_hyp in zip(chunk_ref, chunk_hyp):
                    if token_ref.text != token_hyp.text:
                        assert token_ref.text.lower() == token_hyp.text.lower()
                        error_counts["case"] += 1

        if visualize_errors:
            vis_htmls.append(visualizer.get_html())

    return edit_counts, error_counts, vis_htmls


def compute_word_metrics(
    references: list[list[Token]],
    hypotheses: list[list[Token]],
    count_substitutions: bool = True,
    visualize_errors: bool = False,
) -> dict[str, Any]:
    references = [tokens_as_words(tokens) for tokens in references]
    hypotheses = [tokens_as_words(tokens) for tokens in hypotheses]

    wo = jiwer.process_words(
        [[t.text.lower() for t in tokens] for tokens in references],
        [[t.text.lower() for t in tokens] for tokens in hypotheses],
        reference_transform=IDENTITY_TRANSFORM,
        hypothesis_transform=IDENTITY_TRANSFORM,
    )

    _, error_counts, vis_htmls = process_alignments(
        references,
        hypotheses,
        wo.alignments,
        count_substitutions=count_substitutions,
        visualize_errors=visualize_errors,
    )
    total_len = sum(len(tokens) for tokens in references)

    results = {
        "WER": wo.wer,
        "MER": wo.mer,
        "WIL": wo.wil,
        "ER_case": error_counts["case"] / total_len,
    }
    if visualize_errors:
        results["errors_html"] = vis_htmls
    return results


def compute_other_metrics(
    references: list[list[Token]],
    hypotheses: list[list[Token]],
    count_substitutions: bool = True,
    visualize_errors: bool = False,
) -> dict[str, Any]:
    wo = jiwer.process_words(
        [[t.text.lower() for t in tokens] for tokens in references],
        [[t.text.lower() for t in tokens] for tokens in hypotheses],
        reference_transform=IDENTITY_TRANSFORM,
        hypothesis_transform=IDENTITY_TRANSFORM,
    )

    counts, _, vis_htmls = process_alignments(
        references,
        hypotheses,
        wo.alignments,
        count_substitutions=count_substitutions,
        visualize_errors=visualize_errors,
    )

    results = {}
    for tag in [PUNCT, PAREN, LINE, SECT]:
        tg = tag[:4]
        H, S, D, I = counts[tag].H, counts[tag].S, counts[tag].D, counts[tag].I
        P = H / (H + S + I) if H + S + I else float("nan")
        R = H / (H + S + D) if H + S + D else float("nan")
        results[f"P_{tg}"] = P
        results[f"R_{tg}"] = R
        if P == float("nan") or R == float("nan"):
            results[f"F1_{tg}"] = float("nan")
        elif P + R == 0:
            results[f"F1_{tg}"] = 0.0
        else:
            results[f"F1_{tg}"] = 2 * P * R / (P + R)

    if visualize_errors:
        results["errors_html"] = vis_htmls

    return results


def compute_metrics(
    references: list[str],
    hypotheses: list[str],
    languages: Union[list[str], str] = "en",
    visualize_errors: bool = False,
) -> dict[str, Any]:
    """Compute all metrics for the given references and hypotheses.

    Args:
        references: A list of reference transcripts.
        hypotheses: A list of hypotheses.
        languages: The language of each reference transcript or a single language to use for all
            transcripts.
        visualize_errors: Whether to visualize errors.

    Returns:
        A dictionary of metrics. If `visualize_errors` is `True`, the dictionary will also contain
        an `errors_html` key with a list of HTML snippets visualizing the errors for each
        transcript.
    """
    if isinstance(languages, str):
        languages = [languages] * len(references)
    languages = [iso639.Language.match(lg).part1 for lg in languages]

    tokenizer = LyricsTokenizer()
    tokens_ref, tokens_hyp = [], []
    for i in range(len(references)):
        tokens_ref.append(tokenizer(references[i], language=languages[i]))
        tokens_hyp.append(tokenizer(hypotheses[i], language=languages[i]))

    results = {
        **compute_word_metrics(
            tokens_ref,
            tokens_hyp,
        ),
        **compute_other_metrics(
            tokens_ref,
            tokens_hyp,
            visualize_errors=visualize_errors,
        ),
    }
    return results
