import pytest

from gifpgn.components import (
    _Canvas,
    _AssetImage,
    _Piece,
    _Board,
    _Headers,
    _EvalBar,
    _Graph
)
from gifpgn._types import Coord, PieceTheme, BoardTheme

import chess
import chess.pgn
from chess.engine import Cp, Mate, PovScore
from PIL import Image

from gifpgn.exceptions import MoveOutOfRangeError


# Test files

PGN_NO_ANNOTATIONS = "test_no_annotations.pgn"
PGN_EVAL_ANNOTATIONS = "test_eval_annotations.pgn"
PGN_CLOCK_ANNOTATIONS = "test_clock.pgn"
PGN_NO_MOVES = "test_no_moves.pgn"
PGN_EMPTY = "test_empty.pgn"


# Test _Component and _Canvas

@pytest.fixture()
def canvas() -> _Canvas:
    return _Canvas(480, 20, 50, 10, False)


def test_component(canvas: _Canvas):
    assert isinstance(canvas.image(), Image.Image)


def test_canvas_size(canvas: _Canvas):
    assert canvas.size() == (500, 550)


def test_canvas_headers(canvas: _Canvas):
    canvas.add_headers(
        white=Image.new("RGBA", (canvas.size()[0], 20), "#0000ff"),
        black=Image.new("RGBA", (canvas.size()[0], 20), "#00ff00")
    )
    assert canvas._canvas.getpixel((240, 5)) == (0, 255, 0, 255)
    assert canvas._canvas.getpixel((240, 495)) == (0, 0, 255, 255)

    canvas = _Canvas(480, 20, 50, 10, True)
    canvas.add_headers(
        white=Image.new("RGBA", (canvas.size()[0], 20), "#0000ff"),
        black=Image.new("RGBA", (canvas.size()[0], 20), "#00ff00")
    )
    assert canvas._canvas.getpixel((240, 495)) == (0, 255, 0, 255)
    assert canvas._canvas.getpixel((240, 5)) == (0, 0, 255, 255)


def test_add_board(canvas: _Canvas):
    canvas.add_board(Image.new("RGBA", (480, 480), "#00ffff"))
    assert canvas._canvas.getpixel((0, 9)) == (255, 0, 0, 255)
    assert canvas._canvas.getpixel((0, 10)) == (0, 255, 255, 255)
    assert canvas._canvas.getpixel((479, 245)) == (0, 255, 255, 255)
    assert canvas._canvas.getpixel((480, 245)) == (255, 0, 0, 255)


def test_add_bar(canvas: _Canvas):
    canvas.add_bar(Image.new("RGBA", (20, 480), "#00ffff"))
    assert canvas._canvas.getpixel((480, 9)) == (255, 0, 0, 255)
    assert canvas._canvas.getpixel((480, 10)) == (0, 255, 255, 255)
    assert canvas._canvas.getpixel((479, 10)) == (255, 0, 0, 255)


def test_add_graph(canvas: _Canvas):
    canvas.add_graph(Image.new("RGBA", (canvas.size()[0], 50), "#00ffff"))
    assert canvas._canvas.getpixel((0, 499)) == (255, 0, 0, 255)
    assert canvas._canvas.getpixel((0, 500)) == (0, 255, 255, 255)
    assert canvas._canvas.getpixel((499, 500)) == (0, 255, 255, 255)


# Test _AssetImage and _Piece

def test_asset_image():
    asset = _AssetImage("nags/blunder", 20).image()
    assert asset.size == (20, 20)
    assert "nags/blunder-20" in _AssetImage._images


def test_piece_image():
    piece = _Piece(chess.Piece(chess.KNIGHT, chess.WHITE), 40, PieceTheme.MAYA)
    assert piece.get_piece_string(chess.Piece(chess.KING, chess.BLACK)) == "bk"
    piece_image = piece.image()
    assert piece_image.size == (40, 40)
    assert "pieces/maya/wn-40" in _AssetImage._images


def test_asset_image_cache():
    a = _AssetImage("nags/blunder", 20)
    assert "pieces/maya/wn-40" in a._images


# Test _Board

@pytest.fixture()
def chess_board():
    def _chess_board(pgn: str) -> chess.Board:
        return chess.pgn.read_game(open(f"tests/test_data/{pgn}")).board()
    return _chess_board


@pytest.fixture()
def board(chess_board: chess.Board) -> _Board:
    return _Board(
        480,
        chess_board(PGN_NO_ANNOTATIONS),
        False,
        BoardTheme(white="#ff0000", black="#00ff00")
    )


def test_board(board: _Board):
    assert board._board_size == 480
    assert board._sq_size == 60
    assert len(board._square_images.keys()) == 2
    assert board._square_images[chess.WHITE].getpixel((30, 30)) == (255, 0, 0, 255)
    assert board._square_images[chess.BLACK].getpixel((30, 30)) == (0, 255, 0, 255)


def test_default_square_color(chess_board):
    board = _Board(480, chess_board(PGN_NO_ANNOTATIONS))
    assert board.square_colors == BoardTheme(white="#f0d9b5", black="#b58863")


