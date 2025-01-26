class MoveOutOfRangeError(Exception):
    """Requested move was higher than the game length"""
    def __init__(self, move, range):
        super().__init__(f"Requested move ({move}) was higher than the game length ({range})")


class MissingAnalysisError(Exception):
    "PGN did not contain an ``[%eval ...]`` annotation for every ply"
    pass
