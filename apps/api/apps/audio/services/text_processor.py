import logging
import re

logger = logging.getLogger(__name__)


class AudioTextSegmenter:
    """Segments long educational texts into sequential, bounded chunks for TTS synthesis.

    Guarantees:
    1. Zero loss or duplication of sentences.
    2. Boundaries honor natural pauses (paragraphs, sentences, punctuation, Arabic semicolons/question marks).
    3. Never splits in the middle of a word.
    4. Each chunk respects the provider limit (default 2500 characters, safe for OpenAI 4096 and ElevenLabs 5000).
    """

    DEFAULT_MAX_CHUNK_CHARS = 2500
    SENTENCE_ENDINGS = re.compile(r"(?<=[.!?؟؛])\s+")

    @classmethod
    def segment_text(cls, text: str, max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS) -> list[str]:
        """Segments text into an ordered list of strings each <= max_chunk_chars."""
        if not text or not text.strip():
            return []

        cleaned = text.strip()
        if len(cleaned) <= max_chunk_chars:
            return [cleaned]

        paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
        chunks: list[str] = []
        current_chunk = ""

        for para in paragraphs:
            # If paragraph itself fits in current chunk
            candidate = f"{current_chunk}\n\n{para}".strip() if current_chunk else para
            if len(candidate) <= max_chunk_chars:
                current_chunk = candidate
                continue

            # If current chunk has content and candidate exceeds limit, flush current chunk
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # If paragraph itself is within limit, start new chunk
            if len(para) <= max_chunk_chars:
                current_chunk = para
                continue

            # Paragraph is longer than max_chunk_chars: split by sentence
            sentences = [s.strip() for s in cls.SENTENCE_ENDINGS.split(para) if s.strip()]
            for sent in sentences:
                candidate_sent = f"{current_chunk} {sent}".strip() if current_chunk else sent
                if len(candidate_sent) <= max_chunk_chars:
                    current_chunk = candidate_sent
                    continue

                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""

                # If sentence itself is still too long, split by clause or words
                if len(sent) <= max_chunk_chars:
                    current_chunk = sent
                else:
                    sub_chunks = cls._split_oversized_sentence(sent, max_chunk_chars)
                    for sc in sub_chunks:
                        if len(sc) <= max_chunk_chars:
                            chunks.append(sc)
                        else:
                            # Hard wrap on space boundary
                            chunks.extend(cls._split_by_words(sc, max_chunk_chars))

        if current_chunk:
            chunks.append(current_chunk)

        # Verification check: no empty chunk
        final_chunks = [c.strip() for c in chunks if c.strip()]
        logger.debug(
            "Segmented text into %d chunks (total chars: %d)", len(final_chunks), len(cleaned)
        )
        return final_chunks

    @classmethod
    def _split_oversized_sentence(cls, sentence: str, max_chunk_chars: int) -> list[str]:
        """Splits an oversized sentence along clause delimiters (commas, colons, Arabic commas)."""
        delimiters = re.compile(r"(?<=[,،:;])\s+")
        clauses = [c.strip() for c in delimiters.split(sentence) if c.strip()]
        res = []
        buf = ""
        for c in clauses:
            cand = f"{buf} {c}".strip() if buf else c
            if len(cand) <= max_chunk_chars:
                buf = cand
            else:
                if buf:
                    res.append(buf)
                buf = c
        if buf:
            res.append(buf)
        return res

    @classmethod
    def _split_by_words(cls, text: str, max_chunk_chars: int) -> list[str]:
        """Last resort word-boundary splitter for sentences without punctuation."""
        words = text.split()
        res = []
        buf = []
        curr_len = 0
        for w in words:
            w_len = len(w) + (1 if buf else 0)
            if curr_len + w_len <= max_chunk_chars:
                buf.append(w)
                curr_len += w_len
            else:
                if buf:
                    res.append(" ".join(buf))
                buf = [w]
                curr_len = len(w)
        if buf:
            res.append(" ".join(buf))
        return res
