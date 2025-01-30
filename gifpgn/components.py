from io import BytesIO
from math import floor
from importlib.resources import files
from datetime import timedelta

from typing import List, Dict, Tuple, Optional, Literal

import chess
import chess.pgn
import chess.engine
from PIL import Image, ImageDraw, ImageFont

from ._types import Coord, PieceTheme, BoardTheme
from .exceptions import (
    MoveOutOfRangeError
)
from .geometry import (
    rotate_around_point,
    angle_between_two_points,
    shorten_line,
    line_intersection
)
from .utils import _eval, _font_size_approx


class _Component():
    def __init__(self):
        self._canvas: Image.Image

    def image(self) -> Image.Image:
        return self._canvas


class _Canvas(_Component):
    """Stitches the components together into a final frame

    :param int board: Board size in pixels
    :param Optional[int] analysis_bar: Analysis bar width in pixels
    :param Optional[int] analysis_graph: Graph height in pixels
    :param Optional[int] headers: Header heights in pixels
    :param bool reverse: White at the top if True, at the bottom if False
    """
    def __init__(self, board: int, analysis_bar: Optional[int], analysis_graph: Optional[int],
                 headers: Optional[int], reverse: bool):
        self.board_size: int = board
        self.bar_size: int = 0 if analysis_bar is None else analysis_bar
        self.graph_size: int = 0 if analysis_graph is None else analysis_graph
        self.header_size: int = 0 if headers is None else headers
        self.reverse = reverse
        self._canvas = Image.new('RGBA', self.size(), "red")

    def size(self) -> Tuple[int, int]:
        """Calculates the full canvas size

        :return Tuple[int, int]: x,y tuple
        """
        return (
            self.board_size + self.bar_size,
            self.board_size + self.graph_size + (self.header_size*2)
        )

    def add_board(self, board: Image.Image) -> None:
        self._canvas.paste(board, (0, self.header_size))

    def add_headers(self, white: Image.Image, black: Image.Image) -> None:
        self._canvas.paste(white, (0, 0 if self.reverse else self.header_size + self.board_size), white)
        self._canvas.paste(black, (0, self.header_size + self.board_size if self.reverse else 0), black)

    def add_bar(self, bar: Image.Image) -> None:
        self._canvas.paste(bar, (self.board_size, self.header_size))

    def add_graph(self, graph: Image.Image) -> None:
        self._canvas.paste(graph, (0, self.size()[1]-self.graph_size))


class _AssetImage:
    """Loads an image from the assets directory or the cache

    :param str name: filename
    :param int size: size in pixels to resize the image to
    """
    _images: Dict[str, Image.Image] = {}

    def __init__(self, name: str, size: int):
        self._name = name
        self._size = size

    def image(self) -> Image.Image:
        """Returns the loaded image

        :return Image.Image: PIL Image object containing the loaded image
        """
        imgname = f"{self._name}-{self._size}"
        try:
            return self._images[imgname]
        except KeyError:
            asset = files('gifpgn.assets').joinpath(f"{self._name}.png").read_bytes()
            img = Image.open(BytesIO(asset))
            self._images[imgname] = img.convert("RGBA").resize((self._size, self._size))
            return self._images[imgname]


class _Piece(_AssetImage):
    """Extends ``_AssetImage`` to convert a ``chess.Piece`` to the corresponding filename
    in the assets directory

    :param chess.Piece piece:
    :param int size: size in pixels to resize the image to
    :param Piecetheme theme: Instance of gifpgn.PieceTheme
    """
    def __init__(self, piece: chess.Piece, size: int, theme: PieceTheme = PieceTheme.ALPHA):
        name = f"pieces/{theme.value}/{self.get_piece_string(piece)}"
        super().__init__(name, size)

    def get_piece_string(self, piece: chess.Piece) -> str:
        """Returns the filename of the given piece

        :param chess.Piece piece:
        :return str:
        """
        p = piece.symbol()
        if p.isupper():
            return "w%s" % p.lower()
        else:
            return "b%s" % p.lower()


