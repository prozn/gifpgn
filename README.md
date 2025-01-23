# gifpgn

Generate a GIF of a chess game from a PGN with optional:

* Analysis bar
* Analysis chart
* Numerical Annotation Glyphs (NAGs)
* Move and check arrows

## Demo

### Demo with all features enabled

```python
import chess
import chess.engine
import chess.pgn
import io
from gifpgn import CreateGifFromPGN, MissingAnalysisError

pgn_string = ...
game = chess.pgn.read_game(io.StringIO(pgn_string))
g = CreateGifFromPGN(game)
g.enable_arrows()
g.add_headers(height=20)
try:
	g.add_analysis_bar()    
except MissingAnalysisError:
	with chess.engine.SimpleEngine.popen_uci("/path/to/stockfish") as engine:
		g.add_analysis_to_pgn(engine, chess.engine.Limit(depth=18))
	g.add_analysis_bar()
g.add_analysis_graph()
g.enable_nags()
gif = g.generate("test_gif.gif")
```

![image](https://i.imgur.com/hxQM0cl.gif)

### Small GIF with no analysis

```python
import chess.pgn
import io
from from gifpgn import CreateGifFromPGN

pgn_string = ...
game = chess.pgn.read_game(io.StringIO(pgn_string))
g = CreateGifFromPGN(game)
g.board_size = 240
g.generate("test_small_gif.gif")
```

![image](https://i.imgur.com/HkT2K8k.gif)

### *class* gifpgn.gifpgn.CreateGifFromPGN(game: Game)

* **Parameters:**
  **game** (*chess.pgn.Game*) – An instance of `chess.pgn.Game` from the python-chess library.

#### add_analysis_bar(width: int = 30) → None

Adds an analysis bar to the right side of the chess board.

#### NOTE
Requires that a PGN has been loaded with `[%eval ...]` annotations for
each half move.

Alternatively the PGN can be decorated using the add_analysis_to_pgn method.

* **Parameters:**
  **width** (*int*) – Width of the analysis bar in pixels, defaults to 30
* **Raises:**
  [**MissingAnalysisError**](#gifpgn.exceptions.MissingAnalysisError) – At least one ply in the PGN has a missing `[%eval ...]` annotation

#### add_analysis_graph(height: int = 81) → None

Adds an analysis graph to the bottom of the chess board.

#### NOTE
Requires that a PGN has been loaded with `[%eval ...]` annotations for
each half move.

Alternatively the PGN can be decorated using the add_analysis_to_pgn method.

* **Parameters:**
  **height** (*int*) – Height of the analysis graph in pixels, defaults to 81
* **Raises:**
  [**MissingAnalysisError**](#gifpgn.exceptions.MissingAnalysisError) – At least one ply in the PGN has a missing `[%eval ...]` annotation

#### add_analysis_to_pgn(engine: SimpleEngine, engine_limit: Limit) → None

Calculates and adds [%eval …] annotations to each half move in the PGN

```python
game = chess.pgn.read_game(io.StringIO(pgn_string))
engine = chess.engine.SimpleEngine.popen_uci("/path/to/stockfish")
limit = chess.engine.Limit(depth=18)
gif = CreateGifFromPGN(game)
gif.add_analysis_to_pgn(engine, limit)
engine.close()
...
```

#### WARNING
Engine analysis is a CPU intensive operation, ensure that an appropriate
limit is applied.

A depth limit of 18 provides a reasonable trade-off
between accuracy and compute time.

#### NOTE
Once you have finished with the chess.engine.SimpleEngine instance it should be
closed using the close() method. Otherwise your program will not exit as expected.

* **Parameters:**
  * **engine** (*chess.engine.SimpleEngine*) – Instance of [chess.engine.SimpleEngine](https://python-chess.readthedocs.io/en/latest/engine.html) from python-chess
  * **engine_limit** (*chess.engine.Limit*) – Instance of [chess.engine.Limit](https://python-chess.readthedocs.io/en/latest/engine.html#chess.engine.Limit) from python-chess

#### add_headers(height: int = 20) → None

Adds headers with player names, captured pieces, and clock (if PGN contains 
`[%clk ...]` annotations) to the top and bottom of the chess board.

* **Parameters:**
  **height** (*int*) – Height of headers in pixels, defaults to 20

#### *property* board_size *: int*

int: Size of the board in pixels, defaults to 480

#### NOTE
Size will be rounded down to the nearest multiple of 8

#### enable_arrows()

Enables move and check arrows

#### enable_nags()

Enable numerical annoation glyphs

#### NOTE
Requires that a PGN has been loaded with `[%eval ...]` annotations for
each half move.

Alternatively the PGN can be decorated using the add_analysis_to_pgn method.

* **Raises:**
  [**MissingAnalysisError**](#gifpgn.exceptions.MissingAnalysisError) – At least one ply in the PGN has a missing `[%eval ...]` annotation

#### *property* frame_duration *: float*

float: Duration of each frame in seconds, defaults to 0.5

#### generate(output_file: str | None = None) → BytesIO | None

Generate the GIF and either save it to the specified file path or return the
raw bytes if no file path is specified.

```python
game = chess.pgn.read_game(io.StringIO(pgn_string))
engine = chess.engine.SimpleEngine.popen_uci("/path/to/stockfish")
limit = chess.engine.Limit(depth=18)
gif = CreateGifFromPGN(game)
gif.add_analysis_to_pgn(engine, limit)

...
```

* **Parameters:**
  **output_file** (*Optional* *[**str* *]*) – Filepath to save to, defaults to None
* **Return Optional[BytesIO]:**
  Raw bytes of the generated GIF if `output_file` parameter is set, else returns `None`

#### *property* max_eval *: int*

int: Maximum evaluation displayed on analysis graph or bar, defaults to 1000

#### pgn_has_analysis() → bool

Checks that every half move in the PGN has `[%eval ...]` annotations

Returns:
: bool: True if every half move has `[%eval ...]` annotations, False otherwise

#### reverse_board()

Reverses the board so that black is at the bottom

#### *property* square_colors *: Dict[bool, str]*

Dict[chess.Color, str]: A dict mapping each chess.Color to a color format understandable by PIL

## gifpgn.exceptions module

### *exception* gifpgn.exceptions.MissingAnalysisError

Bases: `Exception`

PGN did not contain an `[%eval ...]` annotation for every ply

### *exception* gifpgn.exceptions.MoveOutOfRangeError(move, range)

Bases: `Exception`

Requested move was higher than the game length
