"""Main entry point for DAG build and execution tool."""

import json
import os

from . import logger as lg
from . import parser
from . import runner
from . import builder

logger = lg.get_logger(__name__)


def set_logger(args):
    """Set logging level based on CLI arguments."""
    if args.verbosity:
        logger.setLevel(lg.logging.INFO)
    if args.debug:
        logger.setLevel(lg.logging.DEBUG)
    if args.quiet:
        logger.setLevel(lg.logging.ERROR)

    logger.addHandler(lg.logging.StreamHandler())


def main():
    """Parse arguments and dispatch commands."""
    parserd = parser.parser
    args = parserd.parse_args()
    set_logger(args)
    logger.debug("Arguments: %s", args)

    if args.command == "merge":
        merge(args)
    if args.command == "run":
        run(args)
    if args.command == "collect":
        collect(args)
    if args.command == "post":
        run(args, "post")


def merge_items(args):
    """Load stages and targets and perform merging."""
    with open(args.stages, encoding="utf-8") as f:
        stages = json.load(f)
    with open(args.targets, encoding="utf-8") as f:
        targets = json.load(f)
    b = builder.Builder(stages, targets)
    return b.build()


def merge(args):
    """Write merged stage definitions to output JSON."""
    combined = merge_items(args)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=4)


def run(args, mode="all"):
    """Execute DAG stages or post steps."""
    with open(args.stages, encoding="utf-8") as f:
        all_stages = json.load(f)

    stages = all_stages

    if args.only:
        if args.only not in all_stages:
            raise ValueError(f"Stage '{args.only}' not found in merged file")

        def collect_with_deps(stage_name, visited):
            if stage_name in visited:
                return
            visited.add(stage_name)
            stage = all_stages[stage_name]
            for dep in stage.get("after", []):
                collect_with_deps(dep, visited)

        selected = set()
        if args.with_deps:
            collect_with_deps(args.only, selected)
        selected.add(args.only)

        stages = {k: all_stages[k] for k in selected}

        for v in stages.values():
            v["before"] = [b for b in v.get("before", []) if b in stages]
            v["after"] = [a for a in v.get("after", []) if a in stages]

    runner.Runner.create_from_dict(stages).launch(
        max_workers=args.max_workers,
        mode=mode
    )


def collect(args):
    """Collect post outputs from executed stages into a single JSON report."""
    with open(args.stages, encoding="utf-8") as f:
        stages = json.load(f)

    runs = runner.Runner.create_from_dict(stages)
    outputs = {}

    for name, node in runs.nodes.items():
        if node.post:
            directory = node.post.get("directory", "")
            output = node.post.get("output", "")
            filename = f"{directory}/{output}"
            if not os.path.isfile(filename):
                outputs[name] = {
                    "status": "failed",
                    "content": "File not found",
                    "filename": filename
                }
                continue

            with open(filename, encoding="utf-8") as f:
                outputs[name] = {
                    "status": "unverified",
                    "content": f.read(),
                    "filename": filename
                }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=4)
