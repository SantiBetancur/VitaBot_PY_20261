from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .chunking import create_chunks
from .config import UploadConfig
from .db import DatabaseClient
from .embedding_openai import OpenAIEmbeddingClient
from .extract_pdf import extract_pdf_pages
from .models import ChunkExecutionReport, DocumentInsertRow
from .reporting import write_chunk_report
from .tokenizer import TokenCounter
from .utils import as_posix, list_pdf_files, sha256_file


LOGGER = logging.getLogger(__name__)


@dataclass
class UploadStats:
    discovered_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    inserted_chunks: int = 0
    deleted_chunks: int = 0


class DocumentationUploader:
    def __init__(self, config: UploadConfig) -> None:
        self.config = config
        self.token_counter = TokenCounter()
        self.embedder = None

        if not self.config.dry_run:
            self.embedder = OpenAIEmbeddingClient(
                api_key=self.config.openai_api_key,
                model_name=self.config.embed_model_name,
                expected_dimension=self.config.expected_embedding_dim,
            )

    def run(self) -> UploadStats:
        pdf_files = list_pdf_files(self.config.docs_root, max_files=self.config.max_files)
        stats = UploadStats(discovered_files=len(pdf_files))
        run_started_at = datetime.now().astimezone()
        chunk_reports: List[ChunkExecutionReport] = []

        LOGGER.info(
            "Upload started | docs_root=%s | product=%s | files=%s | dry_run=%s",
            self.config.docs_root,
            self.config.product,
            len(pdf_files),
            self.config.dry_run,
        )

        if not pdf_files:
            LOGGER.warning("No PDF files found in %s", self.config.docs_root)
            return stats

        if self.config.dry_run:
            for pdf_path in pdf_files:
                self._process_file_dry_run(pdf_path, stats, chunk_reports)

            self._write_chunk_report_if_requested(run_started_at, chunk_reports)
            return stats

        if not self.config.postgres_dsn:
            raise ValueError("PostgreSQL connection is required when dry_run is false")

        with DatabaseClient(self.config.postgres_dsn) as db:
            for pdf_path in pdf_files:
                self._process_file(db, pdf_path, stats, chunk_reports)

            db.analyze_documents()
            db.commit()

        self._write_chunk_report_if_requested(run_started_at, chunk_reports)

        LOGGER.info(
            "Upload finished | processed=%s | skipped=%s | failed=%s | inserted_chunks=%s | deleted_chunks=%s",
            stats.processed_files,
            stats.skipped_files,
            stats.failed_files,
            stats.inserted_chunks,
            stats.deleted_chunks,
        )

        return stats

    def _process_file_dry_run(
        self,
        pdf_path: Path,
        stats: UploadStats,
        chunk_reports: List[ChunkExecutionReport],
    ) -> None:
        try:
            source = self._build_source(pdf_path)
            pages = extract_pdf_pages(pdf_path)
            if not pages:
                stats.skipped_files += 1
                LOGGER.warning("Dry-run skip: no text extracted | file=%s", pdf_path)
                chunk_reports.append(
                    self._build_chunk_report(
                        pdf_path=pdf_path,
                        source=source,
                        pages=pages,
                        chunks=[],
                        status="skipped",
                        note="No text extracted from the PDF.",
                    )
                )
                return

            chunks = create_chunks(
                pages=pages,
                chunk_size_tokens=self.config.chunk_size_tokens,
                chunk_overlap_ratio=self.config.chunk_overlap_ratio,
                token_counter=self.token_counter,
            )

            if not chunks:
                stats.skipped_files += 1
                LOGGER.warning("Dry-run skip: no chunks generated | file=%s", pdf_path)
                chunk_reports.append(
                    self._build_chunk_report(
                        pdf_path=pdf_path,
                        source=source,
                        pages=pages,
                        chunks=[],
                        status="skipped",
                        note="Text was extracted, but chunking produced no chunks.",
                    )
                )
                return

            stats.processed_files += 1
            stats.inserted_chunks += len(chunks)

            chunk_reports.append(
                self._build_chunk_report(
                    pdf_path=pdf_path,
                    source=source,
                    pages=pages,
                    chunks=chunks,
                    status="dry-run",
                    note="Dry-run output only; nothing was written to the database.",
                )
            )

            LOGGER.info(
                "Dry-run processed | file=%s | chunks=%s",
                pdf_path.name,
                len(chunks),
            )
        except Exception:
            stats.failed_files += 1
            LOGGER.exception("Dry-run failed | file=%s", pdf_path)
            chunk_reports.append(
                self._build_chunk_report(
                    pdf_path=pdf_path,
                    source=self._build_source(pdf_path),
                    pages=[],
                    chunks=[],
                    status="failed",
                    note="Dry-run raised an exception before chunk output could be built.",
                )
            )

    def _process_file(
        self,
        db: DatabaseClient,
        pdf_path: Path,
        stats: UploadStats,
        chunk_reports: List[ChunkExecutionReport],
    ) -> None:
        try:
            source = self._build_source(pdf_path)
            pages = extract_pdf_pages(pdf_path)

            if not pages:
                stats.skipped_files += 1
                LOGGER.warning("Skip: no text extracted | source=%s", source)
                chunk_reports.append(
                    self._build_chunk_report(
                        pdf_path=pdf_path,
                        source=source,
                        pages=pages,
                        chunks=[],
                        status="skipped",
                        note="No text extracted from the PDF.",
                    )
                )
                return

            chunks = create_chunks(
                pages=pages,
                chunk_size_tokens=self.config.chunk_size_tokens,
                chunk_overlap_ratio=self.config.chunk_overlap_ratio,
                token_counter=self.token_counter,
            )

            if not chunks:
                stats.skipped_files += 1
                LOGGER.warning("Skip: no chunks generated | source=%s", source)
                chunk_reports.append(
                    self._build_chunk_report(
                        pdf_path=pdf_path,
                        source=source,
                        pages=pages,
                        chunks=[],
                        status="skipped",
                        note="Text was extracted, but chunking produced no chunks.",
                    )
                )
                return

            chunk_texts = [chunk.content for chunk in chunks]
            if self.embedder is None:
                raise RuntimeError("OpenAI embedder is not initialized")

            embeddings = self.embedder.embed_passages(
                texts=chunk_texts,
                batch_size=self.config.embed_batch_size,
            )

            if self.config.recreate_source_version:
                deleted = db.delete_source_version(
                    source=source,
                    version=self.config.version,
                    embedding_model=self.config.embed_model_name,
                )
                stats.deleted_chunks += deleted

            rows = self._build_document_rows(pdf_path, source, chunks, embeddings)
            inserted = db.insert_document_rows(rows)
            db.commit()

            stats.processed_files += 1
            stats.inserted_chunks += inserted

            LOGGER.info(
                "Inserted source | source=%s | chunks=%s",
                source,
                inserted,
            )

            chunk_reports.append(
                self._build_chunk_report(
                    pdf_path=pdf_path,
                    source=source,
                    pages=pages,
                    chunks=chunks,
                    status="inserted",
                    note=f"Inserted {inserted} chunks into rag.documents.",
                )
            )

        except Exception:
            db.rollback()
            stats.failed_files += 1
            LOGGER.exception("Failed source | file=%s", pdf_path)
            chunk_reports.append(
                self._build_chunk_report(
                    pdf_path=pdf_path,
                    source=self._build_source(pdf_path),
                    pages=[],
                    chunks=[],
                    status="failed",
                    note="Processing failed before chunk output could be written.",
                )
            )

    def _build_document_rows(
        self,
        pdf_path: Path,
        source: str,
        chunks,
        embeddings,
    ) -> List[DocumentInsertRow]:
        relative = pdf_path.relative_to(self.config.docs_root)
        relative_posix = as_posix(relative)
        section_path = as_posix(relative.parent) if str(relative.parent) != "." else ""
        file_hash = sha256_file(pdf_path)

        rows: List[DocumentInsertRow] = []

        for chunk, embedding in zip(chunks, embeddings):
            metadata: Dict[str, object] = {
                "product": self.config.product,
                "relative_path": relative_posix,
                "section_path": section_path,
                "file_name": pdf_path.name,
                "file_hash": file_hash,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "section_title": chunk.section_title,
                "token_count": chunk.token_count,
            }

            rows.append(
                DocumentInsertRow(
                    content=chunk.content,
                    embedding=embedding,
                    source=source,
                    chunk_index=chunk.chunk_index,
                    metadata=metadata,
                    embedding_model=self.config.embed_model_name,
                    version=self.config.version,
                )
            )

        return rows

    def _build_source(self, pdf_path: Path) -> str:
        relative = pdf_path.relative_to(self.config.docs_root)
        return f"{self.config.product}/{as_posix(relative)}"

    def _build_chunk_report(
        self,
        pdf_path: Path,
        source: str,
        pages,
        chunks,
        status: str,
        note: Optional[str],
    ) -> ChunkExecutionReport:
        relative = pdf_path.relative_to(self.config.docs_root)
        file_hash = sha256_file(pdf_path)
        return ChunkExecutionReport(
            source=source,
            file_name=pdf_path.name,
            relative_path=as_posix(relative),
            file_hash=file_hash,
            page_count=len(pages),
            chunk_count=len(chunks),
            status=status,
            note=note,
            chunks=chunks,
        )

    def _write_chunk_report_if_requested(
        self,
        run_started_at: datetime,
        chunk_reports: List[ChunkExecutionReport],
    ) -> None:
        if not self.config.chunks_report_path:
            return

        report_path = write_chunk_report(
            report_path=self.config.chunks_report_path,
            run_started_at=run_started_at,
            reports=chunk_reports,
        )
        LOGGER.info("Chunk report written | path=%s | files=%s", report_path, len(chunk_reports))