def test_setting_square_color(chess_board):
    board = _Board(480, chess_board(PGN_NO_ANNOTATIONS), square_colors=BoardTheme(white="#0000ff", black="#00ff00"))
    assert board.square_colors == BoardTheme(white="#0000ff", black="#00ff00")


def test_square_color_error(chess_board):
    with pytest.raises(ValueError):
        _Board(480, chess_board(PGN_NO_ANNOTATIONS), square_colors="#ff0000")


def test_board_size(board: _Board):
    assert board.board_size == 480
    board.draw_board()
    assert len(board._square_images.items()) == 2
    board.board_size = 245
    assert board.board_size == 240
    assert board._sq_size == 30
    assert len(board._square_images.items()) == 0


def test_draw_squares(board: _Board):
    board.draw_squares()
    assert board._canvas.getpixel(board.get_square_position(chess.H8)) == (0, 255, 0, 255)
    assert board._canvas.getpixel(board.get_square_position(chess.H1)) == (255, 0, 0, 255)


def test_draw_square(board: _Board):
    board._canvas = Image.new("RGBA", (480, 480), "#0000ff")
    board.draw_square(chess.A1)
    assert board._canvas.getpixel((30, 420)) == (0, 255, 0, 255)
    assert board._canvas.getpixel((30, 450)) != (0, 255, 0, 255)  # Should be a piece here, so different color
    board.draw_square(chess.D5)
    assert board._canvas.getpixel((210, 180)) == (255, 0, 0, 255)
    assert board._canvas.getpixel((210, 210)) == (255, 0, 0, 255)


def test_get_square_position(board: _Board):
    board.board_size = 240
    assert board.get_square_position(chess.A1) == (0, 210)
    assert board.get_square_position(chess.A1, True) == (15, 225)
    assert board.get_square_position(chess.H8) == (210, 0)
    board.reverse = True
    assert board.get_square_position(chess.A1) == (210, 0)
    assert board.get_square_position(chess.A1, True) == (225, 15)
    assert board.get_square_position(chess.H8) == (0, 210)


def test_get_square_color(board: _Board):
    assert board.get_square_color(chess.A4) == chess.WHITE
    assert board.get_square_color(chess.H6) == chess.BLACK


def test_get_square_image(board: _Board):
    assert board.get_square_image(chess.A6).getpixel((5, 5)) == (255, 0, 0, 255)
    assert board.get_square_image(chess.E3).getpixel((5, 5)) == (0, 255, 0, 255)


def test_draw_arrow(board: _Board):
    board.board_size = 240
    board.square_colors = BoardTheme(white="#000000", black="#000000")
    board.draw_board()
    board.draw_arrow(chess.A1, chess.H8, "red")
    assert board._canvas.getpixel((120, 120))[0] > 0
    assert board._canvas.getpixel((120, 120))[1] == 0

    board.draw_arrow(chess.A6, chess.B5, "blue")
    assert board._canvas.getpixel((0, 0)) == (0, 0, 0, 255)
    assert board._canvas.getpixel((30, 90))[2] > 0
    assert board._canvas.getpixel((30, 90))[0] == 0


def test_draw_nag(board: _Board):
    board.square_colors = BoardTheme(white="#000000", black="#000000")
    board.draw_board()
    assert board._canvas.getpixel((239, 239)) == (0, 0, 0, 255)
    board.draw_nag("blunder", chess.D4)
    assert board._canvas.getpixel((239, 239)) != (0, 0, 0, 255)


# Test _Headers

@pytest.fixture()
def chess_game():
    def _chess_game(pgn: str) -> chess.Board:
        return chess.pgn.read_game(open(f"tests/test_data/{pgn}"))
    return _chess_game


@pytest.fixture()
def headers(chess_game: chess.pgn.Game) -> _Board:
    captures = [
        chess.Piece(chess.PAWN, chess.WHITE),
        chess.Piece(chess.PAWN, chess.BLACK),
        chess.Piece(chess.ROOK, chess.WHITE),
        chess.Piece(chess.ROOK, chess.BLACK)
    ]
    return _Headers(chess_game(PGN_CLOCK_ANNOTATIONS).next().next(), captures, (400, 40))


def test_draw_headers_size(headers: _Headers):
    assert headers.image(chess.WHITE).size == (400, 40)
    assert headers.image(chess.BLACK).size == (400, 40)

# Test _EvalBar

