"""Simple JSON-file-backed persistence for expenses.

A flat JSON file is used instead of a database because the assignment's
scope is small and a database would add setup overhead without real
benefit here. A module-level lock protects against corrupting the file
if two requests happen to write at the same time.

Every function here re-reads/re-writes the *entire* file rather than
appending or patching it. That's intentionally simple for this scale
(a handful to a few thousand expenses); it would not be the right
approach for a large or high-throughput dataset, where a database is
the correct next step.
"""
import json
import threading
from pathlib import Path
from typing import List

from src.models import Expense

# Resolved relative to this file's location (not the current working
# directory), so the data file always lands at the project root
# regardless of where `uvicorn` or `pytest` is invoked from.
DATA_FILE = Path(__file__).resolve().parent.parent / "expenses_data.json"

# Guards read-modify-write sequences against two concurrent requests
# (e.g. two near-simultaneous POSTs) interleaving their file writes.
_lock = threading.Lock()


def _read_raw() -> List[dict]:
    """Read the raw JSON list from disk, tolerating a missing or empty file."""
    if not DATA_FILE.exists():
        # Fresh checkout, no data file yet — an empty list, not an error.
        return []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        content = f.read().strip()
        return json.loads(content) if content else []


def load_expenses() -> List[Expense]:
    """Load all expenses from disk, parsed and validated as Expense models."""
    with _lock:
        raw = _read_raw()
    # Validation happens here (outside the lock) so we don't hold the
    # lock any longer than the actual file I/O requires.
    return [Expense(**item) for item in raw]


def save_expenses(expenses: List[Expense]) -> None:
    """Persist the full list of expenses to disk, overwriting the file."""
    # model_dump_json() -> json.loads() round-trip converts model fields
    # (e.g. `date`) into their JSON-safe representations before we write.
    payload = [json.loads(e.model_dump_json()) for e in expenses]
    with _lock:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with DATA_FILE.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)


def next_id(expenses: List[Expense]) -> int:
    """Return the next available integer id, starting from 1.

    IDs are derived from the current max, not a running counter, since
    we don't keep any state beyond what's on disk. Fine for this scale;
    a real database would use an auto-increment/sequence instead.
    """
    if not expenses:
        return 1
    return max(expense.id for expense in expenses) + 1
