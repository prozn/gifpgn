from io import BytesIO
from math import floor
import pkgutil
from datetime import timedelta

import chess
import chess.pgn
import chess.engine
from PIL import Image, ImageDraw, ImageFont

from typing import List, Dict, Tuple, Optional, Literal

from ._types import *
from .exceptions import (
    MissingAnalysisError,
    MoveOutOfRangeError
)
from .geometry import (
    rotate_around_point,
    angle_between_two_points,
    shorten_line,
    line_intersection
)

class CreateGifFromPGN:
    """Creates a GIF of a chess game from a PGN with optional features such as stockfish evaluation chart, 
    move arrows, and numeric anotation glyphs (blunder, mistake  etc)

    Example
    =======

    .. code-block:: python
        game = chess.pgn.read_game(io.StringIO(pgn_string))
        engine = chess.engine.SimpleEngine.popen_uci("/path/to/stockfish")
        limit = chess.engine.Limit(depth=18)
        g = CreateGifFromPGN(game)
        g.board_size = 560
        g.frame_duration = 0.75
        g.max_eval = 1000
        g.enable_arrows()
        g.add_headers(height=25)
        g.add_analysis_to_pgn(engine, limit)
        g.add_analysis_bar()
        g.add_analysis_graph()
        g.enable_nags()
        g.reverse_board()
        g.generate("output.gif")

    :param chess.pgn.Game game: An instance of :class:`chess.pgn.Game` from the python-chess library.
    """
    def __init__(self, game: chess.pgn.Game):
        if game is None:
            raise ValueError("Provided game is not valid/empty")
        
        if game.end().ply() < 1:
            raise ValueError(f"Provided game does not have any moves.")

        self.board_size: int = 480
        self.square_colors: Dict[chess.Color, str] = {chess.WHITE: '#f0d9b5', chess.BLACK: '#b58863'}
        self.frame_duration: float = 0.5
        self.max_eval: int = 1000

        self._reverse: bool = False
        self._arrows: bool = False
        self._nag: bool = False
        self._bar_size: Optional[int] = False
        self._graph_size: Optional[int] = False
        self._header_size: Optional[int] = False
        self._game_root: chess.pgn.Game = game
        self._game: Optional[chess.pgn.Game] = None
        self._board: chess.Board = self._game_root.board()
        self._start_color: chess.Color = self._game_root.turn
        self._board_image: Optional[Image.Image] = None
        self._images: Dict[str, Image.Image] = {}
        self._square_images: Dict[chess.Color, Image.Image] = {}
        self._pieces: Dict[str, Image.Image] = {}

    @property
    def board_size(self) -> int:
        """int: Size of the board in pixels, defaults to 480
        .. note::
            Size will be rounded down to the nearest multiple of 8
        """
        return self._board_size

    @board_size.setter
    def board_size(self, bsize: int):
        self._board_size = floor(bsize/8)*8
        self._sq_size = self._board_size // 8
        self._pieces = {}
        self._square_images = {}

    @property
    def square_colors(self) -> Dict[chess.Color, str]:       
        """Dict[chess.Color, str]: A dict mapping each `chess.Color` to a color format understandable by PIL"""
        return self._square_colors
    
    @square_colors.setter
    def square_colors(self, colors: Dict[chess.Color, str]):
        self._square_colors = colors
        self._square_images = {}

    @property
    def frame_duration(self) -> float:
        """float: Duration of each frame in seconds, defaults to 0.5"""
        return self._frame_duration
    
    @frame_duration.setter
    def frame_duration(self, frame_duration: float):
        self._frame_duration = frame_duration

    @property
    def max_eval(self) -> int:
        """int: Maximum evaluation displayed on analysis graph or bar, defaults to 1000"""
        return self._max_eval
    
    @max_eval.setter
    def max_eval(self, max_eval: int):
        self._max_eval = max_eval
    

    # Optional features

    def add_analysis_bar (self, width: int=30) -> None:
        """Adds an analysis bar to the right side of the chess board.
        .. note::
            Requires that a PGN has been loaded with ``[%eval ...]`` annotations for
            each half move.
            
            Alternatively the PGN can be decorated using the `add_analysis_to_pgn` method.

        :param int width: Width of the analysis bar in pixels, defaults to 30
        :raises MissingAnalysisError: At least one ply in the PGN has a missing ``[%eval ...]`` annotation
        """
        if not self.pgn_has_analysis():
            raise MissingAnalysisError("PGN did not contain evaluations for each half move")
        self._bar_size = width

    def add_analysis_graph(self, height: int=81) -> None:
        """Adds an analysis graph to the bottom of the chess board.
        .. note::
            Requires that a PGN has been loaded with ``[%eval ...]`` annotations for
            each half move.

            Alternatively the PGN can be decorated using the `add_analysis_to_pgn` method.

        :param int height: Height of the analysis graph in pixels, defaults to 81
        :raises MissingAnalysisError: At least one ply in the PGN has a missing ``[%eval ...]`` annotation
        """
        # PGN needs to be decorated with evaluations for each half move
        if not self.pgn_has_analysis():
            raise MissingAnalysisError("PGN did not contain evaluations for each half move")
        self._graph_size = height

    def enable_nags(self):
        """Enable numerical annoation glyphs
        .. note::
            Requires that a PGN has been loaded with ``[%eval ...]`` annotations for
            each half move.

            Alternatively the PGN can be decorated using the `add_analysis_to_pgn` method.

        :raises MissingAnalysisError: At least one ply in the PGN has a missing ``[%eval ...]`` annotation
        """
        if not self.pgn_has_analysis():
            raise MissingAnalysisError("PGN did not contain evaluations for every half move")
        self._nag = True

    def add_headers(self, height: int=20) -> None:
        """Adds headers with player names, captured pieces, and clock (if PGN contains 
        ``[%clk ...]`` annotations) to the top and bottom of the chess board.

        :param int height: Height of headers in pixels, defaults to 20
        """
        self._header_size = height

    def reverse_board(self):
        """Reverses the board so that black is at the bottom"""
        self._reverse = True

    def enable_arrows(self):
        """Enables move and check arrows"""
        self._arrows = True

    # Analysis

    def pgn_has_analysis (self) -> bool:
        """Checks that every half move in the PGN has ``[%eval ...]`` annotations

        Returns:
            bool: `True` if every half move has ``[%eval ...]`` annotations, `False` otherwise
        """
        game = self._game_root
        while True:
            if game.eval() is None:
                return False
            if game.is_end():
                break
            game = game.next()
        return True
    
    def add_analysis_to_pgn(self, engine: chess.engine.SimpleEngine, engine_limit: chess.engine.Limit) -> None:
        """Calculates and adds ``[%eval ...]`` annotations to each half move in the PGN
        .. code-block:: python
            game = chess.pgn.read_game(io.StringIO(pgn_string))
            engine = chess.engine.SimpleEngine.popen_uci("/path/to/stockfish")
            limit = chess.engine.Limit(depth=18)
            gif = CreateGifFromPGN(game)
            gif.add_analysis_to_pgn(engine, limit)
            ...

        .. warning::
            Engine analysis is a CPU intensive operation, ensure that an appropriate
            limit is applied. 
            
            A depth limit of 18 provides a reasonable trade-off
            between accuracy and compute time.

        :param chess.engine.SimpleEngine engine: Instance of `chess.engine.SimpleEngine 
        <https://python-chess.readthedocs.io/en/latest/engine.html>`_ from python-chess 
        :param chess.engine.Limit engine_limit: Instance of `chess.engine.Limit 
        <https://python-chess.readthedocs.io/en/latest/engine.html#chess.engine.Limit>`_ from python-chess 
        """
        game = self._game_root
        while True:
            info = engine.analyse(game.board(), engine_limit)
            game.set_eval(info['score'], info['depth'])
            if game.is_end():
                break
            game = game.next()

    # Drawing functions

    def _draw_board(self) -> None:
        """Draws the board at the current game state stored in `self._game`"""
        self._board_image = Image.new('RGBA',(self.board_size,self.board_size))
        self._draw_squares(list(chess.SQUARES))

    def _draw_squares(self, squares: List[chess.Square]) -> None:
        """Draws the listed squares

        :param List[chess.Square] squares: List of `chess.Square` types
        """
        for square in squares:
            self._draw_square(square)
    
    def _draw_square(self, square: chess.Square) -> None:
        """Draws the specified square

        :param chess.Square square: 
        """
        crd = self._get_square_position(square)
        self._board_image.paste(self._get_square_image(self._get_square_color(square)), crd, self._get_square_image(self._get_square_color(square)))
        p = self._board.piece_at(square)
        if p is not None:
            self._board_image.paste(self._get_piece_image(p), crd, self._get_piece_image(p))

    def _draw_arrow(self, from_sqare: chess.Square, to_square: chess.Square, color: Literal["red","green","blue"]="green") -> None:
        """Draws an arrow from one square to another square

        :param chess.Square from_sqare:
        :param chess.Square to_square:
        :param string color: Arrow color. Options are "red", "green", or "blue". Defaults to "green"
        """
        arrow_mask = Image.new('RGBA', self._board_image.size)
        arrow = {
            'green': (0, 255, 0, 100),
            'blue':  (0, 0, 255, 100),
            'red':   (255, 0, 0, 100)
        }
        from_crd = self._get_square_position(from_sqare, center=True)
        to_crd = self._get_square_position(to_square, center=True)
        draw = ImageDraw.Draw(arrow_mask)
        # draw arrow line
        draw.line(shorten_line(from_crd, to_crd, self._sq_size/2), fill=arrow[color], width=floor(self._sq_size/4))
        
        # draw arrow head
        line_degrees = angle_between_two_points(Coord(from_crd), Coord(to_crd))
        x0, y0 = from_crd
        x1, y1 = to_crd
        c1 = to_crd
        c2 = rotate_around_point(Coord((x1-self._sq_size/2, y1-self._sq_size/3)), line_degrees, Coord(c1))
        c3 = rotate_around_point(Coord((x1-self._sq_size/2, y1+self._sq_size/3)), line_degrees, Coord(c1))
        draw.polygon([c1, c2, c3], fill=arrow[color])

        self._board_image = Image.alpha_composite(self._board_image, arrow_mask)

    def _draw_nag(self) -> None:
        """Draws a blunder, mistake or inaccuracy nag, if applicable, to the move
        that lead to the current `self._game` ply"""
        if self._game.move is None:
            return
        prev =  self._game.parent.eval().relative.wdl(model="sf", ply=self._game.parent.ply())
        curr = self._game.eval().pov(not self._game.eval().turn).wdl(model="sf", ply=self._game.ply())
        change = curr.expectation() - prev.expectation()

        nag = None
        if change < -0.3: nag = "blunder"
        elif change < -0.2: nag = "mistake"
        elif change < -0.1: nag = "inaccuracy"

        x,y = self._get_square_position(self._game.move.to_square)
        x += int(self._sq_size*(0.75 if x < self._sq_size*7 else 0.5))
        y -= int(self._sq_size*(0.25 if y > 0 else 0))

        if nag is not None:
            nag_icon = self._get_image(nag, int(self._sq_size/2))
            self._board_image.paste(nag_icon,(x,y),nag_icon)


    def _draw_graph_background(self) -> Image.Image:
        """Iterates through the game in `self._game_root` and draws a the analysis graph

        :return Image.Image: PIL Image object containing the graph
        """
        points = []
        graph_image = Image.new('RGBA', (self.board_size + (self._bar_size if self._bar_size is not None else 0), self._graph_size), 'black')
        draw = ImageDraw.Draw(graph_image)
        game = self._game_root
        while True:
            move_num = game.ply()
            evalu = game.eval().white().score(mate_score=self.max_eval)
            prev_evalu = 0 if move_num == 0 else game.parent.eval().white().score(mate_score=self.max_eval)
            points.append(self._get_graph_position(game.eval().white(),move_num))
            if move_num > 0:
                zprev = self._get_graph_position(chess.engine.Cp(0),move_num-1)
                znew = self._get_graph_position(chess.engine.Cp(0),move_num)
                if evalu * prev_evalu < 0: # eval symbols different => crossing the zero line
                    zinter = line_intersection((points[move_num-1],points[move_num]),(zprev,znew))
                    draw.polygon([zprev,points[move_num-1],zinter],fill="#514f4c" if prev_evalu < 0 else "#7f7e7c")
                    draw.polygon([zinter,points[move_num],znew],fill="#514f4c" if evalu < 0 else "#7f7e7c")
                else:
                    if evalu == 0:
                        fill_color = "#514f4c" if prev_evalu < 0 else "#7f7e7c"
                    else:
                        fill_color = "#514f4c" if evalu < 0 else "#7f7e7c"
                    draw.polygon([zprev,points[move_num-1],points[move_num],znew],fill=fill_color)
            if game.is_end():
                break
            game = game.next()
        draw.line(points,fill='white',width=1)
        x_axis_f = self._get_graph_position(chess.engine.Cp(0), 0)
        x_axis_t = self._get_graph_position(chess.engine.Cp(0), self._game_root.end().ply())
        draw.line([x_axis_f, x_axis_t], fill="grey", width=1)
        return graph_image

    def _draw_graph_point(self, graph_background: Image.Image, evalu: chess.engine.PovScore, move_num: int) -> Image.Image:
        """Draws a red dot on the provided graph image at the provided evaluation and move number

        :param Image.Image graph_background: A PIL Image object containing an evaluation graph
        :param chess.engine.PovScore evalu:
        :param int move_num: 
        :raises MoveOutOfRangeError: Requested move was larger than game length
        :return Image.Image: PIL Image object containing the provided image with red dot added
        """
        if move_num > self._game_root.end().ply():
            raise MoveOutOfRangeError(move_num, self._game_root.end().ply())
        x,y = self._get_graph_position(evalu.white(), move_num)
        draw = ImageDraw.Draw(graph_background)
        draw.ellipse([(x-3,y-3),(x+3,y+3)],fill="red")
        return graph_background

    def _draw_eval_bar(self, evalu: chess.engine.Score) -> Image.Image:
        """Draws the evaluation bar for the provided evalation

        :param chess.engine.Score evalu:
        :return Image.Image: PIL Image object containing an evaluation bar
        """
        bar_image = Image.new('RGBA', (self._bar_size, self.board_size), "black")
        draw = ImageDraw.Draw(bar_image)
        if self._reverse:
            draw.rectangle([(0, 0),(self._bar_size, self._get_bar_position(evalu))], fill="white")
        else:
            draw.rectangle([(0, self._get_bar_position(evalu)),(self._bar_size, self.board_size)], fill="white")

        if evalu.mate() is None:
            eval_string = '{0:+.{1}f}'.format(round(float(evalu.score())/100,1),1)
        else:
            eval_string = f"M{abs(evalu.mate())}"
        
        if evalu.score(mate_score=self.max_eval) > 0:
            eval_string_color = "black"
            eval_string_pos = 0 if self._reverse else self.board_size
            eval_string_anchor = "ma" if self._reverse else "md"
        else:
            eval_string_color = "white"
            eval_string_pos = self.board_size if self._reverse else 0
            eval_string_anchor = "md" if self._reverse else "ma"

        font = ImageFont.truetype(BytesIO(pkgutil.get_data(__name__, "fonts/Carlito-Regular.ttf")), 10)
        draw.text((self._bar_size/2,eval_string_pos),eval_string,font=font,fill=eval_string_color,anchor=eval_string_anchor)

        return bar_image

    def _draw_headers(self, captures: List[chess.Piece]) -> Dict[chess.Color, Image.Image]:
        """Draw headers and populate with player name, captured pieces, and clock if available

        :param List[chess.Piece] captures: List of captured pieces
        :return Dict[chess.Color, Image.Image]: A Dict containing a header image for each color
        """
        header_width = self._canvas_size()[0]
        font = ImageFont.truetype(BytesIO(pkgutil.get_data(__name__, "fonts/Carlito-Regular.ttf")), int(self._header_size*0.7))

        clock = {
            not self._game.turn(): self._game.clock(),
            self._game.turn(): None if self._game.move is None else self._game.parent.clock()
        }

        whitebar = Image.new('RGBA',(header_width,self._header_size),"white")
        draw = ImageDraw.Draw(whitebar)
        draw.text((3,self._header_size/2),self._game_root.headers['White'],font=font,fill="black",anchor="lm")
        if clock[chess.WHITE] is not None:
            draw.text((header_width-3,self._header_size/2),str(timedelta(seconds=round(clock[chess.WHITE]))),font=font,fill="black",anchor="rm")

        blackbar = Image.new('RGBA',(header_width,self._header_size),"black")
        draw = ImageDraw.Draw(blackbar)
        draw.text((3,self._header_size/2),self._game_root.headers['Black'],font=font,fill="white",anchor="lm")
        if clock[chess.BLACK] is not None:
            draw.text((header_width-3,self._header_size/2),str(timedelta(seconds=round(clock[chess.BLACK]))),font=font,fill="white",anchor="rm")

        piece_size = self._header_size-2
        piece_offset = int(max(draw.textlength(self._game_root.headers['White'], font), draw.textlength(self._game_root.headers['Black'], font))) + self._header_size
        num_takes = {chess.WHITE: 0, chess.BLACK: 0}
        for piece in captures:
            if piece.color == chess.WHITE:
                blackbar.paste(self._get_piece_image(piece, piece_size), (piece_offset+(piece_size*num_takes[chess.WHITE]),1), self._get_piece_image(piece, piece_size))
            else:
                whitebar.paste(self._get_piece_image(piece, piece_size), (piece_offset+(piece_size*num_takes[chess.BLACK]),1), self._get_piece_image(piece, piece_size))
            num_takes[piece.color] += 1

        return {
            chess.WHITE: whitebar,
            chess.BLACK: blackbar
        }
    
    # Helper Functions

    def _get_square_position(self, square: chess.Square, center: bool=False) -> Coord:
        """Calculates the position of either the top left of center of the specified square
        taking into account whether the board is reversed by `self._reverse`

        :param chess.Square square:
        :param bool center: If true the center of the square will be calculated, otherwise top left, defaults to False
        :return Coord: Coordinates of the given square
        """
        row = abs(chess.square_rank(square)-(0 if self._reverse else 7))
        column = abs(chess.square_file(square)-(7 if self._reverse else 0))
        x = (column*self._sq_size) + (self._sq_size/2 if center else 0)
        y = (row*self._sq_size) + (self._sq_size/2 if center else 0)
        return (x,y)
    
    def _get_square_color(self, square: chess.Square) -> chess.Color:
        """Returns the color of the given square

        :param chess.Square square: 
        :return chess.Color: 
        """
        return square % 2 != floor(square/8) % 2

    def _get_square_image (self, color: chess.Color) -> Image.Image:
        """Retrieves or creates a square image of the given color, sized for the current
        value of `self.board_size`

        :param chess.Color color: 
        :return Image.Image: PIL Image object containing an image of the given square color
        """
        try:
            return self._square_images[color]
        except KeyError:
            self._square_images[color] = Image.new('RGBA', (self._sq_size, self._sq_size), self.square_colors[color])
            return self._square_images[color]

    def _get_image(self, name: str, size: int) -> Image.Image:
        """Return from the cache or retreive from assets directory the provided image, resized
        to the given size

        :param str name: filename
        :param int size: size in pixels to resize the image to
        :return Image.Image: PIL Image object containing the resized image
        """
        imgname = f"{name}-{size}"
        try:
            return self._images[imgname]
        except KeyError:
            self._images[imgname] = Image.open(BytesIO(pkgutil.get_data(__name__, f"assets/{name}.png"))).resize((size, size)) 
            return self._images[imgname]
    
    def _get_piece_string(self, piece: chess.Piece) -> str:
        """Returns the filename of the given piece

        :param chess.Piece piece:
        :return str:
        """
        p = piece.symbol()
        if p.isupper():
            return "w%s" % p.lower()
        else:
            return "b%s" % p.lower()

    def _get_piece_image(self, piece: str, size: int = 0) -> Image.Image:
        """Return from the cache or retreive from assets directory the provided piece image,
        resized to the given size

        :param str piece:
        :param int size:
        :return Image.Image: PIL Image object containing the resized piece image
        """
        size = self._sq_size if size == 0 else size
        piece_string = self._get_piece_string(piece)
        piecename = f"{piece_string}-{size}"
        try:
            return self._pieces[piecename]
        except KeyError:
            self._pieces[piecename] = Image.open(BytesIO(pkgutil.get_data(__name__, f"assets/{piece_string}.png"))).resize((size, size)) 
            return self._pieces[piecename]
        
    def _get_graph_position(self, evalu: chess.engine.Score, move: int) -> Coord:
        """Returns the position of a given evluation and move number on the evaluation graph

        :param chess.engine.Score evalu:
        :param int move:
        :return Coord: Coordinates on the evaluation graph
        """
        x = (self._canvas_size()[0]/self._game_root.end().ply())*move
        y = -((evalu.score(mate_score=self.max_eval)-self.max_eval)*(self._graph_size-1))/(2*self.max_eval)
        return (floor(x),floor(y))
    
    def _get_bar_position(self, evalu: chess.engine.Score) -> int:
        """Returns the y coordinate on the evaluation bar for a given evaluation

        :param chess.engine.Score evalu:
        :return int: 
        """
        max_eval = self.max_eval + 0 if evalu.mate() is None else abs(evalu.mate())
        y = ((evalu.score(mate_score=max_eval)/max_eval)+1)*(self.board_size/2)
        if not self._reverse:
            y = self.board_size - y
        return floor(y)
    
    def _canvas_size(self) -> Tuple[int,int]:
        """Calculates the size of the GIF canvas

        :return Tuple[int,int]: 
        """
        return (
            self.board_size + (self._bar_size if self._bar_size is not None else 0),
            self.board_size + ((self._header_size if self._header_size is not None else 0)*2) + (self._graph_size if self._graph_size is not None else 0)
        )

    def generate(self, output_file: Optional[str]=None) -> Optional[BytesIO]:
        """Generate the GIF and either save it to the specified file path or return the
        raw bytes if no file path is specified.

        .. code-block:: python
            game = chess.pgn.read_game(io.StringIO(pgn_string))
            engine = chess.engine.SimpleEngine.popen_uci("/path/to/stockfish")
            limit = chess.engine.Limit(depth=18)
            gif = CreateGifFromPGN(game)
            gif.add_analysis_to_pgn(engine, limit)

            ...

        :param Optional[str] output_file: Filepath to save to, defaults to None
        :return Optional[BytesIO]: Raw bytes of the generated GIF if `output_file` parameter is set, else returns `None`
        """
        captures: List[chess.Piece] = []
        frames: List[Image.Image] = []

        bar_size = self._bar_size if self._bar_size is not None else 0
        graph_size = self._graph_size if self._graph_size is not None else 0
        header_size = self._header_size if self._header_size is not None else 0

        blank_canvas = Image.new('RGBA', self._canvas_size(),"red")

        if self._graph_size is not None:
            graph_background = self._draw_graph_background()

        self._game = self._game_root
        while True:
            frame = blank_canvas.copy()
            self._board = self._game.board()

            self._draw_board()
            if self._game.move is not None and self._game.parent.board().is_capture(self._game.move):
                if self._game.parent.board().is_en_passant(self._game.move):
                    captures.append(chess.Piece(chess.PAWN, self._board.turn))
                else:
                    captures.append(self._game.parent.board().piece_at(self._game.move.to_square))
            if self._arrows and self._game.move is not None:
                self._draw_arrow(self._game.move.from_square, self._game.move.to_square, color="blue")
                if self._board.is_check():
                    for sq in self._board.checkers():
                        self._draw_arrow(sq, self._board.king(self._board.turn), color="red")
            if self._nag and self._game.move is not None:
                self._draw_nag()
            frame.paste(self._board_image, (0, header_size))

            if self._bar_size is not None:
                bar = self._draw_eval_bar(self._game.eval().white())
                frame.paste(bar, (self.board_size,header_size))
            if self._graph_size is not None:
                graph = graph_background.copy()
                self._draw_graph_point(graph, self._game.eval(), self._game.ply())
                frame.paste(graph, (0, self._canvas_size()[1]-graph_size))
            if self._header_size is not None:
                headers = self._draw_headers(captures)
                frame.paste(headers[chess.WHITE], (0, 0 if self._reverse else header_size+self.board_size))
                frame.paste(headers[chess.BLACK], (0, header_size + self.board_size if self._reverse else 0))

            frames.append(frame)

            if self._game.is_end():
                break
            self._game = self._game.next()
        
        last_frame = frames[-1].copy()
        for _ in range(20):
            frames.append(last_frame)

        if output_file is None:
            target = BytesIO()
        else:
            target = output_file
        
        frames[0].save(target,
                    format="GIF",
                    append_images=frames[1:],
                    optimize=True,
                    save_all=True,
                    duration=int(self.frame_duration*1000),
                    loop=0)
        
        if output_file is None:
            target.seek(0)
            return target

    def output_image(self, image, name="output.png"): # dump an image for bug testing
        print("Saving image")
        image.save(name, format="PNG")