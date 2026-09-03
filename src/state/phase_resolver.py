"""Calendar date to experimental Phase and Factor (X1, X2) resolution."""

from datetime import UTC, date, datetime
from typing import NamedTuple

from src.core.constants import PHASE_FACTORS, PHASE_WINDOWS, Phase


class PhaseResolution(NamedTuple):
    """Resolved experimental phase and factor settings."""

    phase: Phase
    factor_x1: int
    factor_x2: int


def resolve_phase(
    target_date: date | None = None,
    override_phase: Phase | str | None = None,
) -> PhaseResolution:
    """Resolve the active experimental phase and factors (X1, X2).

    Args:
        target_date: Date to evaluate against experimental phase windows.
            Defaults to today's date if not provided.
        override_phase: Optional phase identifier to bypass calendar lookup.

    Returns:
        PhaseResolution containing phase enum, factor_x1, and factor_x2.

    Raises:
        ValueError: If target_date falls outside all defined phase windows,
            or if override_phase is not a valid Phase.
    """
    if override_phase is not None:
        if isinstance(override_phase, Phase):
            selected_phase = override_phase
        else:
            try:
                selected_phase = Phase(str(override_phase))
            except ValueError as err:
                valid = ", ".join(p.value for p in Phase)
                raise ValueError(
                    f"Invalid override phase '{override_phase}'. Must be one of: {valid}"
                ) from err

        x1, x2 = PHASE_FACTORS[selected_phase]
        return PhaseResolution(phase=selected_phase, factor_x1=x1, factor_x2=x2)

    eval_date = (
        target_date if target_date is not None else datetime.now(UTC).date()
    )

    for phase, date_range in PHASE_WINDOWS.items():
        if date_range.contains(eval_date):
            x1, x2 = PHASE_FACTORS[phase]
            return PhaseResolution(phase=phase, factor_x1=x1, factor_x2=x2)

    raise ValueError(
        f"Date {eval_date.isoformat()} does not fall within any configured "
        "experimental phase window. Specify an explicit phase override."
    )
