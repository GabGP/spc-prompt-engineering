"""Unit tests for spc.core.constants."""

from datetime import date
from spc.core.constants import (
    DateRange,
    Phase,
    PHASE_FACTORS,
    PHASE_WINDOWS,
    QualityGateRules,
    SPCConstants,
)


def test_phase_enum_values() -> None:
    """Verify phase string values match the experimental specification."""
    assert Phase.PHASE_I.value == "Phase_I"
    assert Phase.PHASE_II.value == "Phase_II"
    assert Phase.PHASE_III.value == "Phase_III"
    assert Phase.PHASE_IV.value == "Phase_IV"


def test_date_range_contains() -> None:
    """Verify DateRange inclusive boundary checking."""
    rng = DateRange(date(2026, 9, 2), date(2026, 9, 23))
    assert rng.contains(date(2026, 9, 2))
    assert rng.contains(date(2026, 9, 15))
    assert rng.contains(date(2026, 9, 23))
    assert not rng.contains(date(2026, 9, 1))
    assert not rng.contains(date(2026, 9, 24))


def test_phase_factors_mapping() -> None:
    """Verify experimental factors X1 (context) and X2 (SOP schema) by phase."""
    assert PHASE_FACTORS[Phase.PHASE_I] == (0, 0)
    assert PHASE_FACTORS[Phase.PHASE_II] == (1, 0)
    assert PHASE_FACTORS[Phase.PHASE_III] == (1, 1)
    assert PHASE_FACTORS[Phase.PHASE_IV] == (1, 1)


def test_shewhart_spc_constants() -> None:
    """Verify Shewhart I-MR constants for sample size n=2."""
    assert SPCConstants.D2 == 1.128
    assert SPCConstants.D4 == 3.267
    assert SPCConstants.D3 == 0.0
    expected_sigma_factor = 3.0 / 1.128
    assert abs(SPCConstants.INDIVIDUALS_SIGMA_FACTOR - expected_sigma_factor) < 1e-6


def test_quality_gate_rules() -> None:
    """Verify mandatory quality headers and empty formula clause."""
    assert len(QualityGateRules.REQUIRED_HEADERS) == 3
    assert "## Core Synthesis" in QualityGateRules.REQUIRED_HEADERS
    assert "## Technical Taxonomy" in QualityGateRules.REQUIRED_HEADERS
    assert "## Analytical Formulations" in QualityGateRules.REQUIRED_HEADERS
    assert QualityGateRules.EMPTY_FORMULA_MARKER == "NONE RECORDED"
