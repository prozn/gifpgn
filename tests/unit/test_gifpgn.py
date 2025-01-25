import pytest

from gifpgn import CreateGifFromPGN
from gifpgn.exceptions import MissingAnalysisError
import chess.pgn
import chess.engine
from PIL import Image

PGN_NO_ANNOTATIONS = "test_no_annotations.pgn"
PGN_EVAL_ANNOTATIONS = "test_eval_annotations.pgn"
PGN_NO_MOVES = "test_no_moves.pgn"
PGN_EMPTY = "test_empty.pgn"

### Fixtures ###

@pytest.fixture()
def game():
    def _game(pgn):
        return CreateGifFromPGN(chess.pgn.read_game(open(f"tests/test_data/{pgn}")))
    return _game

@pytest.fixture
def engine():
    e = chess.engine.SimpleEngine.popen_uci("stockfish")
    yield e
    e.close()

@pytest.fixture
def enginelimit():
    return chess.engine.Limit(depth=6)

### gifpgn Tests ###

def test_init(game):
    assert game(PGN_NO_ANNOTATIONS)._game_root.end().ply() == 7

    with pytest.raises(ValueError) as e:
        game(PGN_EMPTY)
    assert str(e.value) == "Provided game is not valid/empty"

    with pytest.raises(ValueError) as e:
        game(PGN_NO_MOVES)
    assert str(e.value) == "Provided game does not have any moves."

def test_board_size(game):
    g = game(PGN_NO_ANNOTATIONS)
    g.board_size = 245

    assert g._board_size == 240
    assert g._sq_size == 30
    assert len(g._pieces.items()) == 0
    assert len(g._square_images.items()) == 0

@pytest.mark.parametrize("method",["add_analysis_bar","add_analysis_graph","enable_nags"])
def test_missing_analysis(game, method):
    g = game(PGN_NO_ANNOTATIONS)

    with pytest.raises(MissingAnalysisError) as e:
        m = getattr(g, method)()
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

def test_pgn_has_analysis(game):
    assert game(PGN_EVAL_ANNOTATIONS).pgn_has_analysis() == True
    assert game(PGN_NO_ANNOTATIONS).pgn_has_analysis() == False

def test_add_analysis_to_pgn(game, engine, enginelimit):
    g = game(PGN_NO_ANNOTATIONS)
    assert g.pgn_has_analysis() == False
    g.add_analysis_to_pgn(engine, enginelimit)
    assert g.pgn_has_analysis() == True

# Covers draw_board, draw_squares, draw_square
def test_draw_board(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    g.board_size = 240
    g.square_colors = {chess.WHITE: '#ffffff', chess.BLACK: 'black'}
    g._game = g._game_root
    g._draw_board()
    assert g._board_image.getpixel((0,0)) == (255, 255, 255, 255)
    assert g._board_image.getpixel((239,0)) == (0, 0, 0, 255)
    assert g._board_image.getpixel((120,120)) == (255, 255, 255, 255)

def test_draw_arrow(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    g.board_size = 240
    g.square_colors = {chess.WHITE: 'black', chess.BLACK: 'black'}
    g._game = g._game_root
    g._draw_board()

    g._draw_arrow(chess.A1, chess.H8, "red")
    assert g._board_image.getpixel((120,120))[0] > 0
    assert g._board_image.getpixel((120,120))[1] == 0

    g._draw_arrow(chess.A6, chess.B5, "blue")
    assert g._board_image.getpixel((1,1)) == (0, 0, 0, 255)
    assert g._board_image.getpixel((30,90))[2] > 0
    assert g._board_image.getpixel((30,90))[0] == 0

def test_headers(game):
    g: CreateGifFromPGN = game(PGN_NO_ANNOTATIONS)
    g.board_size = 240
    g.add_headers(25)
    assert g._header_size == 25
    gif = g.generate()
    with Image.open(gif).convert("RGBA") as frame:
        assert frame.size == (240, 290)
        assert frame.getpixel((120,5)) == (0, 0, 0, 255)
        # have to use approx +/-1 here due to gif compression??? white is grey I guess
        assert pytest.approx(frame.getpixel((120,270)), abs=1) == (255, 255, 255, 255)
    g.reverse_board()
    gif = g.generate()
    with Image.open(gif).convert("RGBA") as frame:
        assert frame.size == (240, 290)
        assert frame.getpixel((120,270)) == (0, 0, 0, 255)
        # have to use approx +/-1 here due to gif compression??? white is grey I guess
        assert pytest.approx(frame.getpixel((120,5)), abs=1) == (255, 255, 255, 255)


### geometry Tests ###