@pytest.mark.parametrize(
        "eval, max_eval, reverse, expected",
        [
            (Cp(1000), 1000, False, 0),   # Max white
            (Cp(1500), 1000, False, 0),   # >Max white
            (Mate(2), 1000, False, 0),    # White mate in 2
            (Cp(500), 1000, False, 100),    # White ahead
            (PovScore(Mate(0), chess.BLACK).white(), 1000, False, 0), # White has won
            (Cp(-1000), 1000, False, 400),    # Max black
            (Cp(-1500), 1000, False, 400),    # >Max black
            (Mate(-2), 1000, False, 400),     # Black mate in 2
            (Cp(-500), 1000, False, 300),    # Black ahead
            (PovScore(Mate(0), chess.WHITE).white(), 1000, False, 400), # Black has won
            (Cp(0), 1000, False, 200),      # Equal

            (Cp(1000), 1000, True, 400),   # Max white reversed
            (Cp(1500), 1000, True, 400),   # >Max white reversed
            (Mate(2), 1000, True, 400),    # White mate in 2 reversed
            (Cp(500), 1000, True, 300),    # White ahead reversed
            (PovScore(Mate(0), chess.BLACK).white(), 1000, True, 400), # White has won reversed
            (Cp(-1000), 1000, True, 0),    # Max black reversed
            (Cp(-1500), 1000, True, 0),    # >Max black reversed
            (Mate(-2), 1000, True, 0),     # Black mate in 2 reversed
            (PovScore(Mate(0), chess.WHITE).white(), 1000, True, 0), # Black has won reversed
            (Cp(0), 1000, True, 200),      # Equal reversed
        ]
)
def test_get_bar_position(eval, max_eval, reverse, expected):
    bar = _EvalBar((30, 400), eval, max_eval, reverse)
    assert bar._get_bar_position(eval) == expected

@pytest.mark.parametrize(
        "eval, text, color, pos, anchor, reverse",
        [
            (Cp(1000), "+10.0", "black", 400, "md", False),
            (Mate(2), "M2", "black", 400, "md", False),
            (Cp(-1000), "-10.0", "white", 0, "ma", False),
            (Mate(-2), "M2", "white", 0, "ma", False),
            (Cp(0), "+0.0", "white", 0, "ma", False),
            (Cp(1000), "+10.0", "black", 0, "ma", True),
            (Mate(2), "M2", "black", 0, "ma", True),
            (Cp(-1000), "-10.0", "white", 400, "md", True),
            (Mate(-2), "M2", "white", 400, "md", True),
            (Cp(0), "+0.0", "white", 400, "md", True),
        ]
)
def test_get_bar_text(eval, text, color, pos, anchor, reverse):
    bar = _EvalBar((30, 400), eval, 1000, reverse)
    es = bar._get_bar_text(eval)
    assert es["text"] == text
    assert es["color"] == color
    assert es["pos"] == pos
    assert es["anchor"] == anchor


@pytest.mark.parametrize(
        "score, reverse, expected",
        [
            (Cp(500), False, (0, 0, 0, 255)),
            (Cp(-500), False, (0, 0, 0, 255)),
            (Cp(950), False, (255, 255, 255, 255)),
            (Cp(-950), False, (0, 0, 0, 255)),
            (Cp(0), False, (0, 0, 0, 255)),
            (Cp(500), True, (255, 255, 255, 255)),
            (Cp(-500), True, (255, 255, 255, 255)),
            (Cp(950), True, (255, 255, 255, 255)),
            (Cp(-950), True, (0, 0, 0, 255)),
            (Cp(0), True, (255, 255, 255, 255))
        ]
)
def test_draw_eval_bar(score, reverse, expected):
    bar = _EvalBar((30, 400), score, 1000, reverse)
    assert bar._canvas.getpixel((15, 40)) == expected

# Test _Graph

@pytest.fixture()
def chess_game_graph():
    def _chess_game() -> chess.Board:
        with open(f"tests/test_data/{PGN_EVAL_ANNOTATIONS}") as pgn:
            chess.pgn.read_game(pgn)  # skip to second game
            return chess.pgn.read_game(pgn)
    return _chess_game()

@pytest.mark.parametrize(
        "eval, move, expected",
        [
            (Cp(0), 0, Coord(0, 49)),
            (Cp(1000), 1, Coord(23, 0)),
            (Cp(-1000), 17, Coord(400, 99)),
            (Cp(500), 10, Coord(235, 24)),
            (Cp(1500), 1, Coord(23, 0)),
            (Cp(-1500), 17, Coord(400, 99)),
            (Mate(-2), 15, Coord(352, 99)),
            (Mate(2), 15, Coord(352, 0)),
            (PovScore(Mate(0), chess.WHITE).white(), 17, Coord(400, 99)),
            (PovScore(Mate(0), chess.BLACK).white(), 17, Coord(400, 0))
        ]
)
def test_get_graph_position(chess_game_graph, eval, move, expected):
    graph = _Graph(chess_game_graph, (100, 25), 1000, 1)
    assert graph._get_graph_position(eval, move) == expected

@pytest.mark.parametrize(
        "move_num, coord",
        [
            (5, (176, 99)),
            (9, (317, 149)),
            (17, (599, 69))
        ]
)
def test_at_move(chess_game_graph, move_num, coord):
    graph = _Graph(chess_game_graph, (600, 200), 1000, 1)
    assert graph.at_move(move_num).getpixel(coord) == (255, 0, 0, 255)

def test_at_move_error(chess_game_graph):
    graph = _Graph(chess_game_graph, (600, 200), 1000, 1)
    with pytest.raises(MoveOutOfRangeError):
        graph.at_move(18)
