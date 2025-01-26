import pytest

from gifpgn import CreateGifFromPGN
from gifpgn.exceptions import MissingAnalysisError

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
    def _game(pgn):
        return CreateGifFromPGN(chess.pgn.read_game(open(f"tests/test_data/{pgn}")))
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


def test_square_colors(game):
    g = game(PGN_NO_ANNOTATIONS)
    assert isinstance(g.square_colors, dict)
    for k, v in g.square_colors.items():
        assert isinstance(k, chess.Color)
        assert isinstance(v, str)
    g.square_colors = {chess.WHITE: "white", chess.BLACK: "#000000"}
    assert g.square_colors == {chess.WHITE: "white", chess.BLACK: "#000000"}


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


def test_generate(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)

    g.board_size = 240
    gif = g.generate()
    with Image.open(gif).convert("RGBA") as frame:
        assert frame.size == (240, 240)

    g.add_headers(25)
    gif = g.generate()
    with Image.open(gif).convert("RGBA") as frame:
        assert frame.size == (240, 290)
        assert frame.getpixel((120, 5)) == (0, 0, 0, 255)

    g.reverse_board()
    gif = g.generate()
    with Image.open(gif).convert("RGBA") as frame:
        assert frame.size == (240, 290)
        assert frame.getpixel((120, 270)) == (0, 0, 0, 255)
