"""Standardized deterministic markdown templates for mock engine testing."""

CONFORMING_MARKDOWN = """## Core Synthesis
Statistical Process Control (SPC) leverages Shewhart control charts to distinguish
between common-cause variation and assignable causes, stabilizing operational latency.

## Technical Taxonomy
- **Common Cause:** Natural, random, inherent variation in an established system.
- **Assignable Cause:** Specific, identifiable disturbance requiring root-cause intervention.
- **Cycle Time (T):** Elapsed real-time latency required to process an operational unit.

## Analytical Formulations
$$ \\bar{X} = \\frac{1}{n} \\sum_{i=1}^{n} X_i $$
$$ \\text{UCL} = \\bar{X} + A_2 \\bar{R} $$
$$ \\text{LCL} = \\bar{X} - A_2 \\bar{R} $$
"""

MISSING_HEADER_MARKDOWN = """## Core Synthesis
Defective output missing Technical Taxonomy section.

## Analytical Formulations
$$ \\bar{X} = \\frac{1}{n} \\sum_{i=1}^{n} X_i $$
"""

UNCLOSED_LATEX_MARKDOWN = """## Core Synthesis
LaTeX syntax error demonstration.

## Technical Taxonomy
- **Defect:** Unclosed LaTeX formula block.

## Analytical Formulations
$$ \\bar{X} = \\frac{1}{n} \\sum_{i=1}^{n} X_i
"""

MISSING_EMPTY_RULE_MARKDOWN = """## Core Synthesis
No mathematical expressions in this input unit.

## Technical Taxonomy
- **Qualitative Content:** Pure narrative without mathematical formulations.

## Analytical Formulations
No formulas were present in this excerpt.
"""

EMPTY_RULE_CONFORMING_MARKDOWN = """## Core Synthesis
No mathematical expressions in this input unit.

## Technical Taxonomy
- **Qualitative Content:** Pure narrative without mathematical formulations.

## Analytical Formulations
NONE RECORDED
"""
