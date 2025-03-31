"""Custom exceptions for the DAG builder module.
"""

class NoSuchStage(Exception):
    """Exception raised when a referenced stage is not found in the stage map."""

    def __init__(self, stage: str, stages: dict):
        self.stage = stage
        self.stages = stages
        super().__init__(self.__str__())

    def __str__(self) -> str:
        available = ', '.join(self.stages.keys())
        return f"No such stage: '{self.stage}'. Available stages: [{available}]"
