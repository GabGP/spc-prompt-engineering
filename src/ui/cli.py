"""Command-line interface argument parsing and dispatching for spc-runner."""

import argparse
import sys

from src.ui.handlers import handle_run, handle_slice, handle_status


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser and subcommands."""
    parser = argparse.ArgumentParser(
        prog="spc", description="SPC Transformation & Prompt Engineering Engine"
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Execute transformation run")
    run_parser.add_argument("--page", "-p", help="Path to input PDF or text page")
    run_parser.add_argument("--phase", help="Override phase (e.g. Phase_I)")
    run_parser.add_argument("--run-id", type=int, help="Override sequential run ID")
    run_parser.add_argument(
        "--reworks", type=int, default=3, help="Max rework loops"
    )
    run_parser.add_argument(
        "--cause", default="NONE", help="Special assignable cause"
    )
    run_parser.add_argument(
        "--math", action="store_true", help="Flag if input contains math"
    )
    run_parser.set_defaults(func=handle_run)

    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.set_defaults(func=handle_status)

    slice_parser = subparsers.add_parser("slice", help="Slice textbook PDF")
    slice_parser.add_argument(
        "--book", "-b", required=True, help="Path to raw textbook PDF"
    )
    slice_parser.add_argument(
        "--start", "-s", type=int, required=True, help="Start page"
    )
    slice_parser.add_argument(
        "--end", "-e", type=int, required=True, help="End page"
    )
    slice_parser.add_argument(
        "--output-dir", "-o", default="data/inputs", help="Output directory"
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
