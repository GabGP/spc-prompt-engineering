"""Standardized deterministic markdown templates for mock engine testing."""

CONFORMING_MARKDOWN = """## Core Synthesis
Statistical Process Control (SPC) provides rigorous analytical principles and quantitative methodologies to monitor transformation quality and operational latency.
By utilizing Shewhart control charts, the system distinguishes between common-cause system noise and assignable causes
requiring corrective engineering intervention, thereby ensuring long-term operational stability and predictable cycle times.
Continuous sampling of operational units allows real-time detection of process shifts, eliminating context bloat and stabilizing throughput.

## Technical Taxonomy
- **Common-Cause Variation:** Inherent, predictable system background noise inherent in standard execution under stable operating conditions.
- **Assignable-Cause Variation:** Identifiable, non-random disturbances necessitating diagnostic intervention and root-cause remediation.
- **Cycle Time (T):** Total elapsed duration in seconds required to complete end-to-end transformation of an individual input unit.
- **Deterministic Gate:** Strict Go/No-Go inspection evaluating structural section integrity, LaTeX syntax completeness, and schema rules.
- **Subgroup Rationality:** Consecutive temporal sampling preserving homogeneity within subgroups while exposing process shifts across subgroups.

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
The provided document excerpt focuses on foundational statistical learning methodologies and empirical data analysis workflows.
Statistical learning provides a comprehensive framework for modeling, estimating, and understanding structure in complex high-dimensional datasets.
The text systematically analyzes the distinction between supervised statistical learning, where an explicit supervising output response guides model estimation,
and unsupervised statistical learning, where latent structures, clusters, and variable relationships are discovered without external guidance.
Empirical applications span diverse scientific and commercial domains, including economic analysis, medical prognosis, genomics, and public policy evaluation.
No mathematical expressions or analytical formula definitions are present in this input unit.

## Technical Taxonomy
- **Statistical Learning:** Methodological collection of computational and statistical tools for data analysis and inference.
- **Supervised Learning:** Predictive mapping where target labels or output variables guide model training and error minimization.
- **Unsupervised Learning:** Exploratory analysis uncovering hidden groupings and associations without supervising targets.
- **Qualitative Domain:** Narrative exposition describing empirical dataset characteristics, predictor relationships, and observational goals.
- **Input Predictors:** Covariates and independent features utilized to explain response variation.

## Analytical Formulations
NONE RECORDED
"""
