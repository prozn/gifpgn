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
    :alt: Coverage Status

Introduction
------------

Generate a GIF of a chess game from a PGN with optional:

* Analysis bar
* Analysis chart
* Numerical Annotation Glyphs (NAGs)
* Move and check arrows

Demo
----

GIF with all features enabled
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import chess
    import chess.engine
    import chess.pgn
    import io
    from gifpgn import CreateGifFromPGN
    from gifpgn.utils import PGN

    pgn_string = ...
    game = chess.pgn.read_game(io.StringIO(pgn_string))
    if not PGN(game).has_analysis():
        with chess.engine.SimpleEngine.popen_uci("/path/to/stockfish") as engine:
            game = PGN(game).add_analysis(engine, chess.engine.Limit(depth=18))
    g = CreateGifFromPGN(game)
    g.enable_arrows()
    g.add_headers(height=20)
    g.add_analysis_bar()
    g.add_analysis_graph()
    g.enable_nags()
    gif = g.generate("test_gif.gif")


.. image:: https://i.imgur.com/hxQM0cl.gif


Small GIF with no analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import chess.pgn
    import io
    from from gifpgn import CreateGifFromPGN

    pgn_string = ...
    game = chess.pgn.read_game(io.StringIO(pgn_string))
    g = CreateGifFromPGN(game)
    g.board_size = 240
    g.generate("test_small_gif.gif")


.. image:: https://i.imgur.com/HkT2K8k.gif

Installing
----------

Install with pip:

::

    pip install gifpgn


Documentation
-------------

`View on Read The Docs <https://gifpgn.readthedocs.io/en/latest/>`_


