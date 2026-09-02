"""Smoke test for built gifpgn packages (wheel/sdist).

Run in an isolated environment containing only the built distribution and its
declared dependencies (no pytest, no source checkout on sys.path):

    uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
"""

import sys
from io import BytesIO, StringIO

import chess.pgn
from PIL import Image

import gifpgn
from gifpgn import CreateGifFromPGN, PieceTheme, BoardThemes


SAMPLE_PGN = """
[Event "Smoke Test"]
[Site "?"]
[Date "1620.??.??"]
[Round "?"]
[White "Gioachino Greco"]
[Black "NN"]
[Result "1-0"]

{ [%eval 0.32,18] } 1. e3 { [%eval 0.14,18] } 1... e5 { [%eval 0.25,18] } 2. Qh5 { [%eval -0.90,18] } 
2... Nc6 { [%eval -0.95,18] } 3. Bc4 { [%eval -1.34,18] } 3... Nf6 { [%eval #1,18] } 4. Qxf7# 1-0
"""


def main() -> None:
    print(f"gifpgn version: {gifpgn.__version__}")

    game = chess.pgn.read_game(StringIO(SAMPLE_PGN))
    assert game is not None, "Failed to parse sample PGN"

    gif = CreateGifFromPGN(game)
    gif.board_size = 240
    gif.piece_theme = PieceTheme.ALPHA
    gif.square_colors = BoardThemes.BROWN
    gif.add_analysis_bar()  # exercises package-data/font loading too

    result = gif.generate()
    assert isinstance(result, BytesIO), "generate() did not return a BytesIO"

    data = result.getvalue()
    assert data.startswith(b"GIF8"), "Output does not have a valid GIF header"

    image = Image.open(BytesIO(data))
    assert image.format == "GIF"
    n_frames = getattr(image, "n_frames", 1)
    assert n_frames > 1, "Expected an animated (multi-frame) GIF"

    print(f"OK: generated {len(data)} byte GIF with {n_frames} frames")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        sys.exit(1)
