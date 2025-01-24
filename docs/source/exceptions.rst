Exceptions
==========

Exceptions that can be raised when using this package.

.. code-block:: python
    :caption: Calculate engine analysis if required

    try:
        g.add_analysis_bar()    
    except MissingAnalysisError:
        with chess.engine.SimpleEngine.popen_uci("/path/to/stockfish") as engine:
            g.add_analysis_to_pgn(engine, chess.engine.Limit(depth=18))
        g.add_analysis_bar()


.. automodule:: gifpgn.exceptions
   :members:
   :undoc-members:
   :show-inheritance: