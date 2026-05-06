from pathlib import Path
import argparse
import os

from dotenv import load_dotenv

from uploader.config import UploadConfig
from uploader.logging_utils import setup_logging
from uploader.pipeline import DocumentationUploader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate rag.documents from local documentation PDFs"
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="Optional path to .env file. Defaults to project_root/.env",
    )
    parser.add_argument(
        "--docs-root",
        default=None,
        help="Documentation root path for PDF discovery",
    )
    parser.add_argument(
        "--product",
        default=None,
        help="Product label to store in metadata/source (example: deluge)",
    )
    parser.add_argument(
        "--version",
        type=int,
        default=None,
        help="Version number stored in rag.documents.version",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help="Chunk size in tokens",
    )
    parser.add_argument(
        "--overlap",
        type=float,
        default=None,
        help="Chunk overlap ratio (example: 0.15)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="OpenAI embeddings batch size",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Limit number of PDF files processed",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run parsing and chunking without calling OpenAI or DB",
    )
    parser.add_argument(
        "--no-recreate",
        action="store_true",
        help="Do not delete existing source+version rows before inserting",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    parser.add_argument(
        "--chunks-report",
        default=None,
        help="Optional Markdown file path to write the extracted chunks for this run",
    )
    return parser.parse_args()


def resolve_path(base: Path, maybe_relative: str) -> Path:
    candidate = Path(maybe_relative)
    if candidate.is_absolute():
        return candidate
    return (base / candidate).resolve()


def main() -> int:
    args = parse_args()

    if args.dry_run:
        os.environ["UPLOAD_DRY_RUN"] = "true"

    upload_root = Path(__file__).resolve().parent
    project_root = upload_root.parent

    default_env_path = project_root / ".env"

    if args.env_file:
        env_path = resolve_path(project_root, args.env_file)
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
    elif default_env_path.exists():
        load_dotenv(dotenv_path=default_env_path, override=False)

    config = UploadConfig.from_env(project_root=project_root, upload_root=upload_root)

    if args.docs_root:
        config.docs_root = resolve_path(project_root, args.docs_root)

    if args.product:
        config.product = args.product.strip().lower()

    if args.version is not None:
        config.version = args.version

    if args.chunk_size is not None:
        config.chunk_size_tokens = args.chunk_size

    if args.overlap is not None:
        config.chunk_overlap_ratio = args.overlap

    if args.batch_size is not None:
        config.embed_batch_size = args.batch_size

    if args.max_files is not None:
        config.max_files = args.max_files

    if args.dry_run:
        config.dry_run = True

    if args.no_recreate:
        config.recreate_source_version = False

    if args.log_level:
        config.log_level = args.log_level.upper()

    if args.chunks_report:
        config.chunks_report_path = resolve_path(project_root, args.chunks_report)

    setup_logging(config.log_level)

    uploader = DocumentationUploader(config)
    stats = uploader.run()

    print("Upload summary")
    print(f"- PDF files discovered: {stats.discovered_files}")
    print(f"- Files processed: {stats.processed_files}")
    print(f"- Files skipped: {stats.skipped_files}")
    print(f"- Files failed: {stats.failed_files}")
    print(f"- Chunks inserted: {stats.inserted_chunks}")
    print(f"- Chunks deleted (recreate mode): {stats.deleted_chunks}")

    return 1 if stats.failed_files > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
