from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class SemanticUnit:
    text: str
    page_start: int
    page_end: int
    section_title: Optional[str] = None
    is_overlap: bool = False


@dataclass(frozen=True)
class ChunkRecord:
    chunk_index: int
    section_title: Optional[str]
    page_start: int
    page_end: int
    content: str
    token_count: int


@dataclass(frozen=True)
class DocumentInsertRow:
    content: str
    embedding: list
    source: str
    chunk_index: int
    metadata: Dict[str, Any]
    embedding_model: str
    version: int


@dataclass(frozen=True)
class ChunkExecutionReport:
    source: str
    file_name: str
    relative_path: str
    file_hash: str
    page_count: int
    chunk_count: int
    status: str
    note: Optional[str]
    chunks: List[ChunkRecord]
