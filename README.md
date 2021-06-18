# gifpgn
Generate a GIF of a chess game from a PGN with optional stockfish analysis chart.
## Installation
 ``pip install gifpgn``

For stockfish analysis a local stockfish binary is required.
For best performance you can compile your own with support for the fastest instruction sets available on your hardware. Alternatively you can install using your distribution's package manager.

eg. ``apt-get install stockfish``

## Usage
1. Import the package:

``from gifpgn import CreateGifFromPGN``

2. Initialise the class:
	- Using a PGN string:
  
	``gif = CreateGifFromPGN(pgn_string)``
  
	- Using a PGN file:
  
	``gif = CreateGifFromPGN(path_to_pgn,pgn_file=True)``

3. Optionally enable stockfish evaluation:

``gif.enable_evaluation()``

4. Generate the GIF:

``gif.generate(output_file_path)``

See reference section for optional parameters.

## Reference
```python
class  CreateGifFromPGN()
```
**Arguments**:
-  `pgn`  _str_ - PGN as a string or filepath. Filepath requires optional parameter pgn_file=True
-  `reverse`  _bool, optional_ - Whether board should be reversed. Defaults to False.
-  `duration`  _float, optional_ - Duration of each GIF frame in seconds. Defaults to 0.5.
-  `pgn_file`  _bool, optional_ - Specify whether pgn contains a pgn string [False] or filepath [True]. Defaults to False.

**Properties**
- `board_size` _int_ - Size of the board in pixels. Defaults to 480.
- `bar_size` _int_ - Width of the evaluation bar in pixels. Defaults to 30.
- `graph_size` _int_ - Height of the evaluation graph in pixels. Defaults to 81.
- `ws_color` _str_ - Color of the white squares. Defaults to "#f0d9b5".
- `bs_color` _str_ - Color of the black squares. Defaults to "#b58863".
- `max_eval` _int_ - Maximum position evaluation in centipawns. Defaults to 1000.

#### enable\_evaluation
```python
| enable_evaluation(path_to_stockfish='stockfish', depth: int = 18, threads: int = 1, memory: int = 1024)
```
Enable stockfish evaluation

**Arguments**:
-  `path_to_stockfish`  _str, optional_ - Path to stockfish binary. Defaults to 'stockfish'.
-  `depth`  _int, optional_ - Depth of stockfish evaluation. Defaults to 18.
-  `threads`  _int, optional_ - Number of threads to use in stockfish evaluation. Defaults to 1.
-  `memory`  _int, optional_ - Amount of memory to use in stockfish evaluation in Mb. Defaults to 1024.

#### generate
```python
| generate(output_file: str)
```
Output GIF

**Arguments**:
-  `output_file`  _str_ - Full path and filename of output file