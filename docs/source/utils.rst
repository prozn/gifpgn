Utilities
=========

Provides functionality to:

* Check whether a PGN has ``[%eval ...]`` tags for every half move
* Generate analysis and decorate a PGN with ``[%eval ...]`` tags


.. code-block:: python

   game = chess.pgn.read_game(io.StringIO(pgn_string))

   # If analysis is not present, add it
   if not PGN(game).has_analysis():
         with chess.engine.SimpleEngine.popen_uci("/path/to/stockfish") as engine:
            game = PGN(game).add_analysis(engine, chess.engine.Limit(depth=18))
            
   # Optionally store the new PGN to avoid having to generate analysis again
   pgn_with_analysis = game.export()
   with open("analysis.pgn", "w") as text_file:
      text_file.write(pgn_with_analysis)


.. warning::
   Engine analysis is a CPU intensive operation, ensure that an appropriate limit is applied.

   A depth limit of 18 provides a reasonable trade-off between accuracy and compute time.

.. note::
   Once you have finished with the ``chess.engine.SimpleEngine`` instance it should be
   closed using the ``close()`` method, or alternatively use a with statement.
   Otherwise your program will not exit as expected.


.. automodule:: gifpgn.utils
   :members:
   :undoc-members:
   :show-inheritance: