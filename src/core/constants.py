"""Statistical constants, calendar phase windows, and quality gate rules."""

from datetime import date
from enum import Enum
from typing import NamedTuple


class Phase(str, Enum):
    """Experimental phase identifiers."""

    PHASE_I = "Phase_I"
    PHASE_II = "Phase_II"
    PHASE_III = "Phase_III"
    PHASE_IV = "Phase_IV"


class DateRange(NamedTuple):
    """Start and end dates (inclusive) for an experimental phase window."""

    start: date
    end: date

    def contains(self, target_date: date) -> bool:
        """Check if target_date falls within the inclusive range."""
        return self.start <= target_date <= self.end


# Experimental phase calendar boundaries (2026 academic timeline)
PHASE_WINDOWS: dict[Phase, DateRange] = {
    Phase.PHASE_I: DateRange(date(2026, 9, 2), date(2026, 9, 23)),
    Phase.PHASE_II: DateRange(date(2026, 9, 24), date(2026, 10, 7)),
    Phase.PHASE_III: DateRange(date(2026, 10, 8), date(2026, 10, 21)),
    Phase.PHASE_IV: DateRange(date(2026, 10, 22), date(2026, 11, 2)),
}

# Factor levels (X1: Context Buffer, X2: Schema SOP) mapped by Phase
PHASE_FACTORS: dict[Phase, tuple[int, int]] = {
    Phase.PHASE_I: (0, 0),
    Phase.PHASE_II: (1, 0),
    Phase.PHASE_III: (1, 1),
    Phase.PHASE_IV: (1, 1),
}


class SPCConstants:
    """Shewhart Individuals–Moving Range (I-MR) chart constants for n=2."""

    # Unbiasing factor for sample size n=2
    D2: float = 1.128

    # Moving Range Upper Control Limit multiplier (n=2)
    D4: float = 3.267

    # Moving Range Lower Control Limit multiplier (n=2)
    D3: float = 0.0

    # Individuals 3-sigma multiplier: 3 / d2 ≈ 2.6596
    INDIVIDUALS_SIGMA_FACTOR: float = 3.0 / D2


class QualityGateRules:
    """Deterministic criteria for the Go / No-Go inspection gate."""

    # Mandatory Markdown headers that must appear in conforming outputs
    REQUIRED_HEADERS: tuple[str, ...] = (
        "## Core Synthesis",
        "## Technical Taxonomy",
        "## Analytical Formulations",
    )

    # Empty handling rule: exact text required if no math formulas exist
    EMPTY_FORMULA_MARKER: str = "NONE RECORDED"
