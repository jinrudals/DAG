import json
import os

from . import logger as lg
from . import parser
from . import runner
from . import builder

logger = lg.getLogger(__name__)

def set_logger(args):
    if args.verbosity:
        logger.setLevel(lg.logging.INFO)
    if args.debug:
        logger.setLevel(lg.logging.DEBUG)
    if args.quiet:
        logger.setLevel(lg.logging.ERROR)

    logger.addHandler(lg.logging.StreamHandler())

def main():
    parserd = parser.parser
    args = parserd.parse_args()
    set_logger(args)
    logger.debug(f"Arguments: {args}")
    if args.command == "merge":
        merge(args)
    if args.command == "run":
        run(args)
    if args.command == "collect":
        collect(args)
    if args.command == "post":
        run(args, "post")

def merge_items(args):
    with open(args.stages) as f:
        stages = json.load(f)
    with open(args.targets) as f:
        targets = json.load(f)
    b = builder.Builder(stages, targets)
    combined = b.build()
    return combined

def merge(args):
    combined = merge_items(args)
    with open(args.output, "w") as f:
        json.dump(combined, f, indent=4)

def run(args, mode="all"):
    with open(args.stages) as f:
        all_stages = json.load(f)

    stages = all_stages

    if args.only:
        if args.only not in all_stages:
            raise ValueError(f"Stage '{args.only}' not found in merged file")

        # Recursive dependency resolver
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

        # Remove non-existent links to unselected stages
        for v in stages.values():
            v["before"] = [b for b in v.get("before", []) if b in stages]
            v["after"] = [a for a in v.get("after", []) if a in stages]

    runner.Runner.create_from_dict(stages).launch(
        max_workers=args.max_workers,
        mode=mode
    )


def collect(args):
    with open(args.stages) as f:
        stages = json.load(f)
    runs = runner.Runner.create_from_dict(stages)
    outputs = {}
    for name, node in runs.nodes.items():
        if node.post:
            directory = node.post.get("directory", "")
            output = node.post.get("output", "")
            filename = "{}/{}".format(directory, output)
            if not os.path.isfile(filename):
                outputs[name] = {
                    "status" : "failed",
                    "content" : "File not found",
                    "filename" : filename
                }
                continue

            with open(filename) as f:
                outputs[name] = {
                    "status" : "unverified",
                    "content" : f.read(),
                    "filename" : filename
                }

    with open(args.output, "w") as f:
        json.dump(outputs, f, indent=4)
