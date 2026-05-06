from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import os


def _to_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    return default


@dataclass
class UploadConfig:
    project_root: Path
    upload_root: Path
    docs_root: Path
    chunks_report_path: Optional[Path]
    product: str
    version: int
    chunk_size_tokens: int
    chunk_overlap_ratio: float
    embed_model_name: str
    expected_embedding_dim: int
    embed_batch_size: int
    recreate_source_version: bool
    max_files: Optional[int]
    dry_run: bool
    log_level: str
    openai_api_key: str
    postgres_dsn: Optional[str]

    @classmethod
    def from_env(cls, project_root: Path, upload_root: Path) -> "UploadConfig":
        docs_root = Path(
            os.getenv(
                "UPLOAD_DOCS_ROOT",
                str(upload_root / "Documentation" / "Deluge"),
            )
        )

        if not docs_root.is_absolute():
            docs_root = (project_root / docs_root).resolve()

        max_files = os.getenv("UPLOAD_MAX_FILES")
        parsed_max_files = int(max_files) if max_files else None

        chunk_size_tokens = int(os.getenv("UPLOAD_CHUNK_SIZE_TOKENS", "600"))
        if chunk_size_tokens < 100:
            raise ValueError("UPLOAD_CHUNK_SIZE_TOKENS must be >= 100")

        chunk_overlap_ratio = float(os.getenv("UPLOAD_CHUNK_OVERLAP_RATIO", "0.15"))
        if chunk_overlap_ratio < 0 or chunk_overlap_ratio >= 1:
            raise ValueError("UPLOAD_CHUNK_OVERLAP_RATIO must be in [0, 1)")

        embed_batch_size = int(os.getenv("UPLOAD_EMBED_BATCH_SIZE", "64"))
        if embed_batch_size <= 0:
            raise ValueError("UPLOAD_EMBED_BATCH_SIZE must be greater than 0")

        dry_run = _to_bool(os.getenv("UPLOAD_DRY_RUN"), default=False)

        dsn = _resolve_postgres_dsn(required=not dry_run)

        return cls(
            project_root=project_root,
            upload_root=upload_root,
            docs_root=docs_root,
            chunks_report_path=None,
            product=os.getenv("UPLOAD_PRODUCT", "deluge").strip().lower(),
            version=int(os.getenv("UPLOAD_VERSION", "1")),
            chunk_size_tokens=chunk_size_tokens,
            chunk_overlap_ratio=chunk_overlap_ratio,
            embed_model_name=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small").strip(),
            expected_embedding_dim=int(os.getenv("OPENAI_EMBED_DIM", "1536")),
            embed_batch_size=embed_batch_size,
            recreate_source_version=_to_bool(
                os.getenv("UPLOAD_RECREATE_SOURCE_VERSION"),
                default=True,
            ),
            max_files=parsed_max_files,
            dry_run=dry_run,
            log_level=os.getenv("UPLOAD_LOG_LEVEL", "INFO").strip().upper(),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            postgres_dsn=dsn,
        )


def _append_sslmode_to_url(database_url: str, sslmode: str) -> str:
    parsed = urlparse(database_url)
    query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))

    if "sslmode" not in query_pairs and sslmode:
        query_pairs["sslmode"] = sslmode

    new_query = urlencode(query_pairs)
    return urlunparse(parsed._replace(query=new_query))


def _resolve_postgres_dsn(required: bool) -> Optional[str]:
    database_url = os.getenv("DATABASE_URL", "").strip()
    sslmode = os.getenv("POSTGRES_SSLMODE", "require").strip()

    if database_url:
        return _append_sslmode_to_url(database_url, sslmode)

    if required:
        raise ValueError("DATABASE_URL is missing. Set it in the repository root .env file.")

    return None
