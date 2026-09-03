"""Resolves input documents and source books for transformation runs and slicing."""

import re
from pathlib import Path


def natural_sort_key(path: Path) -> list[int | str]:
    """Split path filename into numeric and text chunks for natural sorting."""
    return [
        int(chunk) if chunk.isdigit() else chunk.lower()
        for chunk in re.split(r"(\d+)", path.name)
    ]


def discover_input_files(inputs_dir: Path | str = "data/inputs") -> list[Path]:
    """Find and return all valid input documents sorted in natural order."""
    p = Path(inputs_dir)
    if not p.exists() or not p.is_dir():
        return []

    valid_extensions = {".pdf", ".txt", ".md"}
    candidates = [
        item
        for item in p.iterdir()
        if item.is_file()
        and not item.name.startswith(".")
        and item.suffix.lower() in valid_extensions
    ]
    candidates.sort(key=natural_sort_key)
    return candidates


def resolve_input_path(
    explicit_page: str | Path | None,
    run_id: int,
    inputs_dir: Path | str = "data/inputs",
) -> Path:
    """Resolve target input document for a given run ID.

    If explicit_page is provided, it is returned if it exists.
    Otherwise, candidates in inputs_dir are discovered and ordered:
      - If run_id is within range (1-indexed), candidate at run_id - 1 is selected.
    """
    if explicit_page:
        path = Path(explicit_page)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path.as_posix()}")
        return path

    candidates = discover_input_files(inputs_dir)
    if not candidates:
        dir_name = Path(inputs_dir).as_posix()
        raise FileNotFoundError(
            f"No input files found in '{dir_name}'. "
            "Run 'spc slice' to prepare input pages or specify -p/--page."
        )

    if 1 <= run_id <= len(candidates):
        return candidates[run_id - 1]

    dir_name = Path(inputs_dir).as_posix()
    raise IndexError(
        f"Input file for Run #{run_id:03d} not found: '{dir_name}' contains "
        f"{len(candidates)} file(s), but requested run exceeds available inputs."
    )


def resolve_source_book(
    explicit_book: str | Path | None,
    raw_dir: Path | str = "data/raw",
    data_dir: Path | str = "data",
) -> Path:
    """Discover or validate the source textbook PDF for slicing."""
    if explicit_book:
        src = Path(explicit_book)
        if not src.exists():
            raise FileNotFoundError(f"Source textbook PDF not found: {src.as_posix()}")
        return src

    r_dir = Path(raw_dir)
    d_dir = Path(data_dir)
    candidates = list(r_dir.glob("*.pdf")) if r_dir.exists() else []
    if not candidates and d_dir.exists():
        candidates = [p for p in d_dir.glob("*.pdf") if p.is_file()]

    if len(candidates) == 1:
        return candidates[0]

    msg = "Multiple PDFs found in" if len(candidates) > 1 else "No PDF found in"
    raise ValueError(f"{msg} data/raw/ or data/. Specify -b / --book PATH.")