class _Board(_Component):
    """Generate an image of a given board position

    :param int size: Size of the board image in pixels
    :param chess.Board board: A board state
    :param bool reverse: Draws the board from the perspective of black if True, defaults to False
    :param BoardTheme square_colors: Colors of the white and black squares, instance of gifpgn.BoardTheme
    :param PieceTheme piece_theme: The piece theme to use, instance of gifpgn.PieceTheme
    """
    def __init__(self,
                 size: int,
                 board: chess.Board,
                 reverse: bool = False,
                 square_colors: Optional[BoardTheme] = None,
                 piece_theme: PieceTheme = PieceTheme.ALPHA):
        super().__init__()
        self.board_size = size
        self.reverse: bool = reverse
        if square_colors is None:
            self.square_colors = BoardTheme()
        elif isinstance(square_colors, BoardTheme):
            self.square_colors = square_colors
        else:
            raise ValueError(f"square_colors should be an instance of Boardtheme. Provided: {square_colors}")

        self._piece_theme = piece_theme
        self._pieces: Dict[str, Image.Image] = {}
        self._square_images: Dict[chess.Color, Image.Image] = {}
        self._images: Dict[str, Image.Image] = {}

        self._sq_size: int

        self.board = board  # triggers setter

    @property
    def board_size(self) -> int:
        """Size of the board in pixels"""
        return self._board_size

    @board_size.setter
    def board_size(self, bsize: int):
        self._board_size = floor(bsize/8)*8
        self._sq_size = self._board_size // 8
        self._pieces = {}
        self._square_images = {}

    @property
    def square_colors(self) -> BoardTheme:
        return self._square_colors

    @square_colors.setter
    def square_colors(self, colors) -> None:
        if isinstance(colors, BoardTheme):
            self._square_colors = colors
            self._square_images = {}
        else:
            raise ValueError(f"Colors should be an instance of BoardTheme. Provided: {type(colors)}")

    @property
    def board(self) -> chess.Board:
        return self._board

    @board.setter
    def board(self, board) -> None:
        self._board = board
        self.draw_board()

    def draw_board(self) -> None:
        "Draws the full board"
        self._canvas = Image.new('RGBA', (self.board_size, self.board_size))
        self.draw_squares(list(chess.SQUARES))

    def draw_squares(self, squares: Optional[List[chess.Square]] = None) -> None:
        "Draws the listed squares"
        if squares is None:
            squares = list(chess.SQUARES)
        for square in squares:
            self.draw_square(square)

    def draw_square(self, square: chess.Square) -> None:
        "Draws a single square"
        crd = self.get_square_position(square)
        self._canvas.paste(self.get_square_image(square), crd, self.get_square_image(square))
        p = self.board.piece_at(square)
        # _Piece(p, self._sq_size, self._piece_theme).image().save("test_piece.png", "png")
        if p is not None:
            self._canvas.paste(
                _Piece(p, self._sq_size, self._piece_theme).image(), crd, _Piece(p, self._sq_size, self._piece_theme).image()
            )

    def get_square_position(self, square: chess.Square, center: bool = False) -> Coord:
        """Calculates the position of either the top left of center of the specified square
        taking into account whether the board is reversed

        :param chess.Square square:
        :param bool center: If true the center of the square will be calculated, otherwise top left, defaults to False
        :return Coord: Coordinates of the given square
        """
        row = abs(chess.square_rank(square)-(0 if self.reverse else 7))
        column = abs(chess.square_file(square)-(7 if self.reverse else 0))
        x = int((column*self._sq_size) + (self._sq_size/2 if center else 0))
        y = int((row*self._sq_size) + (self._sq_size/2 if center else 0))
        return Coord(x, y)

    def get_square_color(self, square: chess.Square) -> chess.Color:
        """Returns the color of the given square

        :param chess.Square square:
        :return chess.Color:
        """
        return square % 2 != floor(square/8) % 2

    def get_square_image(self, square: chess.Square) -> Image.Image:
        """Retrieves or creates a square image of the given color

        :param chess.Square square:
        :return Image.Image: PIL Image object containing an image of the given square color
        """
        color = self.get_square_color(square)
        try:
            return self._square_images[color]
        except KeyError:
            self._square_images[color] = \
                Image.new('RGBA', (self._sq_size, self._sq_size), self.square_colors.square_color(color))
            return self._square_images[color]

    def draw_arrow(self, from_sqare: chess.Square, to_square: chess.Square,
                   color: Literal["red", "green", "blue"] = "green") -> None:
        """Draws an arrow from one square to another square

        :param chess.Square from_sqare:
        :param chess.Square to_square:
        :param str color: Arrow color. Options are "red", "green", or "blue". Defaults to "green"
        """
        arrow_mask = Image.new('RGBA', self._canvas.size)
        arrow = {
            'green': (0, 255, 0, 100),
            'blue':  (0, 0, 255, 100),
            'red':   (255, 0, 0, 100)
        }
        from_crd = self.get_square_position(from_sqare, center=True)
        to_crd = self.get_square_position(to_square, center=True)
        draw = ImageDraw.Draw(arrow_mask)
        # draw arrow line
        draw.line(shorten_line(from_crd, to_crd, int(self._sq_size/2)), fill=arrow[color], width=floor(self._sq_size/4))

        # draw arrow head
        line_degrees = angle_between_two_points(Coord(*from_crd), Coord(*to_crd))
        x0, y0 = from_crd
        x1, y1 = to_crd
        c1 = to_crd
        c2 = rotate_around_point(Coord(int(x1-self._sq_size/2), int(y1-self._sq_size/3)), line_degrees, Coord(*c1))
        c3 = rotate_around_point(Coord(int(x1-self._sq_size/2), int(y1+self._sq_size/3)), line_degrees, Coord(*c1))
        draw.polygon([c1, c2, c3], fill=arrow[color])

        self._canvas = Image.alpha_composite(self._canvas, arrow_mask)

    def draw_nag(self, nag: Literal["blunder", "mistake", "inaccuracy"], square: chess.Square) -> None:
        """Draws a blunder, mistake or inaccuracy NAG at the specified square

        :param str nag: NAG to draw. Options are "blunder", "mistake", or "inaccuracy"
        :param chess.Square square: The square to draw the NAG
        """
        x, y = self.get_square_position(square)
        x += int(self._sq_size*(0.75 if x < self._sq_size*7 else 0.5))
        y -= int(self._sq_size*(0.25 if y > 0 else 0))

        nag_icon = _AssetImage(f"nags/{nag}", int(self._sq_size/2)).image()
        self._canvas.paste(nag_icon, (x, y), nag_icon)


