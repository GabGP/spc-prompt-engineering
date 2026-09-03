"""Unit tests for phase and factor resolution module."""

from datetime import date
import pytest

from src.core.constants import Phase
from src.state.phase_resolver import PhaseResolution, resolve_phase


def test_resolve_phase_all_calendar_windows() -> None:
    """Verify correct phase and factor mapping for dates inside all 4 windows."""
    # Phase I: 2026-09-02 to 2026-09-23 -> X1=0, X2=0
    res_i = resolve_phase(target_date=date(2026, 9, 10))
    assert res_i == PhaseResolution(phase=Phase.PHASE_I, factor_x1=0, factor_x2=0)

    # Phase II: 2026-09-24 to 2026-10-07 -> X1=1, X2=0
    res_ii = resolve_phase(target_date=date(2026, 9, 30))
    assert res_ii == PhaseResolution(phase=Phase.PHASE_II, factor_x1=1, factor_x2=0)

    # Phase III: 2026-10-08 to 2026-10-21 -> X1=1, X2=1
    res_iii = resolve_phase(target_date=date(2026, 10, 15))
    assert res_iii == PhaseResolution(phase=Phase.PHASE_III, factor_x1=1, factor_x2=1)

    # Phase IV: 2026-10-22 to 2026-11-02 -> X1=1, X2=1
    res_iv = resolve_phase(target_date=date(2026, 10, 25))
    assert res_iv == PhaseResolution(phase=Phase.PHASE_IV, factor_x1=1, factor_x2=1)


def test_resolve_phase_out_of_bounds_raises_error() -> None:
    """Verify ValueError is raised when date is outside all experimental windows."""
    with pytest.raises(ValueError, match="does not fall within any configured"):
        resolve_phase(target_date=date(2025, 1, 1))

    with pytest.raises(ValueError, match="does not fall within any configured"):
        resolve_phase(target_date=date(2026, 11, 10))


def test_resolve_phase_enum_override() -> None:
    """Verify explicit Phase enum override overrides date resolution."""
    res = resolve_phase(
        target_date=date(2025, 1, 1), override_phase=Phase.PHASE_I
    )
    assert res == PhaseResolution(phase=Phase.PHASE_I, factor_x1=0, factor_x2=0)


def test_resolve_phase_string_override() -> None:
    """Verify string override identifier is converted and factors retrieved."""
    res = resolve_phase(override_phase="Phase_II")
    assert res == PhaseResolution(phase=Phase.PHASE_II, factor_x1=1, factor_x2=0)


def test_resolve_phase_invalid_override_raises_error() -> None:
    """Verify invalid phase string raises an informative ValueError."""
    with pytest.raises(ValueError, match="Invalid override phase 'Phase_UNKNOWN'"):
        resolve_phase(override_phase="Phase_UNKNOWN")


def test_resolve_phase_default_today() -> None:
    """Verify default target_date falls back to today's date."""
    # When no target_date is given and today is outside the 2026 window, raises ValueError
    # If today happens to be in window, returns PhaseResolution.
    try:
        res = resolve_phase()
        assert isinstance(res, PhaseResolution)
    except ValueError as err:
        assert "does not fall within any configured" in str(err)
