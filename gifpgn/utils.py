import chess
import chess.pgn
import chess.engine

from io import BytesIO
from PIL import ImageFont

from .exceptions import MissingAnalysisError
from ._types import AnalysisStats

from typing import Callable, Dict, List, Awaitable, Optional


class PGN:
    """Class for working with ``[%eval ...]`` annotations

    :param chess.pgn.Game pgn: An instance of ``chess.pgn.Game`` containing the PGN for analysis
    """

    def __init__(self, pgn: chess.pgn.Game):
        if pgn is None:
            raise ValueError("Provided game is not valid/empty")

        if pgn.end().ply() - pgn.ply() < 1:
            raise ValueError("Provided game does not have any moves.")

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
            game = game.next()
            if game is None:
                break
            
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
            game.set_eval(info["score"], info["depth"])
            game = game.next()
            if game is None:
                break
            
        return self._game_root

    async def add_analysis_async(
        self,
        engine: chess.engine.Protocol,
        engine_limit: chess.engine.Limit,
        update_callback: Optional[Callable[[AnalysisStats], Awaitable[None]]] = None,
    ) -> chess.pgn.Game:
        """Asynchronously calculates and adds ``[%eval ...]`` annotations to each half move in the PGN

        :param chess.engine.SimpleEngine engine: Instance of
            `chess.engine.SimpleEngine <https://python-chess.readthedocs.io/en/latest/engine.html>`_ from python-chess
        :param chess.engine.Limit engine_limit: Instance of
            `chess.engine.Limit <https://python-chess.readthedocs.io/en/latest/engine.html#chess.engine.Limit>`_
            from python-chess
        :param Optional[Callable[[AnalysisStats], Awaitable[None]]] update_callback: Optional async callback function to
            receive updates during analysis. The function should accept a `gifpgn.AnalysisStats` typed dictionary.
        """
        game = self._game_root
        total_moves = game.end().ply() - game.ply()
        move_number = 0
        while True:
            info: chess.engine.InfoDict = await engine.analyse(game.board(), engine_limit)

            if update_callback:
                move_number += 1
                stats: AnalysisStats = {
                    **info,
                    "movenumber": move_number,
                    "totalmoves": total_moves,
                    "percentcomplete": move_number / total_moves,
                }
                await update_callback(stats)

            game.set_eval(info["score"], info["depth"])

            game = game.next()
            if game is None:
                break
            
        return self._game_root

    def acpl(self, max_eval: int = 1000) -> Dict[chess.Color, int]:
        """Calculate the average centipawn loss for each player.

        :param int max_eval: The maximum evaluation to consider when calculating the ACPL, defaults to 1000
        :raises MissingAnalysisError: PGN is not decorated with ``[%eval ...]`` annotations
        :return Dict[chess.Color, int]: Dictionary containing the ACPL for each player
        """
        if not self.has_analysis():
            raise MissingAnalysisError
        acpl: Dict[chess.Color, List[int]] = {chess.WHITE: [0, 0], chess.BLACK: [0, 0]}
        game = self._game_root
        while True:
            if game.parent is not None:
                curr_eval = _eval(game).pov(not game.turn()).score(mate_score=max_eval)
                curr_eval = min(max_eval * (-1 if curr_eval < 0 else 1), curr_eval, key=abs)
                prev_eval = _eval(game.parent).pov(not game.turn()).score(mate_score=max_eval)
                prev_eval = min(max_eval * (-1 if prev_eval < 0 else 1), prev_eval, key=abs)
                acpl[not game.turn()][0] += curr_eval - prev_eval
                acpl[not game.turn()][1] += 1

            game = game.next()
            if game is None:
                break

        return {
            chess.WHITE: int(acpl[chess.WHITE][0] / acpl[chess.WHITE][1] * -1) if acpl[chess.WHITE][1] > 0 else 0,
            chess.BLACK: int(acpl[chess.BLACK][0] / acpl[chess.BLACK][1] * -1) if acpl[chess.BLACK][1] > 0 else 0,
        }

    def export(self) -> str:
        """Output the current PGN

        :return str:
        """
        return self._game_root.__str__()

    def __str__(self) -> str:
        return self.export()


def _eval(game: chess.pgn.GameNode) -> chess.engine.PovScore:
    """Patch ``chess.pgn.Game.eval()``, which does not return a valid ``chess.engine.PovScore`` if
    the position is mate.

    :param chess.pgn.GameNode game: Game node to evaluate
    :raises MissingAnalysisError: Raised if the game node has no analysis
    :return chess.engine.PovScore: Evaluation of the game node
    """
    eval = game.eval()
    if eval is not None:
        return eval

    if game.board().is_checkmate():
        return chess.engine.PovScore(chess.engine.Mate(0), game.turn())
    else:
        raise MissingAnalysisError


def _font_size_approx(text: str, font_file: bytes, target_width: int, target_ratio: float, min_size: int) -> int:
    """Get the approximate font size required to fit ``text`` inside ``target_width*target_ratio`` pixels width

    This is only an approximate calculation as string lengths do not scale linearly with font size.

    :param str text: String to be drawn
    :param bytes font_file: Raw bites of a .ttf font file
    :param int target_width: Width of the destination image
    :param float target_ratio: Ratio to scale down text width by
    :param int min_size: If calculated font size is less than min_size, return min_size
    :return int: Approximate font size
    """
    font: ImageFont.FreeTypeFont = ImageFont.truetype(BytesIO(font_file), 100)
    width = font.getbbox(text)[2]
    approx_size = int(100 / (width / target_width) * target_ratio)
    return max(min_size, approx_size)
