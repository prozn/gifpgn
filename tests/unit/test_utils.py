import pytest

from gifpgn.exceptions import MissingAnalysisError
from gifpgn.utils import (
    PGN,
    _eval,
    _font_size_approx
)

import chess.pgn
import chess.engine

from importlib.resources import files

PGN_NO_ANNOTATIONS = "test_no_annotations.pgn"
PGN_EVAL_ANNOTATIONS = "test_eval_annotations.pgn"
PGN_NO_MOVES = "test_no_moves.pgn"
PGN_EMPTY = "test_empty.pgn"

@pytest.fixture()
def game():
    def _game(pgn, game_num: int = 0):
        f = open(f"tests/test_data/{pgn}")
        pgn = chess.pgn.read_game(f)
        for _ in range(0, game_num):
            pgn = chess.pgn.read_game(f)
        return pgn
    return _game

# test PGN class

def test_pgn_has_analysis_true(game):
    pgn = PGN(game(PGN_EVAL_ANNOTATIONS))
    assert pgn.has_analysis() is True

def test_pgn_has_analysis_false(game):
    pgn = PGN(game(PGN_NO_ANNOTATIONS))
    assert pgn.has_analysis() is False

def test_pgn_has_analysis_one_missing_annotation(game):
    pgn = PGN(game(PGN_EVAL_ANNOTATIONS, 2))
    assert pgn.has_analysis() is False

def test_pgn_has_analysis_no_moves(game):
    with pytest.raises(ValueError):
        PGN(game(PGN_NO_MOVES))

def test_pgn_has_analysis_empty_pgn(game):
    with pytest.raises(ValueError):
        PGN(game(PGN_EMPTY))

def test_pgn_add_analysis(game):
    pgn = PGN(game(PGN_NO_ANNOTATIONS))
    assert pgn.has_analysis() is False
    with chess.engine.SimpleEngine.popen_uci("stockfish") as engine:
        game_annotated = pgn.add_analysis(engine, chess.engine.Limit(depth=5))
    pgn2 = PGN(game_annotated)
    assert pgn2.has_analysis() is True

def test_pgn_export(game):
    pgn = PGN(game(PGN_EVAL_ANNOTATIONS))
    assert type(pgn.export()) is str
    assert str(pgn) == pgn.export()

def test_pgn_acpl(game):
    pgn = PGN(game(PGN_EVAL_ANNOTATIONS))
    assert pgn.acpl() == {chess.WHITE: 42, chess.BLACK: 379}
    pgn = PGN(game(PGN_EVAL_ANNOTATIONS, 1))
    assert pgn.acpl() == {chess.WHITE: 176, chess.BLACK: 232}

def test_pgn_acpl_missing_analysis(game):
    pgn = PGN(game(PGN_NO_ANNOTATIONS))
    with pytest.raises(MissingAnalysisError):
        pgn.acpl()

# test _eval function

def test_eval(game):
    assert _eval(game(PGN_EVAL_ANNOTATIONS)) == chess.engine.PovScore(chess.engine.Cp(32), chess.WHITE)    

def test_eval_mate(game):
    assert _eval(game(PGN_EVAL_ANNOTATIONS).end()) == chess.engine.PovScore(chess.engine.Mate(0), chess.BLACK)

def test_eval_no_annotations(game):
    with pytest.raises(MissingAnalysisError):
        _eval(game(PGN_NO_ANNOTATIONS))

# test _font_size_approx function

def test_font_size_approx():
    font = files("gifpgn.fonts").joinpath("Carlito-Regular.ttf").read_bytes()
    assert _font_size_approx("test", font, 100, 0.75, 10) == 48
    assert _font_size_approx("test", font, 50, 0.75, 10) == 24
    assert _font_size_approx("testtest", font, 100, 0.75, 10) == 24

def test_font_size_approx_min():
    font = files("gifpgn.fonts").joinpath("Carlito-Regular.ttf").read_bytes()
    assert _font_size_approx("test", font, 10, 0.75, 10) == 10
    assert _font_size_approx("test", font, 10, 0.75, 1) == 4