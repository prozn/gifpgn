from typing import NamedTuple
from enum import Enum
from dataclasses import dataclass
import chess


class Coord(NamedTuple):
    x: int
    y: int


class PieceTheme(Enum):
    """Enum with valid piece themes

    .. code-block:: python

        game = chess.pgn.read_game(io.StringIO(pgn_string))
        gif = CreateGifFromPGN(game)
        gif.piece_theme = PieceTheme.CASES

    """
    ALPHA = "alpha"
    """Alpha theme by Eric Bentzen, free for personal use."""
    CASES = "cases"
    """Cases theme by Matthieu Leschemelle, freeware."""
    MAYA = "maya"
    """Maya theme by Armando Hernandez Marroquin, freeware."""
    REGULAR = "regular"
    """Regular theme by Alastair Scott, freeware."""


@dataclass
class BoardTheme:
    """Class for creating your own board theme containing colors for the white and black squares

    .. code-block:: python

        game = chess.pgn.read_game(io.StringIO(pgn_string))
        gif = CreateGifFromPGN(game)
        gif.square_colors = BoardTheme(white="#ffffff", black="#000000")

    """
    white: str = "#f0d9b5"
    black: str = "#b58863"

    def square_color(self, color: chess.Color):
        return self.white if color is chess.WHITE else self.black


class BoardThemes(Enum):
    """Class to select one of the built-in board themes

    .. code-block:: python

        game = chess.pgn.read_game(io.StringIO(pgn_string))
        gif = CreateGifFromPGN(game)
        gif.square_colors = BoardThemes.BLUE

    """
    GREEN = ("#ebecd0", "#739552")
    BLUE = ("#eae9d2", "#4b7399")
    BROWN = ("#f0d9b5", "#b58863")
    PURPLE = ("#f0f1f0", "#8476ba")
    RED = ("#f5dbc3", "#bb5746")
    LIGHT_BLUE = ("#f0f1f0", "#c4d8e4")
