"""Read a changing MUMUT master workbook without hard-coded row counts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import pandas as pd

REQUIRED_SHEETS = ("STORE", "STORE_HOUR", "ORIGIN", "ROUTE_MATRIX", "REASON_CODE", "REQUEST_SCHEMA")


@dataclass(frozen=True)
class MasterWorkbook:
    path: Path
    sha256: str
    tables: dict[str, pd.DataFrame]


def find_master_file(master_dir: Path) -> Path:
    files = sorted(master_dir.glob("*.xlsx"))
    if len(files) != 1:
        raise ValueError(f"Expected exactly one .xlsx file in {master_dir}, found {len(files)}")
    return files[0]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_master(path: Path) -> MasterWorkbook:
    workbook = pd.ExcelFile(path)
    try:
        missing = sorted(set(REQUIRED_SHEETS) - set(workbook.sheet_names))
        if missing:
            raise ValueError(f"Missing required sheets: {', '.join(missing)}")
        # Header position is explicit; data row counts and columns remain dynamic.
        tables = {name: pd.read_excel(workbook, sheet_name=name, header=3) for name in workbook.sheet_names}
    finally:
        workbook.close()
    return MasterWorkbook(path=path, sha256=file_sha256(path), tables=tables)
