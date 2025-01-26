import chess
import chess.pgn
import chess.engine

from .exceptions import MissingAnalysisError

from typing import Dict, List


class PGN:
    """Class for working with ``[%eval ...]`` annotations

    :param chess.pgn.Game pgn: An instance of ``chess.pgn.Game`` containing the PGN for analysis
    """
    def __init__(self, pgn: chess.pgn.Game):
        self._game_root = pgn

    def has_analysis(self) -> bool:
        """Checks that every half move in the PGN has ``[%eval ...]`` annotations

        :return bool: `True` if every half move has ``[%eval ...]`` annotations, `False` otherwise
        """
        game = self._game_root
        while True:
            if game.eval() is None:
                if game.board().is_checkmate():
                    return True
                return False
            if game.next() is None:
                break
            game = game.next()
        return True

    def add_analysis(self, engine: chess.engine.SimpleEngine, engine_limit: chess.engine.Limit) -> chess.pgn.Game:
        """Calculates and adds ``[%eval ...]`` annotations to each half move in the PGN

        :param chess.engine.SimpleEngine engine: Instance of
            `chess.engine.SimpleEngine <https://python-chess.readthedocs.io/en/latest/engine.html>`_ from python-chess
        :param chess.engine.Limit engine_limit: Instance of
            `chess.engine.Limit <https://python-chess.readthedocs.io/en/latest/engine.html#chess.engine.Limit>`_
            from python-chess
        """
        game = self._game_root
        while True:
            info = engine.analyse(game.board(), engine_limit)
            game.set_eval(info['score'], info['depth'])
            if game.next() is None:
                break
            game = game.next()
        return game.game()

    def acpl(self, max_eval: int = 1000) -> Dict[chess.Color, int]:
        """Calculate the average centipawn loss for each player.

        :param int max_eval: The maximum evaluation to consider when calculating the ACPL, defaults to 1000
        :raises MissingAnalysisError: PGN is not decorated with ``[%eval ...]`` annotations
        :return Dict[chess.Color, int]: Dictionary containing the ACPL for each player
        """
        if not self.has_analysis():
            raise MissingAnalysisError
        acpl: Dict[chess.Color, List[int]] = {
            chess.WHITE: [0, 0],
            chess.BLACK: [0, 0]
        }
        game = self._game_root
        while True:
            if game.parent is not None:
                curr_eval = min(max_eval, _eval(game).pov(not game.turn()).score(mate_score=max_eval), key=abs)
                prev_eval = min(max_eval, _eval(game.parent).pov(not game.turn()).score(mate_score=max_eval), key=abs)
                print(f"{not game.turn()} : {prev_eval} -> {curr_eval}")
                acpl[not game.turn()][0] += curr_eval - prev_eval
                acpl[not game.turn()][1] += 1
            if game.next() is None:
                break
            game = game.next()
        return {
            chess.WHITE: int(acpl[chess.WHITE][0] / acpl[chess.WHITE][1] * -1),
            chess.BLACK: int(acpl[chess.BLACK][0] / acpl[chess.BLACK][1] * -1)
        }

    def export(self) -> str:
        """Output the current PGN

        :return str:
        """
        return self._game_root.__str__()

    def __str__(self) -> str:
        return self.export()


def _eval(game: chess.pgn.Game) -> chess.engine.PovScore:
    """Patch ``chess.pgn.Game.eval()``, which does not return a valid ``chess.engine.PovScore`` if
    the position is mate.

    :param chess.pgn.Game game: _description_
    :raises MissingAnalysisError: _description_
    :return _type_: _description_
    """
    if game.eval() is None:
        if game.board().is_checkmate():
            return chess.engine.PovScore(chess.engine.Mate(0), game.turn())
        else:
            raise MissingAnalysisError
    return game.eval()
