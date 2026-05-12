from pathlib import Path
from typing import List, Optional
import hashlib


def list_pdf_files(docs_root: Path, max_files: Optional[int] = None) -> List[Path]:
    if not docs_root.exists():
        return []

    files = sorted(path for path in docs_root.rglob("*.pdf") if path.is_file())

    if max_files is not None and max_files >= 0:
        return files[:max_files]

    return files


def sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()

    with file_path.open("rb") as file_obj:
        while True:
            chunk = file_obj.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def as_posix(path: Path) -> str:
    return path.as_posix().replace("\\\\", "/")
