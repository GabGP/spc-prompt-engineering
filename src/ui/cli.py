"""Command-line interface argument parsing and dispatching for spc-runner."""

import argparse
import sys

from src.ui.handlers import handle_run, handle_slice, handle_status


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser with standardized layout."""
    formatter = lambda prog: argparse.HelpFormatter(prog, max_help_position=32)
    parser = argparse.ArgumentParser(
        prog="spc",
        description="SPC Transformation Engine — Statistical Process Control & Prompt Engineering",
        formatter_class=formatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Execute transformation run",
        description="Execute single-page LLM transformation, inspection gate, and telemetry logging",
        formatter_class=formatter,
    )
    run_parser.add_argument(
        "-p", "--page", metavar="PATH", help="Input page PDF/text [default: auto-detect next]"
    )
    run_parser.add_argument(
        "-r", "--run-id", metavar="ID", type=int, help="Run ID override [default: next in CSV]"
    )
    run_parser.add_argument(
        "--phase", metavar="NAME", help="Phase override (e.g. Phase_I, Phase_II)"
    )
    run_parser.add_argument(
        "--reworks", metavar="N", type=int, default=3, help="Max rework attempts [default: 3]"
    )
    run_parser.add_argument(
        "--cause", metavar="TEXT", default="NONE", help="Special cause note [default: NONE]"
    )
    run_parser.add_argument(
        "--math", action="store_true", help="Flag if input contains analytical formulas"
    )
    run_parser.add_argument(
        "--mock",
        nargs="?",
        const="rework",
        default=None,
        choices=["rework", "pass", "fail", "latex", "empty_math"],
        help="Simulate run offline with staged responses [default: rework]",
    )
    run_parser.set_defaults(func=handle_run)

    status_parser = subparsers.add_parser(
        "status",
        help="Show system status",
        description="Display current experimental phase, factor settings, and run ledger statistics",
        formatter_class=formatter,
    )
    status_parser.set_defaults(func=handle_status)

    slice_parser = subparsers.add_parser(
        "slice",
        help="Slice textbook PDF",
        description="Slice pages from raw textbook PDF into individual target inputs",
        formatter_class=formatter,
    )
    slice_parser.add_argument(
        "-b", "--book", metavar="PATH", help="Path to source PDF [default: auto from data/raw]"
    )
    slice_parser.add_argument(
        "-s", "--start", metavar="PAGE", type=int, required=True, help="Starting page number (1-indexed)"
    )
    slice_parser.add_argument(
        "-e", "--end", metavar="PAGE", type=int, required=True, help="Ending page number (inclusive)"
    )
    slice_parser.add_argument(
        "-o", "--output-dir", metavar="DIR", default="data/inputs", help="Output directory [default: data/inputs]"
    )
    slice_parser.add_argument(
        "--sequential", action="store_true", help="Name output files sequentially starting from page_001.pdf"
    )
    slice_parser.add_argument(
        "--start-index", metavar="N", type=int, help="Custom starting index for output filenames [default: 1 if sequential]"
    )
    slice_parser.set_defaults(func=handle_slice)

    return parser


def app(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint callable from poetry/pip scripts."""
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)
