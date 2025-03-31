"""Argument parser for the DAG build/execution CLI tool."""

import argparse
import os
from pathlib import Path

base = Path(__file__).parent.parent.parent

parser = argparse.ArgumentParser(description="DAG workflow CLI tool.")

# Global verbosity options
group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbosity", action="store_true", help="Enable verbose output")
group.add_argument("-q", "--quiet", action="store_true", help="Suppress all output")
group.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")

# Subcommands
subparsers = parser.add_subparsers(dest="command", help="Sub-command help", required=True)

# --- Merge ---
merge_parser = subparsers.add_parser("merge", help="Merge stage and target files")
merge_parser.add_argument(
    "--stages", "-s",
    default=base / "configs" / "stages.json",
    type=Path,
    help="Path to the stage file"
)
merge_parser.add_argument(
    "--targets", "-t",
    type=Path,
    required=True,
    help="Path to the target file"
)
merge_parser.add_argument(
    "--output", "-o",
    default="merged.json",
    help="Output file path"
)

# --- Run/Post shared options ---
def add_to_parser(par):
    """Add common run/post arguments to a subparser."""
    par.add_argument(
        "--stages", "-s",
        default="merged.json",
        help="Path to the merged file"
    )
    par.add_argument(
        "--max_workers", "-j",
        default=os.cpu_count() // 2,
        type=int,
        help="Number of parallel workers to run"
    )
    par.add_argument(
        "--only",
        type=str,
        help="Run only a specific stage (format: target:stage)"
    )
    par.add_argument(
        "--with-deps",
        action="store_true",
        help="Also run dependent posts recursively"
    )

# --- Run ---
run_parser = subparsers.add_parser("run", help="Run stages from the merged file")
add_to_parser(run_parser)

# --- Post ---
post_parser = subparsers.add_parser("post", help="Run only post-processing stages")
add_to_parser(post_parser)

# --- Collect ---
collect_parser = subparsers.add_parser("collect", help="Collect analyzed post output files")
collect_parser.add_argument(
    "--stages", "-s",
    default="merged.json",
    help="Path to the merged file"
)
collect_parser.add_argument(
    "--output", "-o",
    default="analyzed.json",
    help="Output file path"
)

# --- Report ---
report_parser = subparsers.add_parser("report", help="Report based on analyzed file")
report_parser.add_argument(
    "--analyzed",
    default="analyzed.json",
    help="Path to the analyzed file"
)
