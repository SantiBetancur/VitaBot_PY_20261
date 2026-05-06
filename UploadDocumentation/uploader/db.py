from typing import Dict, Iterable, List, Optional
import logging

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .models import DocumentInsertRow


LOGGER = logging.getLogger(__name__)


class DatabaseClient:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.conn: Optional[psycopg.Connection] = None

    def __enter__(self) -> "DatabaseClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        self.close()

    def connect(self) -> None:
        self.conn = psycopg.connect(self.dsn, row_factory=dict_row)
        register_vector(self.conn)
        self._ensure_documents_table()

        LOGGER.info("Connected to PostgreSQL")

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            LOGGER.info("PostgreSQL connection closed")

    def commit(self) -> None:
        self._require_connection().commit()

    def rollback(self) -> None:
        conn = self._require_connection()
        if not conn.closed:
            conn.rollback()

    def delete_source_version(
        self,
        source: str,
        version: int,
        embedding_model: str,
    ) -> int:
        query = """
        DELETE FROM rag.documents
        WHERE source = %s
          AND version = %s
          AND embedding_model = %s;
        """

        with self._require_connection().cursor() as cur:
            cur.execute(query, (source, version, embedding_model))
            deleted = cur.rowcount

        return int(deleted)

    def insert_document_rows(self, rows: Iterable[DocumentInsertRow]) -> int:
        query = """
        INSERT INTO rag.documents (
            content,
            embedding,
            source,
            chunk_index,
            metadata,
            embedding_model,
            version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        records = []
        for row in rows:
            records.append(
                (
                    row.content,
                    row.embedding,
                    row.source,
                    row.chunk_index,
                    Jsonb(row.metadata),
                    row.embedding_model,
                    row.version,
                )
            )

        if not records:
            return 0

        with self._require_connection().cursor() as cur:
            cur.executemany(query, records)

        return len(records)

    def analyze_documents(self) -> None:
        query = "ANALYZE rag.documents;"
        with self._require_connection().cursor() as cur:
            cur.execute(query)

    def _ensure_documents_table(self) -> None:
        query = """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'rag'
              AND table_name = 'documents'
        ) AS found;
        """

        with self._require_connection().cursor() as cur:
            cur.execute(query)
            row: Dict[str, bool] = cur.fetchone()

        if not row or not row.get("found"):
            raise RuntimeError(
                "Table rag.documents was not found. Run SQL QUERIES/databaseInitConfig.sql first."
            )

    def _require_connection(self) -> psycopg.Connection:
        if self.conn is None:
            raise RuntimeError("PostgreSQL connection is not initialized")
        return self.conn
