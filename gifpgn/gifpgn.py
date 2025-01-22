from io import BytesIO
from math import floor
import pkgutil
from datetime import timedelta

import chess
import chess.pgn
import chess.engine
from PIL import Image, ImageDraw, ImageFont

from typing import List, Dict, Tuple, Optional, Literal

from ._t import *
from .geometry import (
    rotate_around_point,
    angle_between_two_points,
    shorten_line,
    line_intersection
)

class CreateGifFromPGN:
    """Creates a GIF of a chess game from a PGN with optional features such as stockfish evaluation, move arrows, 
        and numeric anotation glyphs (blunder, mistake  etc)

    Args:
        pgn (str): PGN as a string or filepath. Filepath requires optional parameter pgn_file=True
        pgn_file_path (bool, optional): Specify whether pgn contains a pgn string [False] or filepath [True]. Defaults to False.
    """
    def __init__(self, game: chess.pgn.Game):
        if game is None:
            raise ValueError("Provided game is not valid/empty")
        
        if game.end().ply() < 1:
            raise ValueError(f"Provided game does not have any moves.")

        self.board_size: int = 480
        self.reverse: bool = False
        self.arrows: bool = False
        self.nag: bool = False
        self.frame_duration: float = 0.5
        self.max_eval: int = 1000

        self._bar_size: Optional[int] = False
        self._graph_size: Optional[int] = False
        self._header_size: Optional[int] = False
        self._square_colors: Dict[chess.Color, str] = {chess.WHITE: '#f0d9b5', chess.BLACK: '#b58863'}
        self._game_root: chess.pgn.Game = game
        self._game: chess.pgn.Game = None
        self._board: chess.Board = self._game_root.board()
        self._start_color: chess.Color = self._game_root.turn
        self._board_image: Optional[Image.Image] = None
        self._images: Dict[str, Image.Image] = {}
        self._square_images: Dict[chess.Color, Image.Image] = {}
        self._pieces: Dict[str, Image.Image] = {}

    @property
    def board_size(self) -> int:
        """(int) Size of the board in pixels. Defaults to 480."""
        return self._board_size

    @board_size.setter
    def board_size(self, bsize: int):
        self._board_size = floor(bsize/8)*8
        self._sq_size = self._board_size // 8
        self._pieces = {}
        self._square_images = {}

    @property
    def square_colors(self) -> Dict[chess.Color, str]:
        return self._square_colors
    
    @square_colors.setter
    def square_colors(self, colors: Tuple[str, str]):
        self._square_colors = {
            chess.WHITE: colors[0],
            chess.BLACK: colors[1]
        }
        self._square_images = {}

    # Optional features

    def add_analysis_bar (self, width: int=30) -> None:
        # PGN needs to be decorated with evaluations for each half move
        if not self.pgn_has_analysis():
            raise ValueError("PGN did not contain evaluations for each half move")
        self._bar_size = width

    def add_analysis_graph(self, height: int=81) -> None:
        # PGN needs to be decorated with evaluations for each half move
        if not self.pgn_has_analysis():
            raise ValueError("PGN did not contain evaluations for each half move")
        self._graph_size = height

    def add_headers(self, height: int=20) -> None:
        self._header_size = height

    # Analysis

    def pgn_has_analysis (self) -> bool:
        game = self._game_root
        while True:
            if game.eval() is None:
                return False
            if game.is_end():
                break
            game = game.next()
        return True
    
    def add_analysis_to_pgn(self, engine: chess.engine.SimpleEngine, engine_limit: chess.engine.Limit) -> None:
        game = self._game_root
        while True:
            info = engine.analyse(game.board(), engine_limit)
            game.set_eval(info['score'], info['depth'])
            if game.is_end():
                break
            game = game.next()

    # Drawing functions

    def _draw_board(self) -> None:
        self._board_image = Image.new('RGBA',(self.board_size,self.board_size))
        self._draw_squares(list(chess.SQUARES))

    def _draw_squares(self, squares: List[chess.Square]) -> None:
        """Draws the listed squares

        Args:
            squares (list): List of ints denoting chess squares
        """
        for square in squares:
            self._draw_square(square)
    
    def _draw_square(self, square: chess.Square) -> None:
        """Draws the specified square

        Args:
            square (int): Int denoting a chess square
        """
        crd = self._get_square_position(square)
        self._board_image.paste(self._get_square_image(self._get_square_color(square)), crd, self._get_square_image(self._get_square_color(square)))
        p = self._board.piece_at(square)
        if p is not None:
            self._board_image.paste(self._get_piece_image(p), crd, self._get_piece_image(p))

    def _draw_arrow(self, from_sqare: chess.Square, to_square: chess.Square, color: Literal["red","green","blue"]="green") -> None:
        """Draw an arrow between two squares

        Args:
            square1 (int): Index of square from
            square2 (int): Index of square to
            color (str, optional): Arrow color: green, blue or red. Defaults to 'green'.
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
        if move_num > self._game_root.end().ply():
            raise Exception()
        x,y = self._get_graph_position(evalu.white(), move_num)
        draw = ImageDraw.Draw(graph_background)
        draw.ellipse([(x-3,y-3),(x+3,y+3)],fill="red")
        return graph_background

    def _draw_eval_bar(self, evalu: chess.engine.Score) -> Image.Image:
        bar_image = Image.new('RGBA', (self._bar_size, self.board_size), "black")
        draw = ImageDraw.Draw(bar_image)
        if self.reverse:
            draw.rectangle([(0, 0),(self._bar_size, self._get_bar_position(evalu))], fill="white")
        else:
            draw.rectangle([(0, self._get_bar_position(evalu)),(self._bar_size, self.board_size)], fill="white")

        if evalu.mate() is None:
            eval_string = '{0:+.{1}f}'.format(round(float(evalu.score())/100,1),1)
        else:
            eval_string = f"M{abs(evalu.mate())}"
        
        if evalu.score(mate_score=self.max_eval) > 0:
            eval_string_color = "black"
            eval_string_pos = 0 if self.reverse else self.board_size
            eval_string_anchor = "ma" if self.reverse else "md"
        else:
            eval_string_color = "white"
            eval_string_pos = self.board_size if self.reverse else 0
            eval_string_anchor = "md" if self.reverse else "ma"

        font = ImageFont.truetype(BytesIO(pkgutil.get_data(__name__, "fonts/Carlito-Regular.ttf")), 10)
        draw.text((self._bar_size/2,eval_string_pos),eval_string,font=font,fill=eval_string_color,anchor=eval_string_anchor)

        return bar_image

    def _draw_headers(self, captures: List[chess.Piece]) -> Dict[chess.Color, Image.Image]:
        """Draw headers and populate with player name, taken pieces, and clock if available"""

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
        """Returns the coordinates of a given square

        Args:
            square (int): Square number in range 0 (a1) to 63 (h8)
            centre (bool, optional): Whether coordinates are top left corner or centre. Defaults to False.

        Returns:
            (int, int): Tuple with x,y coordinate of the top left corner or center of the square
        """
        row = abs(chess.square_rank(square)-(0 if self.reverse else 7))
        column = abs(chess.square_file(square)-(7 if self.reverse else 0))
        x = (column*self._sq_size) + (self._sq_size/2 if center else 0)
        y = (row*self._sq_size) + (self._sq_size/2 if center else 0)
        return (x,y)
    
    def _get_square_color(self, square: chess.Square) -> chess.Color:
        """Returns the color of a given square

        Args:
            square (int): Square number in range 0 (a1) to 63 (h8)

        Returns:
            bool: True if square is white, False if square is black
        """
        return square % 2 != floor(square/8) % 2

    def _get_square_image (self, color: chess.Color) -> Image.Image:
        try:
            return self._square_images[color]
        except KeyError:
            self._square_images[color] = Image.new('RGBA', (self._sq_size, self._sq_size), self._square_colors[color])
            return self._square_images[color]

    def _get_image(self, name: str, size: int) -> Image.Image:
        """Load or return an image from the assets directory

        Args:
            name (str): asset filename
            size (int): size in pixels

        Returns:
            object: PIL image object
        """
        imgname = f"{name}-{size}"
        try:
            return self._images[imgname]
        except KeyError:
            self._images[imgname] = Image.open(BytesIO(pkgutil.get_data(__name__, f"assets/{name}.png"))).resize((size, size)) 
            return self._images[imgname]
    
    def _get_piece_string(self, piece: chess.Piece) -> str:
        p = piece.symbol()
        if p.isupper():
            return "w%s" % p.lower()
        else:
            return "b%s" % p.lower()


    def _get_piece_image(self, piece: str, size: int = 0) -> Image.Image:
        """Loads a piece image or returns a piece image if it has already been loaded

        Args:
            piece (str): single character string denoting a chess piece
            size (int): size in pixels

        Returns:
            object: PIL image object
        """
        size = self._sq_size if size == 0 else size
        piece_string = self._get_piece_string(piece)
        piecename = f"{piece_string}-{size}"
        try:
            return self._pieces[piecename]
        except KeyError:
            self._pieces[piecename] = Image.open(BytesIO(pkgutil.get_data(__name__, f"assets/{piece_string}.png"))).resize((size, size)) 
            return self._pieces[piecename]
        
    def _get_graph_position(self, evalu: chess.engine.Score, move: int) -> tuple:
        """Returns the position of a point on the evaluation graph

        Args:
            evalu (float): Position evaluation
            move (int): Move number

        Returns:
            tuple: Tuple containing x,y coordinates of the graph position
        """
        x = (self._canvas_size()[0]/self._game_root.end().ply())*move
        y = -((evalu.score(mate_score=self.max_eval)-self.max_eval)*(self._graph_size-1))/(2*self.max_eval)
        return (floor(x),floor(y))
    
    def _get_bar_position(self, evalu: chess.engine.Score) -> int:
        max_eval = self.max_eval + 0 if evalu.mate() is None else abs(evalu.mate())
        y = ((evalu.score(mate_score=max_eval)/max_eval)+1)*(self.board_size/2)
        if not self.reverse:
            y = self.board_size - y
        return floor(y)
    
    def _canvas_size(self):
        return (
            self.board_size + (self._bar_size if self._bar_size is not None else 0),
            self.board_size + ((self._header_size if self._header_size is not None else 0)*2) + (self._graph_size if self._graph_size is not None else 0)
        )

    def generate(self, output_file: str):
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
            if self.arrows and self._game.move is not None:
                self._draw_arrow(self._game.move.from_square, self._game.move.to_square, color="blue")
                if self._board.is_check():
                    for sq in self._board.checkers():
                        self._draw_arrow(sq, self._board.king(self._board.turn), color="red")
            if self.nag and self._game.move is not None:
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
                frame.paste(headers[chess.WHITE], (0, 0 if self.reverse else header_size+self._board_size))
                frame.paste(headers[chess.BLACK], (0, header_size + self._board_size if self.reverse else 0))

            frames.append(frame)

            if self._game.is_end():
                break
            self._game = self._game.next()
        
        last_frame = frames[-1].copy()
        for _ in range(20):
            frames.append(last_frame)

        frames[0].save(output_file,
                       format="GIF",
                       append_images=frames[1:],
                       optimize=True,
                       save_all=True,
                       duration=int(self.frame_duration*1000),
                       loop=0)

    def output_image(self, image, name="output.png"): # dump an image for bug testing
        print("Saving image")
        image.save(name, format="PNG")