class _Headers():
    def __init__(self, game: chess.pgn.Game, captures: List[chess.Piece], size: Tuple[int, int]):
        """Draw headers and populate with player name, captured pieces, and clock if available

        :param chess.pgn.Game game: Game object containing player name headers
        :param List[chess.Piece] captures: List of pieces to display in the headers
        :param Tuple[int, int] size: x,y size of the headers in pixels
        """
        self._game = game
        self._game_root = game.game()
        self._width, self._height = size
        self._headers = self._draw_headers(captures)

    def _draw_headers(self, captures: List[chess.Piece]) -> Dict[chess.Color, Image.Image]:
        font = ImageFont.truetype(
            BytesIO(files("gifpgn.fonts").joinpath("Carlito-Regular.ttf").read_bytes()),
            int(self._height*0.7)
        )

        clock = {
            not self._game.turn(): self._game.clock(),
            self._game.turn(): None if self._game.move is None else self._game.parent.clock()
        }

        whitebar = Image.new('RGBA', (self._width, self._height), "white")
        draw = ImageDraw.Draw(whitebar)
        draw.text((3, self._height/2), self._game_root.headers['White'], font=font, fill="black", anchor="lm")
        if clock[chess.WHITE] is not None:
            draw.text(
                (self._width-3, self._height/2),
                str(timedelta(seconds=round(clock[chess.WHITE]))),
                font=font, fill="black", anchor="rm"
            )

        blackbar = Image.new('RGBA', (self._width, self._height), "black")
        draw = ImageDraw.Draw(blackbar)
        draw.text((3, self._height/2), self._game_root.headers['Black'], font=font, fill="white", anchor="lm")
        if clock[chess.BLACK] is not None:
            draw.text(
                (self._width-3, self._height/2),
                str(timedelta(seconds=round(clock[chess.BLACK]))),
                font=font, fill="white", anchor="rm"
            )

        piece_size = self._height-2
        piece_offset = int(max(
            draw.textlength(self._game_root.headers['White'], font),
            draw.textlength(self._game_root.headers['Black'], font)
            )) + self._height
        num_takes = {chess.WHITE: 0, chess.BLACK: 0}
        for piece in captures:
            alpha_img = Image.new('RGBA', (self._width, self._height))
            if piece.color == chess.WHITE:
                alpha_img.paste(
                    _Piece(piece, piece_size).image(),
                    (piece_offset+(piece_size*num_takes[chess.WHITE]), 1),
                    _Piece(piece, piece_size).image()
                )
                blackbar = Image.alpha_composite(blackbar, alpha_img)
            else:
                alpha_img.paste(
                    _Piece(piece, piece_size).image(),
                    (piece_offset+(piece_size*num_takes[chess.BLACK]), 1),
                    _Piece(piece, piece_size).image()
                )
                whitebar = Image.alpha_composite(whitebar, alpha_img)
            num_takes[piece.color] += 1

        return {
            chess.WHITE: whitebar,
            chess.BLACK: blackbar
        }

    def image(self, color: chess.Color) -> Image.Image:
        """Returns the header for the given ``chess.Color``

        :param chess.Color color:
        :return Image.Image:
        """
        return self._headers[color]


