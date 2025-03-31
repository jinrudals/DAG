"""
Builder for generating resolved stage definitions from stage templates and target overrides.
"""

import re
import copy
from typing import Dict, Any

from . import exceptions
from . import logger as lg

logger = lg.get_logger(__name__)


class Stage:
    """Represents a single stage, including its commands, dependencies, and variables."""
    # pylint: disable=too-many-instance-attributes

    VAR_PATTERN = re.compile(r"\$\{(\w+)\}")
    CROSS_REF_PATTERN = re.compile(r"^@\{(.+?)\.(.+?)\}$")

    def __init__(self, name: str, info: Dict[str, Any], target: str):
        self.name = name
        self.target = target
        self.info = copy.deepcopy(info)
        self.command: Dict[str, str] = self.info.get("run", {})
        self.post: Dict[str, str] = self.info.get("post", {})
        self.variables: Dict[str, str] = self.info.get("variables", {})
        self.before = self.info.get("before", [])
        self.after = self.info.get("after", [])

    def apply_target(self) -> None:
        """Replace @{target} in variable values with the actual target name."""
        for key, value in self.variables.items():
            self.variables[key] = value.replace("@{target}", self.target)

    def override_values(self, override_vars: Dict[str, Any]) -> None:
        """Apply overrides to variables, command, and post sections."""
        if "variables" in override_vars:
            self.variables.update(override_vars.pop("variables"))
        if "post" in override_vars:
            self.post.update(override_vars.pop("post"))
        if "command" in override_vars:
            self.command.update(override_vars.pop("command"))
        if override_vars:
            raise ValueError(f"Unrecognized override keys: {list(override_vars.keys())}")

    def update_dependencies(self) -> None:
        """Add full target-qualified names to before/after dependencies."""
        self.before = [f"{self.target}:{stage}" for stage in self.before]
        self.after = [f"{self.target}:{stage}" for stage in self.after]

    def apply_variable_extend(self, stages: Dict[str, "Stage"]) -> None:
        """Resolve variables referencing other stages via @{StageName.VAR}."""
        for key, value in list(self.variables.items()):
            match = self.CROSS_REF_PATTERN.match(value)
            if match:
                ref_stage_name, ref_var = match.groups()
                full_stage_name = f"{self.target}:{ref_stage_name}"
                ref_stage = stages.get(full_stage_name)
                if not ref_stage:
                    raise exceptions.NoSuchStage(full_stage_name, stages)
                if ref_var not in ref_stage.variables:
                    raise KeyError(f"Variable '{ref_var}' not found in stage '{full_stage_name}'")
                ref_value = ref_stage.variables[ref_var]
                self.variables[key] = ref_value
                logger.debug("Resolved variable @{%s.%s} -> %s", ref_stage_name, ref_var, ref_value)

    def normalize_run_post(self) -> None:
        """Substitute ${VAR} inside command and post sections."""

        def replace_vars(section: Dict[str, str]) -> Dict[str, str]:
            result = {}
            for key, value in section.items():
                new_value = value
                for var_name in self.VAR_PATTERN.findall(value):
                    if var_name not in self.variables:
                        raise KeyError(f"Missing variable '{var_name}' in stage '{self.name}'")
                    new_value = new_value.replace(f"${{{var_name}}}", self.variables[var_name])
                result[key] = new_value
            return result

        self.command = replace_vars(self.command)
        self.post = replace_vars(self.post)

    def serialize(self) -> Dict[str, Any]:
        """Convert the stage to a serializable dictionary."""
        return {
            "command": self.command,
            "post": self.post,
            "before": self.before,
            "after": self.after,
            "variables": self.variables,
        }


class Target:
    """Represents a target with optional stage-specific overrides."""
    # pylint: disable=too-few-public-methods

    def __init__(self, target_info: Dict[str, Any]):
        self.name = target_info["target"]
        self.overrides = target_info.get("overrides", {})

    def get_stage_override(self, stage_name: str) -> Dict[str, Any]:
        """Return overrides for a specific stage if available."""
        return self.overrides.get(stage_name, {})


class Builder:
    """Main class for building fully-expanded, target-specific stage definitions."""
    # pylint: disable=too-few-public-methods

    def __init__(self, stages: Dict[str, Any], targets: list[Dict[str, Any]]):
        self.original_stages = stages
        self.targets = [Target(t) for t in targets]
        self.combined_stages: Dict[str, Stage] = {}

    def build(self) -> Dict[str, Any]:
        """
        Build the final resolved stage list:
        - Applies overrides
        - Resolves dependencies
        - Handles variable substitutions
        """
        outputs: Dict[str, Any] = {}

        for target in self.targets:
            for stage_name, stage_info in self.original_stages.items():
                full_stage_name = f"{target.name}:{stage_name}"
                stage = Stage(stage_name, stage_info, target.name)

                override_vars = target.get_stage_override(stage_name)
                stage.override_values(copy.deepcopy(override_vars))

                stage.apply_target()
                stage.update_dependencies()

                self.combined_stages[full_stage_name] = stage

        for name, stage in self.combined_stages.items():
            stage.apply_variable_extend(self.combined_stages)
            stage.normalize_run_post()
            outputs[name] = stage.serialize()

        return outputs
