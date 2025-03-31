"""DAG runner that executes stages in parallel with respect to their dependencies."""

import time
import os
import sys
import subprocess
from concurrent.futures import ProcessPoolExecutor, Future
from typing import Dict, List, Tuple, Optional

from . import logger as lg

logger = lg.get_logger(__name__)
cwd = os.getcwd()


def execute_command(
    command_info: Tuple[str, str, str, str, str]
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Executes a stage's run and/or post command in a separate process.
    Returns (node name, output, post_output).
    """
    name, command, directory, post_command, post_directory = command_info
    try:
        if command:
            cmd = f"cd {directory}; {command}"
            subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                stdout=sys.stdout,
                stderr=sys.stderr,
                check=True
            )

        if post_command:
            cmd = f"cd {post_directory}; {post_command}"
            subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                stdout=sys.stdout,
                stderr=sys.stderr,
                check=True
            )

        return name, None, None

    except subprocess.CalledProcessError as e:
        logger.error("Execution failed for node %s: %s", name, e)
        return name, None, None
    except OSError as e:
        logger.error("OS error for node %s: %s", name, e)
        return name, None, None


class Node:
    """Represents a single stage in the DAG with dependencies, command, and post steps."""

    def __init__(
        self,
        name: str,
        command: dict = None,
        in_degree: int = 0,
        post: dict = None
    ):
        self.name = name
        self.command = command or {}
        self.post = post or {}
        self.in_degree = in_degree
        self.parents: List[Node] = []
        self.children: List[Node] = []
        self.executed = False

    def prepare_command(self) -> Tuple[str, str, str, str, str]:
        """Prepare command and post-command info for execution."""
        directory = self.command.get("directory", cwd)
        command = self.command.get("command", "")
        post_directory = self.post.get("directory", cwd)
        post_command = self.post.get("command", "")
        return (self.name, command, directory, post_command, post_directory)

    def __str__(self):
        return f"Node({self.name})"


class Runner:
    """DAG executor that runs all nodes respecting their dependencies."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}

    @staticmethod
    def create_from_dict(dct: dict) -> "Runner":
        """Create a Runner instance from a dictionary representation of the DAG."""
        dag = Runner()

        for name, data in dct.items():
            dag.nodes[name] = Node(name, data.get("command"), 0, data.get("post"))

        for name, data in dct.items():
            node = dag.nodes[name]
            for child_name in data.get("before", []):
                child = dag.nodes[child_name]
                node.children.append(child)
                child.parents.append(node)
                child.in_degree = max(child.in_degree, node.in_degree + 1)

            for parent_name in data.get("after", []):
                parent = dag.nodes[parent_name]
                node.parents.append(parent)
                parent.children.append(node)
                node.in_degree = max(node.in_degree, parent.in_degree + 1)

        return dag

    def _submit_node(
        self,
        node: Node,
        executor: ProcessPoolExecutor,
        mode: str
    ) -> Future:
        """Submit a node's execution to the process pool."""
        name, command, directory, post_command, post_directory = node.prepare_command()

        if mode == "post":
            command = ""
        elif mode == "command":
            post_command = ""

        return executor.submit(
            execute_command,
            (name, command, directory, post_command, post_directory)
        )

    def launch(self, max_workers: int = 2, mode: str = "all") -> None:
        """
        Execute all nodes in the DAG using a ProcessPoolExecutor.
        :param max_workers: The maximum number of worker processes.
        :param mode: "all" → run + post, "post" → post only, "command" → run only
        """
        logger.info("Launching DAG with mode=%s, workers=%d", mode, max_workers)

        total_nodes = len(self.nodes)
        completed_count = 0
        ready = [n for n in self.nodes.values() if n.in_degree == 0]
        running: Dict[str, Future] = {}

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            while completed_count < total_nodes:
                while ready:
                    node = ready.pop()
                    if not node.executed:
                        future = self._submit_node(node, executor, mode)
                        running[node.name] = future
                        logger.info("Submitted: %s", node.name)

                time.sleep(0.2)

                completed = [name for name, fut in running.items() if fut.done()]
                for name in completed:
                    future = running.pop(name)
                    completed_count += 1
                    node = self.nodes[name]
                    node.executed = True

                    try:
                        result_name, _, _ = future.result()
                        logger.info("Completed: %s", result_name)
                    except Exception as e:
                        logger.error("Error in node %s: %s", name, e)

                    for child in node.children:
                        if all(p.executed for p in child.parents) and not child.executed:
                            ready.append(child)

        logger.info("All DAG stages executed.")

    def __str__(self) -> str:
        return "\n".join(
            f"{n.name}: (in_degree={n.in_degree})"
            for n in sorted(self.nodes.values(), key=lambda n: n.in_degree)
        )