class _EvalBar(_Component):
    def __init__(self, size: Tuple[int, int], evalu: chess.engine.Score, max_eval: int, reverse: bool):
        """Draws the evaluation bar for the provided evalation

        :param Tuple[int, int] size: x,y size of the evaluation bar
        :param chess.engine.Score evalu: The evaluation to be displayed on the bar
        :param int max_eval: The range in centipawns to display on the analysis bar. Larger evaluations will be truncated.
        :param bool reverse: If True bar will be drawn from black's perspective
        """
        super().__init__()
        self._width, self._height = size
        self._reverse = reverse
        self._max_eval = max_eval
        self._draw_eval_bar(evalu)

    def _draw_eval_bar(self, evalu: chess.engine.Score) -> None:
        self._canvas = Image.new('RGBA', (self._width, self._height), "black")
        draw = ImageDraw.Draw(self._canvas)
        if self._reverse:
            draw.rectangle([(0, 0), (self._width, self._get_bar_position(evalu))], fill="white")
        else:
            draw.rectangle([(0, self._get_bar_position(evalu)), (self._width, self._height)], fill="white")

        if evalu.mate() is None:
            eval_string = '{0:+.{1}f}'.format(round(float(evalu.score())/100, 1), 1)
        else:
            eval_string = f"M{abs(evalu.mate())}"

        if evalu.score(mate_score=self._max_eval) > 0:
            eval_string_color = "black"
            eval_string_pos = 0 if self._reverse else self._height
            eval_string_anchor = "ma" if self._reverse else "md"
        else:
            eval_string_color = "white"
            eval_string_pos = self._height if self._reverse else 0
            eval_string_anchor = "md" if self._reverse else "ma"

        font = files("gifpgn.fonts").joinpath("Carlito-Regular.ttf").read_bytes()
        font = ImageFont.truetype(BytesIO(font), _font_size_approx(eval_string, font, self._width, 0.75, 10))
        draw.text((self._width/2, eval_string_pos), eval_string, font=font, fill=eval_string_color, anchor=eval_string_anchor)

    def _get_bar_position(self, evalu: chess.engine.Score) -> int:
        """Returns the y coordinate on the evaluation bar for a given evaluation

        :param chess.engine.Score evalu:
        :return int:
        """
        max_eval = self._max_eval + (0 if evalu.mate() is None else abs(evalu.mate()))
        y = ((evalu.score(mate_score=max_eval)/max_eval)+1)*(self._height/2)
        if not self._reverse:
            y = self._height - y
        return floor(y)


