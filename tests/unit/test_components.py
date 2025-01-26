import pytest

from gifpgn import CreateGifFromPGN
from gifpgn.components import (
    _Board,
    _Graph,
    _EvalBar,
    _Headers,
    _Canvas,
    _AssetImage,
    _Piece
)

import chess.pgn
from PIL import Image


# Test files

PGN_NO_ANNOTATIONS = "test_no_annotations.pgn"
PGN_EVAL_ANNOTATIONS = "test_eval_annotations.pgn"
PGN_NO_MOVES = "test_no_moves.pgn"
PGN_EMPTY = "test_empty.pgn"

# Test _Canvas

@pytest.fixture()
def c() -> _Canvas:
    return _Canvas(480, 20, 50, 10, False)

def test_canvas_size(c):
    assert c.size() == (500, 550)

def test_canvas_headers(c):
    c.add_headers(
        white = Image.new('RGBA', (c.size()[0], 20), "#0000ff"),
        black = Image.new('RGBA', (c.size()[0], 20), "#00ff00")
    )
    assert c._canvas.getpixel((240, 5)) == (0, 255, 0, 255)
    assert c._canvas.getpixel((240, 495)) == (0, 0, 255, 255)

    c = _Canvas(480, 20, 50, 10, True)
    c.add_headers(
        white = Image.new('RGBA', (c.size()[0], 20), "#0000ff"),
        black = Image.new('RGBA', (c.size()[0], 20), "#00ff00")
    )
    assert c._canvas.getpixel((240, 495)) == (0, 255, 0, 255)
    assert c._canvas.getpixel((240, 5)) == (0, 0, 255, 255)

def test_add_board(c):
    c.add_board(Image.new('RGBA', (480, 480), "#00ffff"))
    assert c._canvas.getpixel((0, 9)) == (255, 0, 0, 255)
    assert c._canvas.getpixel((0, 10)) == (0, 255, 255, 255)
    assert c._canvas.getpixel((479, 245)) == (0, 255, 255, 255)
    assert c._canvas.getpixel((480, 245)) == (255, 0, 0, 255)

def test_add_bar(c):
    c.add_bar(Image.new('RGBA', (20, 480), "#00ffff"))
    assert c._canvas.getpixel((480, 9)) == (255, 0, 0, 255)
    assert c._canvas.getpixel((480, 10)) == (0, 255, 255, 255)
    assert c._canvas.getpixel((479, 10)) == (255, 0, 0, 255)

def test_add_graph(c):
    c.add_graph(Image.new('RGBA', (c.size()[0], 50), "#00ffff"))
    assert c._canvas.getpixel((0, 499)) == (255, 0, 0, 255)
    assert c._canvas.getpixel((0, 500)) == (0, 255, 255, 255)
    assert c._canvas.getpixel((499, 500)) == (0, 255, 255, 255)

# Test _AssetImage and _Piece

def test_asset_image():
    a = _AssetImage("blunder", 20).image()
    assert a.size == (20, 20)
    assert "blunder-20" in _AssetImage._images

def test_piece_image():
    p = _Piece(chess.Piece(chess.KNIGHT, chess.WHITE), 40).image()
    assert p.size == (40, 40)
    assert "wn-40" in _AssetImage._images

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
        {
            chess.WHITE: "#ff0000",
            chess.BLACK: "#00ff00"
        }
    )

def test_board(board: _Board):
    assert board._board_size == 480
    assert board._sq_size == 60
    assert len(board._pieces.keys()) == 0
    assert len(board._square_images.keys()) == 2
    assert board._square_images[chess.WHITE].getpixel((30, 30)) == (255, 0, 0, 255)
    assert board._square_images[chess.BLACK].getpixel((30, 30)) == (0, 255, 0, 255)

def test_draw_square(board: _Board):
    board._canvas = Image.new('RGBA', (480, 480), "#0000ff")
    board.draw_square(chess.A3)
    assert board._canvas.getpixel((30, 330)) == (0, 255, 0, 255)
    board.draw_square(chess.D5)
    assert board._canvas.getpixel((185, 185)) == (255, 0, 0, 255)

def test_get_square_position(board: _Board):
    board.board_size = 240
    assert board.get_square_position(chess.A1) == (0, 210)
    assert board.get_square_position(chess.H8) == (210, 0)
    board.reverse = True
    assert board.get_square_position(chess.A1) == (210, 0)
    assert board.get_square_position(chess.H8) == (0, 210)

def test_get_square_color(board: _Board):
    assert board.get_square_color(chess.A4) == chess.WHITE
    assert board.get_square_color(chess.H6) == chess.BLACK

def test_get_square_image(board: _Board):
    assert board.get_square_image(chess.A6).getpixel((5, 5)) == (255, 0, 0, 255)
    assert board.get_square_image(chess.E3).getpixel((5, 5)) == (0, 255, 0, 255)

def test_draw_arrow(board: _Board):
    board.board_size = 240
    board.square_colors = {chess.WHITE: "#000000", chess.BLACK: "#000000"}
    board.draw_board()
    board.draw_arrow(chess.A1, chess.H8, "red")
    assert board._canvas.getpixel((120,120))[0] > 0
    assert board._canvas.getpixel((120,120))[1] == 0

    board.draw_arrow(chess.A6, chess.B5, "blue")
    assert board._canvas.getpixel((0,0)) == (0, 0, 0, 255)
    assert board._canvas.getpixel((30,90))[2] > 0
    assert board._canvas.getpixel((30,90))[0] == 0

def test_draw_nag(board: _Board):
    board.square_colors = {chess.WHITE: "#000000", chess.BLACK: "#000000"}
    board.draw_board()
    assert board._canvas.getpixel((239, 239)) == (0, 0, 0, 255)
    board.draw_nag("blunder", chess.D4)
    assert board._canvas.getpixel((239, 239)) != (0, 0, 0, 255)

# Test _Headers


# Test _EvalBar


# Test _Graph