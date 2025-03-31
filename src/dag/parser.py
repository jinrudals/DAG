import argparse
import os
from pathlib import Path

base = Path(__file__).parent.parent.parent

parser = argparse.ArgumentParser(description='Process some integers.')

group = parser.add_mutually_exclusive_group()

group.add_argument("-v", "--verbosity", action="store_true", help="Enable verbose output")
group.add_argument("-q", "--quiet", action="store_true", help="Suppress all output")
group.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")


subparsers = parser.add_subparsers(dest="command", help="Sub-command help", required=True)


## Merge
merge_parser = subparsers.add_parser("merge", help="Merge the given files")

merge_parser.add_argument(
    "--stages",
    "-s",
    default=base /"configs" / "stages.json",
    help="Path to the stage file",
    type=Path
)
merge_parser.add_argument(
    "--targets",
    "-t",
    help="Path to the target file",
    type=Path,
    required=True
)
merge_parser.add_argument(
    "--output",
    "-o",
    help="Output file path",
    default="merged.json"
)
## run / post parser
def add_to_parser(par):
    par.add_argument(
        "--stages",
        "-s",
        help="Path to the merged file",
        default="merged.json"
    )
    par.add_argument(
        "--max_workers",
        "-j",
        help="Number of workers",
        default=os.cpu_count() // 2,
        type=int
    )
    par.add_argument(
        "--only",
        help="Run only a specific stage (format: target:stage)",
        type=str
    )
    par.add_argument(
        "--with-deps",
        action="store_true",
        help="Also run dependent posts recursively"
    )
## Run
run_parser = subparsers.add_parser("run", help="Run the merged file")
add_to_parser(run_parser)
## Post
post_parser = subparsers.add_parser('post', help="Run only posts")
add_to_parser(post_parser)

## Analyze
collect_parser = subparsers.add_parser("collect", help="Collect Analyzed files")
collect_parser.add_argument(
    "--stages",
    "-s",
    help="Path to the merged file",
    default="merged.json"
)
collect_parser.add_argument(
    "--output",
    "-o",
    help="Output file path",
    default="analyzed.json"
)

## Report
report_parser = subparsers.add_parser("report", help="Report the merged file")
report_parser.add_argument(
    "--analyzed",
    help="Path to the analyzed file",
    default="analyzed.json"
)