class _Graph:
    """Draws the evaluation graph. The full graph is drawn when initialized and stored.

    Calls to ``at_move()`` return a copy of the graph with a red dot drawn at the specified move.

    :param chess.pgn.Game game: Game object containing an ``[%eval ...]`` annotated PGN
    :param Tuple[int, int] size: x,y size of the graph
    :param int max_eval: Limits the y axis to +/- the given number of centipawns
    :param int line_width: Width of graph line (and x axis line) in pixels, defaults to 1
    """
    def __init__(self, game: chess.pgn.Game, size: Tuple[int, int], max_eval: int, line_width: int = 1):
        self._game_root = game.game()
        self._aa_factor = 4  # scale the graph by this factor, and scale back down in at_move to anti-alias
        self._output_size = size
        self._width, self._height = (size[0] * self._aa_factor, size[1] * self._aa_factor)
        self._line_width: int = line_width * self._aa_factor
        self._max_eval: int = max_eval
        self._eval_at_move: Dict[int, chess.engine.Score] = {}
        self._background: Image.Image = self._draw_graph_background()

    def _draw_graph_background(self) -> Image.Image:
        """Iterates through the game in `self._game_root` and draws a the analysis graph

        :return Image.Image: PIL Image object containing the graph
        """
        points = {}
        graph_image = Image.new('RGBA', (self._width, self._height), 'black')
        draw = ImageDraw.Draw(graph_image)
        game = self._game_root
        while True:
            move_num = game.ply()
            evalu = _eval(game).white().score(mate_score=self._max_eval)
            self._eval_at_move[move_num] = _eval(game).white()
            prev_evalu = 0 if game.parent is None else _eval(game.parent).white().score(mate_score=self._max_eval)
            points[move_num] = self._get_graph_position(_eval(game).white(), move_num)
            if game.parent is not None:
                zprev = self._get_graph_position(chess.engine.Cp(0), move_num-1)
                znew = self._get_graph_position(chess.engine.Cp(0), move_num)
                if evalu * prev_evalu < 0:  # eval symbols different => crossing the zero line
                    zinter = line_intersection((points[move_num-1], points[move_num]), (zprev, znew))
                    draw.polygon([zprev, points[move_num-1], zinter], fill="#514f4c" if prev_evalu < 0 else "#7f7e7c")
                    draw.polygon([zinter, points[move_num], znew], fill="#514f4c" if evalu < 0 else "#7f7e7c")
                else:
                    if evalu == 0:
                        fill_color = "#514f4c" if prev_evalu < 0 else "#7f7e7c"
                    else:
                        fill_color = "#514f4c" if evalu < 0 else "#7f7e7c"
                    draw.polygon([zprev, points[move_num-1], points[move_num], znew], fill=fill_color)
            if game.is_end():
                break
            game = game.next()
        points_list = [point for _, point in sorted(points.items())]
        draw.line(points_list, fill='white', width=self._line_width)
        x_axis_f = self._get_graph_position(chess.engine.Cp(0), 0)
        x_axis_t = self._get_graph_position(chess.engine.Cp(0), self._game_root.end().ply())
        draw.line([x_axis_f, x_axis_t], fill="#7d7d7d", width=self._line_width)
        return graph_image

    def _get_graph_position(self, evalu: chess.engine.Score, move: int) -> Coord:
        """Returns the position of a given evluation and move number on the evaluation graph

        :param chess.engine.Score evalu:
        :param int move:
        :return Coord: Coordinates on the evaluation graph
        """
        x = (self._width/(self._game_root.end().ply()-self._game_root.ply()))*move
        y = -((evalu.score(mate_score=self._max_eval)-self._max_eval)*(self._height-1))/(2*self._max_eval)
        return Coord(floor(x), floor(y))

    def at_move(self, move_num: int) -> Image.Image:
        """Returns a copy of the analysis graph with a red dot drawn at the given move number

        :param int move_num:
        :raises MoveOutOfRangeError: Requested move is not valid
        :return Image.Image:
        """
        if move_num > self._game_root.end().ply():
            raise MoveOutOfRangeError(move_num, self._game_root.end().ply())
        graph_background = self._background.copy()
        x, y = self._get_graph_position(self._eval_at_move[move_num], move_num)
        draw = ImageDraw.Draw(graph_background)
        draw.ellipse([
            (x-3-self._line_width, y-3-self._line_width),
            (x+3+self._line_width, y+3+self._line_width)
        ], fill="red")
        return graph_background.resize(self._output_size, Image.Resampling.HAMMING)
