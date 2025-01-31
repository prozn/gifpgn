gifpgn: Chess GIF Generator for Python
======================================

.. image:: https://img.shields.io/pypi/v/gifpgn?color=blue
    :target: https://pypi.org/project/gifpgn/
    :alt: PyPI

.. image:: https://img.shields.io/pypi/dm/gifpgn
    :target: https://pypistats.org/packages/gifpgn
    :alt: Downloads

.. image:: https://github.com/prozn/gifpgn/actions/workflows/run_tests.yml/badge.svg
    :target: https://github.com/prozn/gifpgn/actions/workflows/run_tests.yml
    :alt: Tests Status

Introduction
------------

Generate a GIF of a chess game from a PGN with optional:

* Analysis bar
* Analysis chart
* Numerical Annotation Glyphs (NAGs)
* Move and check arrows
* PGN module to add engine evaluations and calculate ACPL


    **Details on breaking changes in the 1.0.0 release**
    
    This release brings new features such as headers with player names, taken pieces and clocks, and Numeric Annotation Glyphs (NAGs).

    The module was also restructured for easier usage and extensibility. Code using version 0.2.0 and earlier will not work with version 1.0.0 - minor changes will be required to get back up and running again.

    Please see the examples and documentation for details.


Demo
----

GIF with all features enabled
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import chess
    import chess.engine
    import chess.pgn
    import io
    from gifpgn import CreateGifFromPGN, PieceTheme, BoardThemes
    from gifpgn.utils import PGN

    pgn_string = ...
    game = chess.pgn.read_game(io.StringIO(pgn_string))
    if not PGN(game).has_analysis():
        with chess.engine.SimpleEngine.popen_uci("/path/to/stockfish") as engine:
            game = PGN(game).add_analysis(engine, chess.engine.Limit(depth=18))
    g = CreateGifFromPGN(game)
    g.piece_theme = PieceTheme.ALPHA
    g.square_colors = BoardThemes.BLUE
    g.enable_arrows()
    g.add_headers(height=20)
    g.add_analysis_bar()
    g.add_analysis_graph()
    g.enable_nags()
    gif = g.generate("test_gif.gif")



.. image:: https://github.com/prozn/gifpgn/blob/master/docs/images/all_features.gif?raw=true
    :height: 601
    :width: 510


Small GIF with no analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import chess.pgn
    import io
    from from gifpgn import CreateGifFromPGN, PieceTheme, BoardThemes

    pgn_string = ...
    game = chess.pgn.read_game(io.StringIO(pgn_string))
    g = CreateGifFromPGN(game)
    g.board_size = 240
    g.piece_theme = PieceTheme.CASES
    g.square_colors = BoardThemes.GREEN
    g.generate("test_small_gif.gif")



.. image:: https://github.com/prozn/gifpgn/blob/master/docs/images/small_gif.gif?raw=true
    :height: 240
    :width: 240


Piece and Board Themes
^^^^^^^^^^^^^^^^^^^^^^

+---------+------------------------------------------------------------------------------------------------------+
| Alpha   | .. image:: https://github.com/prozn/gifpgn/blob/master/docs/images/alpha.png?raw=true                |
|         |     :height: 60                                                                                      |
| Blue    |     :width: 480                                                                                      |
|         |                                                                                                      |
+---------+------------------------------------------------------------------------------------------------------+
| Cases   | .. image:: https://github.com/prozn/gifpgn/blob/master/docs/images/cases.png?raw=true                |
|         |     :height: 60                                                                                      |
| Green   |     :width: 480                                                                                      |
|         |                                                                                                      |
+---------+------------------------------------------------------------------------------------------------------+
| Maya    | .. image:: https://github.com/prozn/gifpgn/blob/master/docs/images/maya.png?raw=true                 |
|         |     :height: 60                                                                                      |
| Brown   |     :width: 480                                                                                      |
|         |                                                                                                      |
+---------+------------------------------------------------------------------------------------------------------+
| Regular | .. image:: https://github.com/prozn/gifpgn/blob/master/docs/images/regular.png?raw=true              |
|         |     :height: 60                                                                                      |
| Purple  |     :width: 480                                                                                      |
|         |                                                                                                      |
+---------+------------------------------------------------------------------------------------------------------+


Installing
----------

Install with pip:

::

    pip install gifpgn


Documentation
-------------

`View on Read The Docs <https://gifpgn.readthedocs.io/en/latest/>`_


