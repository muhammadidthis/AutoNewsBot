from __future__ import annotations

from typing import Iterable

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer


def summarize_text(text: str, max_sentences: int = 3, language: str = "english") -> str:
    if not text:
        return ""
    try:
        parser = PlaintextParser.from_string(text, Tokenizer(language))
        summarizer = TextRankSummarizer()
        sentences = summarizer(parser.document, max_sentences)
        joined = " ".join(str(s) for s in sentences)
        # Fallback when nothing was produced
        return joined or text.split(". ")[:max_sentences][0]
    except Exception:
        return text


def summarize_paragraphs(paragraphs: Iterable[str], max_sentences: int = 3) -> str:
    combined = "\n".join(p for p in paragraphs if p)
    return summarize_text(combined, max_sentences=max_sentences)


