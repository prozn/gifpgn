from io import BytesIO
from math import floor

from typing import List, Dict, Optional, Union

import chess
import chess.pgn
import chess.engine
from PIL import Image

from .exceptions import MissingAnalysisError
from ._types import PieceTheme, BoardTheme, BoardThemes
from .utils import PGN, _eval
from .components import (
    _Board,
    _Graph,
    _EvalBar,
    _Headers,
    _Canvas
)


class CreateGifFromPGN:
    """
    :param chess.pgn.Game game: An instance of :class:`chess.pgn.Game` from the python-chess library.
    """
    def __init__(self, game: chess.pgn.Game):
        if game is None:
            raise ValueError("Provided game is not valid/empty")

        if game.end().ply() - game.ply() < 1:
            raise ValueError("Provided game does not have any moves.")

        self.board_size = 480
        self.square_colors = BoardThemes.BROWN
        self.frame_duration = 0.5
        self.max_eval = 1000

        self._reverse: bool = False
        self._arrows: bool = False
        self._nag: bool = False
        self.piece_theme = PieceTheme.ALPHA
        self._bar_size: Optional[int] = None
        self._graph_size: Optional[int] = None
        self._header_size: Optional[int] = None
        self._game_root: chess.pgn.Game = game
        self._start_color: chess.Color = self._game_root.turn()

    @property
    def board_size(self) -> int:
        """int: Size of the board in pixels, defaults to 480

        .. note::
            Size will be rounded down to the nearest multiple of 8
        """
        return self._board_size

    @board_size.setter
    def board_size(self, bsize: int):
        self._board_size = floor(bsize/8)*8

    @property
    def square_colors(self) -> BoardTheme:
        """BoardTheme: An instance of gifpgn.BoardTheme"""
        return self._square_colors

    @square_colors.setter
    def square_colors(self, colors: Union[BoardTheme, BoardThemes]):
        """Set the square colors to a given BoardTheme or BoardThemes instance

        Args:
            colors (Union[BoardTheme, BoardThemes]): Use gifpgn.BoardThemes to select a built in theme,
                or gifpgn.BoardTheme to define your own

        Raises:
            ValueError: Provided colors not valid, see error message.
        """
        if isinstance(colors, BoardTheme):
            self._square_colors = colors
        elif isinstance(colors, BoardThemes):
            self._square_colors = BoardTheme(*colors.value)
        elif isinstance(colors, Dict):  # for backwards compatability
            if chess.WHITE in colors and chess.BLACK in colors:
                self._square_colors = BoardTheme(white=colors[chess.WHITE], black=colors[chess.BLACK])
            else:
                raise ValueError("Provided Dict did not contain keys for chess.WHITE and chess.BLACK")
        else:
            raise ValueError(f"Colors should be an instance of BoardTheme. Provided: {type(colors)}")

    @property
    def piece_theme(self) -> PieceTheme:
        """PieceTheme: Instance of gifpgn.PieceTheme"""
        return self._piece_theme

    @piece_theme.setter
    def piece_theme(self, theme: PieceTheme) -> None:
        if isinstance(theme, PieceTheme):
            self._piece_theme = theme
        else:
            raise ValueError(f"Theme should be an instance of PieceTheme. Provided: {type(theme)}")

    @property
    def frame_duration(self) -> float:
        """float: Duration of each frame in seconds, defaults to 0.5"""
        return self._frame_duration

    @frame_duration.setter
    def frame_duration(self, frame_duration: float):
        self._frame_duration = frame_duration

    @property
    def max_eval(self) -> int:
        """int: Maximum evaluation displayed on analysis graph or bar in centipawns, defaults to 1000"""
        return self._max_eval

    @max_eval.setter
    def max_eval(self, max_eval: int):
        self._max_eval = max_eval

    # Optional features

    def add_analysis_bar(self, width: int = 30) -> None:
        """Adds an analysis bar to the right side of the chess board.

        .. note::
            Requires that a PGN has been loaded with ``[%eval ...]`` annotations for
            each half move.

            Alternatively the PGN can be decorated using the ``gifpgn.utils.PGN`` class.

        :param int width: Width of the analysis bar in pixels, defaults to 30
        :raises MissingAnalysisError: At least one ply in the PGN has a missing ``[%eval ...]`` annotation
        """
        if not PGN(self._game_root).has_analysis():
            raise MissingAnalysisError("PGN did not contain evaluations for every half move")
        self._bar_size = width

    def add_analysis_graph(self, height: int = 81, line_width: int = 1) -> None:
        """Adds an analysis graph to the bottom of the chess board.

        .. note::
            Requires that a PGN has been loaded with ``[%eval ...]`` annotations for
            each half move.

            Alternatively the PGN can be decorated using the ``gifpgn.utils.PGN`` class.

        :param int height: Height of the analysis graph in pixels, defaults to 81
        :param int line_width: Width of graph line (and x axis line) in pixels, defaults to 1
        :raises MissingAnalysisError: At least one ply in the PGN has a missing ``[%eval ...]`` annotation
        """
        # PGN needs to be decorated with evaluations for each half move
        if not PGN(self._game_root).has_analysis():
            raise MissingAnalysisError("PGN did not contain evaluations for every half move")
        self._graph_size = height
        self._graph_line_width = line_width

    def enable_nags(self):
        """Enable numerical annoation glyphs

        .. note::
            Requires that a PGN has been loaded with ``[%eval ...]`` annotations for
            each half move.

            Alternatively the PGN can be decorated using the ``gifpgn.utils.PGN`` class.

        :raises MissingAnalysisError: At least one ply in the PGN has a missing ``[%eval ...]`` annotation
        """
        if not PGN(self._game_root).has_analysis():
            raise MissingAnalysisError("PGN did not contain evaluations for every half move")
        self._nag = True

    def add_headers(self, height: int = 20) -> None:
        """Adds headers with player names, captured pieces, and clock (if PGN contains
        ``[%clk ...]`` annotations) to the top and bottom of the chess board.

        :param int height: Height of headers in pixels, defaults to 20
        """
        self._header_size = height

    def reverse_board(self):
        """Reverses the board so that black is at the bottom"""
        self._reverse = True

    def enable_arrows(self):
        """Enables move and check arrows"""
        self._arrows = True

    def generate(self, output_file: Optional[str] = None) -> Optional[BytesIO]:
        """Generate the GIF and either save it to the specified file path or return the
        raw bytes if no file path is specified.

        .. code-block:: python

            game = chess.pgn.read_game(io.StringIO(pgn_string))
            gif = CreateGifFromPGN(game)
            gif.generate("/path/to/output.gif")

        :param Optional[str] output_file: Filepath to save to, defaults to None
        :return Optional[BytesIO]: Raw bytes of the generated GIF if ``output_file`` parameter is set, else returns ``None``
        """
        captures: List[chess.Piece] = []
        frames: List[Image.Image] = []

        if self._graph_size is not None:
            graph = _Graph(
                self._game_root,
                (self.board_size+(0 if self._bar_size is None else self._bar_size), self._graph_size),
                self.max_eval,
                line_width=self._graph_line_width
            )

        game = self._game_root
        while True:
            board = game.board()
            frame = _Canvas(self.board_size, self._bar_size, self._graph_size, self._header_size, self._reverse)
            board_img = _Board(self.board_size, board, self._reverse, self.square_colors, self.piece_theme)

            if game.move is not None and game.parent.board().is_capture(game.move):
                if game.parent.board().is_en_passant(game.move):
                    captures.append(chess.Piece(chess.PAWN, board.turn))
                else:
                    captures.append(game.parent.board().piece_at(game.move.to_square))

            if self._arrows and game.move is not None:
                board_img.draw_arrow(game.move.from_square, game.move.to_square, "blue")
                if board.is_check():
                    for sq in board.checkers():
                        board_img.draw_arrow(sq, board.king(board.turn), "red")

            if self._nag and game.move is not None:
                prev = _eval(game.parent).relative.wdl(model="sf", ply=game.parent.ply())
                curr = _eval(game).pov(not _eval(game).turn).wdl(model="sf", ply=game.ply())
                change = curr.expectation() - prev.expectation()
                nag = None
                if change < -0.3:
                    nag = "blunder"
                elif change < -0.2:
                    nag = "mistake"
                elif change < -0.1:
                    nag = "inaccuracy"
                if nag is not None:
                    board_img.draw_nag(nag, game.move.to_square)

            frame.add_board(board_img.image())
            if self._bar_size is not None:
                frame.add_bar(
                    _EvalBar(
                        (self._bar_size, self.board_size),
                        _eval(game).white(),
                        self.max_eval,
                        self._reverse
                    ).image()
                )

            if self._graph_size is not None:
                frame.add_graph(graph.at_move(game.ply()))

            if self._header_size is not None:
                headers = _Headers(game, captures, (frame.size()[0], self._header_size))
                frame.add_headers(headers.image(chess.WHITE), headers.image(chess.BLACK))

            frames.append(frame.image())

            if game.next() is None:
                break
            game = game.next()

        last_frame = frames[-1].copy()
        for _ in range(20):
            frames.append(last_frame)

        if output_file is None:
            target = BytesIO()
        else:
            target = output_file

        frames[0].save(
            target,
            format="GIF",
            append_images=frames[1:],
            optimize=True,
            save_all=True,
            duration=int(self.frame_duration*1000),
            loop=0
        )

        if output_file is None:
            target.seek(0)
            return target

    def _output_image(self, image: Image.Image, name: str = "output.png"):  # dump an image for bug testing
        print("Saving image")
        image.save(name, format="PNG")
