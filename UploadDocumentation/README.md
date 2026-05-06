# UploadDocumentation

Local uploader for populating `rag.documents` from PDF documentation.

This program is designed to run locally and is not intended to run inside Catalyst functions.

## What it does

1. Discovers PDF files inside `UploadDocumentation/Documentation/Deluge` (or custom path).
2. Extracts and cleans text from each PDF.
3. Builds semantic chunks with token limit and overlap.
4. Calls OpenAI embeddings API (`text-embedding-3-small` by default).
5. Inserts rows into `rag.documents` in PostgreSQL/Supabase.

Extraction fallback order:

1. pypdf text extraction
2. PyMuPDF text extraction
3. OCR fallback (Tesseract)

## What it does not do

1. It does not handle chatbot responses.
2. It does not modify `app.users`, `app.sessions`, or `app.messages`.
3. It does not run as a Catalyst function.

## Environment variables

Read from the repository root `.env` only.

Required:

1. `OPENAI_API_KEY`
2. `CLAUDE_API_KEY`
3. `DATABASE_URL`

Optional:

1. `OPENAI_EMBED_MODEL` (default `text-embedding-3-small`)
2. `OPENAI_EMBED_DIM` (default `1536`)
3. `UPLOAD_DOCS_ROOT` (default `UploadDocumentation/Documentation/Deluge`)
4. `UPLOAD_PRODUCT` (default `deluge`)
5. `UPLOAD_VERSION` (default `1`)
6. `UPLOAD_CHUNK_SIZE_TOKENS` (default `600`)
7. `UPLOAD_CHUNK_OVERLAP_RATIO` (default `0.15`)
8. `UPLOAD_EMBED_BATCH_SIZE` (default `64`)
9. `UPLOAD_RECREATE_SOURCE_VERSION` (default `true`)
10. `UPLOAD_MAX_FILES` (optional)
11. `UPLOAD_DRY_RUN` (default `false`)
12. `UPLOAD_LOG_LEVEL` (default `INFO`)
13. `UPLOAD_OCR_LANG` (default `eng`)
14. `UPLOAD_OCR_ZOOM` (default `2.0`)
15. `TESSERACT_CMD` (optional absolute path to tesseract executable)

## Install

From `UploadDocumentation` folder:

```bash
pip install -r requirements.txt
```

If your PDFs are image-based/scanned, OCR requires Tesseract installed in the OS.

Windows example:

1. Install Tesseract OCR.
2. Set `TESSERACT_CMD` in env if `tesseract` is not in PATH.

Example:

```env
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe
UPLOAD_OCR_LANG=eng
```

## Run

From `UploadDocumentation` folder:

```bash
python run_upload.py
```

Useful examples:

```bash
python run_upload.py --dry-run
python run_upload.py --max-files 10
python run_upload.py --product deluge --version 1
python run_upload.py --docs-root UploadDocumentation/Documentation/Deluge
python run_upload.py --no-recreate
python run_upload.py --max-files 1 --chunks-report UploadDocumentation/runs/chunks-report.md
```

The uploader reads the same root `.env` file as the backend, so there is no separate `UploadDocumentation/.env` anymore.

If you pass `--chunks-report`, the uploader writes a Markdown file with the extracted chunks for each processed PDF in that execution. This is useful for checking exactly what text was extracted, how it was split into chunks, and what page ranges each chunk came from.

## Notes

1. Ensure schema exists before first run: `SQL QUERIES/databaseInitConfig.sql`.
2. The uploader checks that `rag.documents` exists and fails fast if missing.
3. Recreate mode deletes previous rows by `source + version + embedding_model` before inserting new chunks.
