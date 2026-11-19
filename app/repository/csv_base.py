"""Low-level CSV table access.

Only this module knows about CSV files. Repositories compose it, so replacing
the storage medium means writing another table adapter, not editing services.
"""

import csv
import os
from pathlib import Path
from typing import Iterable, Sequence


class CsvTable:
    """Thin, dependency-free reader/writer for one CSV file."""

    def __init__(self, path: Path, fieldnames: Sequence[str]) -> None:
        self._path = Path(path)
        self._fieldnames = list(fieldnames)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def fieldnames(self) -> list[str]:
        return list(self._fieldnames)

    def ensure(self) -> None:
        """Create the file with headers when it does not exist yet."""
        if self._path.exists():
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self.write_rows([])

    def read_rows(self) -> list[dict[str, str]]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader if any((value or "").strip() for value in row.values())]

    def write_rows(self, rows: Iterable[dict[str, str]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self._fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in self._fieldnames})
        os.replace(temp_path, self._path)

    def append_row(self, row: dict[str, str]) -> None:
        rows = self.read_rows()
        rows.append(row)
        self.write_rows(rows)

    def next_id(self, id_field: str) -> int:
        rows = self.read_rows()
        used = [int(row[id_field]) for row in rows if (row.get(id_field) or "").strip().isdigit()]
        return max(used, default=0) + 1
