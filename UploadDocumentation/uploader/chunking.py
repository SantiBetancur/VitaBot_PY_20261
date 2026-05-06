from typing import List, Optional
import re

from .models import ChunkRecord, PageText, SemanticUnit
from .tokenizer import TokenCounter


_HEADING_PATTERN = re.compile(
    r"^(?:\d+(?:\.\d+)*)?\s*[A-Z][A-Za-z0-9\s\-_/&()]{2,100}$"
)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def _is_probable_heading(block: str) -> bool:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if len(lines) != 1:
        return False

    line = lines[0]
    if len(line) < 4 or len(line) > 100:
        return False
    if line.endswith("."):
        return False

    words = line.split()
    if len(words) > 12:
        return False

    if line.isupper():
        return True

    if not _HEADING_PATTERN.match(line):
        return False

    uppercase_words = sum(1 for word in words if word and word[0].isupper())
    return (uppercase_words / max(len(words), 1)) >= 0.6


def _split_page_blocks(text: str) -> List[str]:
    return [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]


def _build_semantic_units(pages: List[PageText]) -> List[SemanticUnit]:
    units = []
    current_section: Optional[str] = None

    for page in pages:
        blocks = _split_page_blocks(page.text)

        for block in blocks:
            if _is_probable_heading(block):
                current_section = block.strip()
                units.append(
                    SemanticUnit(
                        text=current_section,
                        page_start=page.page_number,
                        page_end=page.page_number,
                        section_title=current_section,
                    )
                )
                continue

            units.append(
                SemanticUnit(
                    text=block,
                    page_start=page.page_number,
                    page_end=page.page_number,
                    section_title=current_section,
                )
            )

    return units


def _split_large_unit(unit: SemanticUnit, max_tokens: int, token_counter: TokenCounter) -> List[SemanticUnit]:
    if token_counter.count(unit.text) <= max_tokens:
        return [unit]

    sentences = [
        sentence.strip() for sentence in _SENTENCE_SPLIT_PATTERN.split(unit.text) if sentence.strip()
    ]

    if len(sentences) <= 1:
        return [
            SemanticUnit(
                text=piece,
                page_start=unit.page_start,
                page_end=unit.page_end,
                section_title=unit.section_title,
                is_overlap=unit.is_overlap,
            )
            for piece in token_counter.split_text_by_token_limit(unit.text, max_tokens)
            if piece.strip()
        ]

    grouped = []
    current_group = []

    for sentence in sentences:
        candidate = " ".join(current_group + [sentence]).strip()

        if current_group and token_counter.count(candidate) > max_tokens:
            grouped.append(" ".join(current_group).strip())
            current_group = [sentence]
        else:
            current_group.append(sentence)

    if current_group:
        grouped.append(" ".join(current_group).strip())

    expanded_units = []

    for group_text in grouped:
        if token_counter.count(group_text) <= max_tokens:
            expanded_units.append(
                SemanticUnit(
                    text=group_text,
                    page_start=unit.page_start,
                    page_end=unit.page_end,
                    section_title=unit.section_title,
                    is_overlap=unit.is_overlap,
                )
            )
            continue

        for piece in token_counter.split_text_by_token_limit(group_text, max_tokens):
            if piece.strip():
                expanded_units.append(
                    SemanticUnit(
                        text=piece,
                        page_start=unit.page_start,
                        page_end=unit.page_end,
                        section_title=unit.section_title,
                        is_overlap=unit.is_overlap,
                    )
                )

    return expanded_units


def _build_chunk_record(chunk_index: int, chunk_units: List[SemanticUnit], token_counter: TokenCounter) -> ChunkRecord:
    content = "\n\n".join(unit.text.strip() for unit in chunk_units if unit.text.strip()).strip()
    page_start = min(unit.page_start for unit in chunk_units)
    page_end = max(unit.page_end for unit in chunk_units)

    section_title = None
    for unit in chunk_units:
        if unit.section_title:
            section_title = unit.section_title
            break

    return ChunkRecord(
        chunk_index=chunk_index,
        section_title=section_title,
        page_start=page_start,
        page_end=page_end,
        content=content,
        token_count=token_counter.count(content),
    )


def create_chunks(
    pages: List[PageText],
    chunk_size_tokens: int,
    chunk_overlap_ratio: float,
    token_counter: TokenCounter,
) -> List[ChunkRecord]:
    if not pages:
        return []

    if chunk_size_tokens <= 0:
        raise ValueError("chunk_size_tokens must be greater than 0")

    if chunk_overlap_ratio < 0 or chunk_overlap_ratio >= 1:
        raise ValueError("chunk_overlap_ratio must be in [0, 1)")

    semantic_units = _build_semantic_units(pages)
    if not semantic_units:
        return []

    expanded_units = []
    for unit in semantic_units:
        expanded_units.extend(_split_large_unit(unit, chunk_size_tokens, token_counter))

    chunks = []
    current_units = []
    overlap_tokens = int(chunk_size_tokens * chunk_overlap_ratio)

    for unit in expanded_units:
        candidate_units = current_units + [unit]
        candidate_text = "\n\n".join(u.text for u in candidate_units if u.text.strip()).strip()
        candidate_tokens = token_counter.count(candidate_text)

        if current_units and candidate_tokens > chunk_size_tokens:
            if len(current_units) == 1 and current_units[0].is_overlap:
                current_units = []
            else:
                chunk = _build_chunk_record(len(chunks), current_units, token_counter)
                chunks.append(chunk)
                current_units = []

                if overlap_tokens > 0:
                    overlap_text = token_counter.tail_text(chunk.content, overlap_tokens)
                    if overlap_text:
                        current_units.append(
                            SemanticUnit(
                                text=overlap_text,
                                page_start=chunk.page_end,
                                page_end=chunk.page_end,
                                section_title=chunk.section_title,
                                is_overlap=True,
                            )
                        )

                if current_units and current_units[0].is_overlap:
                    overlap_candidate = "\n\n".join(
                        u.text for u in (current_units + [unit]) if u.text.strip()
                    ).strip()
                    if token_counter.count(overlap_candidate) > chunk_size_tokens:
                        current_units = []

        current_units.append(unit)

    if current_units:
        if len(current_units) > 1 or not current_units[0].is_overlap:
            chunk = _build_chunk_record(len(chunks), current_units, token_counter)
            chunks.append(chunk)

    return chunks
