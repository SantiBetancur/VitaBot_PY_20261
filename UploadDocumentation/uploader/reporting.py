from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from .models import ChunkExecutionReport, ChunkRecord


def _escape_code_block(content: str) -> str:
    if "```" not in content:
        return content
    return content.replace("```", "`\u200b``")


def _format_chunk(chunk: ChunkRecord) -> List[str]:
    lines: List[str] = []
    lines.append(f"#### Chunk {chunk.chunk_index}")
    lines.append(f"- Section: {chunk.section_title or 'N/A'}")
    lines.append(f"- Pages: {chunk.page_start}-{chunk.page_end}")
    lines.append(f"- Tokens: {chunk.token_count}")
    lines.append("")
    lines.append("```text")
    lines.append(_escape_code_block(chunk.content))
    lines.append("```")
    lines.append("")
    return lines


def build_chunk_report_markdown(
    run_started_at: datetime,
    reports: Iterable[ChunkExecutionReport],
) -> str:
    lines: List[str] = []
    lines.append("# Upload Documentation Chunk Report")
    lines.append("")
    lines.append(f"- Generated at: {run_started_at.isoformat(timespec='seconds')}")
    lines.append("")

    for report in reports:
        lines.append(f"## {report.file_name}")
        lines.append(f"- Source: {report.source}")
        lines.append(f"- Relative path: {report.relative_path}")
        lines.append(f"- File hash: {report.file_hash}")
        lines.append(f"- Pages extracted: {report.page_count}")
        lines.append(f"- Chunks: {report.chunk_count}")
        lines.append(f"- Status: {report.status}")
        if report.note:
            lines.append(f"- Note: {report.note}")
        lines.append("")

        for chunk in report.chunks:
            lines.extend(_format_chunk(chunk))

    return "\n".join(lines).rstrip() + "\n"


def write_chunk_report(
    report_path: Path,
    run_started_at: datetime,
    reports: Iterable[ChunkExecutionReport],
) -> Path:
    report_path = report_path.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_chunk_report_markdown(run_started_at=run_started_at, reports=reports),
        encoding="utf-8",
    )
    return report_path