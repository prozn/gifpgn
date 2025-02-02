import pytest

from gifpgn import CreateGifFromPGN
from gifpgn.exceptions import MissingAnalysisError
from gifpgn._types import BoardTheme, PieceTheme

import chess.pgn
from PIL import Image


# Test files

PGN_NO_ANNOTATIONS = "test_no_annotations.pgn"
PGN_EVAL_ANNOTATIONS = "test_eval_annotations.pgn"
PGN_NO_MOVES = "test_no_moves.pgn"
PGN_EMPTY = "test_empty.pgn"


# Fixtures


@pytest.fixture()
def game():
    def _game(pgn, game_num: int = 0):
        f = open(f"tests/test_data/{pgn}")
        pgn = chess.pgn.read_game(f)
        for _ in range(0, game_num):
            pgn = chess.pgn.read_game(f)
        return CreateGifFromPGN(pgn)
    return _game


# Tests


def test_init(game: CreateGifFromPGN):
    assert game(PGN_NO_ANNOTATIONS)._game_root.end().ply() == 7

    with pytest.raises(ValueError) as e:
        game(PGN_EMPTY)
    assert str(e.value) == "Provided game is not valid/empty"

    with pytest.raises(ValueError) as e:
        game(PGN_NO_MOVES)
    assert str(e.value) == "Provided game does not have any moves."


def test_board_size(game: CreateGifFromPGN):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    g.board_size = 245
    assert g._board_size == 240
    assert g.board_size == 240


@pytest.mark.parametrize("method", ["add_analysis_bar", "add_analysis_graph", "enable_nags"])
def test_missing_analysis(game, method):
    g = game(PGN_NO_ANNOTATIONS)
    with pytest.raises(MissingAnalysisError) as e:
        getattr(g, method)()
    assert str(e.value) == "PGN did not contain evaluations for every half move"


@pytest.mark.parametrize(
        "method, var, val", [
            ("add_analysis_bar", "_bar_size", 30),
            ("add_analysis_graph", "_graph_size", 81),
            ("enable_nags", "_nag", True)
        ])
def test_has_analysis(game, method, var, val):
    g = game(PGN_EVAL_ANNOTATIONS)
    getattr(g, method)()
    assert getattr(g, var) == val


def test_square_colors(game: CreateGifFromPGN):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    assert isinstance(g.square_colors, BoardTheme)
    assert g.square_colors.square_color(chess.WHITE) == "#f0d9b5"
    g.square_colors = BoardTheme("white", "#000000")
    assert g.square_colors.square_color(chess.WHITE) == "white"
    assert g.square_colors.square_color(chess.BLACK) == "#000000"
    g.square_colors = {chess.WHITE: "#FF0000", chess.BLACK: "#00FF00"}
    assert g.square_colors.square_color(chess.WHITE) == "#FF0000"
    assert g.square_colors.square_color(chess.BLACK) == "#00FF00"
    with pytest.raises(ValueError):
        g.square_colors = {chess.WHITE: "#FF0000", "BLACK": "#00FF00"}
    with pytest.raises(ValueError):
        g.square_colors = []


def test_piece_theme(game: CreateGifFromPGN):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    g.piece_theme = PieceTheme.CASES
    assert g.piece_theme.value == "cases"
    with pytest.raises(ValueError):
        g.piece_theme = "cases"


def test_headers(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    assert g._header_size is None
    g.add_headers(25)
    assert g._header_size == 25


def test_reverse(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    assert g._reverse is False
    g.reverse_board()
    assert g._reverse is True


def test_arrows(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    assert g._arrows is False
    g.enable_arrows()
    assert g._arrows is True


def test_generate_board_only(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    g.board_size = 240
    gif = g.generate()
    with Image.open(gif).convert("RGBA") as frame:
        assert frame.size == (240, 240)

def test_generate_board_headers(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    g.board_size = 240
    g.add_headers(25)
    gif = g.generate()
    with Image.open(gif).convert("RGBA") as frame:
        assert frame.size == (240, 290)
        assert frame.getpixel((120, 5)) == (0, 0, 0, 255)

def test_generate_board_headers_reversed(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    g.board_size = 240
    g.add_headers(25)
    g.reverse_board()
    gif = g.generate()
    with Image.open(gif).convert("RGBA") as frame:
        assert frame.size == (240, 290)
        assert frame.getpixel((120, 270)) == (0, 0, 0, 255)

def test_generate_en_passant(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS, 1)
    g.piece_theme = PieceTheme.CASES
    g.board_size = 240
    g. add_headers(25)
    gif = g.generate()
    with Image.open(gif) as gif:
        gif.seek(5)
        with gif.convert("RGBA") as frame:
            assert frame.getpixel((43, 277)) == (0, 0, 0, 255)

def test_generate_capture(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS, 1)
    g.piece_theme = PieceTheme.CASES
    g.board_size = 240
    g. add_headers(25)
    gif = g.generate()
    with Image.open(gif) as gif:
        gif.seek(6)
        with gif.convert("RGBA") as frame:
            assert frame.getpixel((43, 18)) == pytest.approx((255, 255, 255, 255), abs=2)  # white pawn should be here

def test_generate_check_arrow(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS, 1)
    g.square_colors = BoardTheme("#000000", "#000000")
    g.board_size = 240
    g.enable_arrows()
    gif = g.generate()
    with Image.open(gif) as gif:
        gif.seek(7)
        with gif.convert("RGBA") as frame:
            assert frame.getpixel((88, 61))[0] > 0   # If red here, arrow was drawn
            assert frame.getpixel((95, 61))[0] == 0  # If arrow correct should be black here

def test_generate_eval_graph(game):
    g: CreateGifFromPGN = game(PGN_EVAL_ANNOTATIONS)
    g.board_size = 400
    g.add_analysis_graph(60, 2)
    gif = g.generate()
    with Image.open(gif).convert("RGBA") as frame:
        assert frame.size == (400, 460)

def test_generate_nags(game):
    g: CreateGifFromPGN = game(PGN_EVAL_ANNOTATIONS)
    g.square_colors = BoardTheme("#000000", "#000000")
    g.board_size = 400
    g.enable_nags()
    gif = g.generate()
    with Image.open(gif) as gif:
        gif.seek(3)
        with gif.convert("RGBA") as frame:
            assert all(frame.getpixel((378, 150)))  # Not black

def test_generate_eval_bar(game):
    g: CreateGifFromPGN = game(PGN_EVAL_ANNOTATIONS)
    g.board_size = 240
    g.add_analysis_bar(20)
    gif = g.generate()
    with Image.open(gif).convert("RGBA") as frame:
        assert frame.size == (260, 240)

def test_generate_save_image(game, tmpdir):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    g.board_size = 240
    temp_path = str(tmpdir.mkdir("gifpgn").join("gifpgn_test.gif"))
    g.generate(temp_path)
    with Image.open(temp_path) as img:
        assert img.size == (240, 240)
