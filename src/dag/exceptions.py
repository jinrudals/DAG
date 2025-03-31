class NoSuchStage(Exception):
    def __init__(self, stage, stages):
        super().__init__(stage, stages)
        self.stage = stage
        self.stages = stages

    def __str__(self):
        return f"No such stage as {self.stage} in {self.stages}"
