import chess
import chess.pgn
from io import StringIO, BytesIO
from stockfish import Stockfish
from PIL import Image, ImageDraw, ImageFont
from math import floor, atan2, sin, cos, sqrt
import pkgutil

class CreateGifFromPGN:
    """Creates a GIF of a chess game from a PGN with optional
        stockfish evaluation chart

    Args:
        pgn (str): PGN as a string or filepath. Filepath requires optional parameter pgn_file=True
        reverse (bool, optional): Whether board should be reversed. Defaults to False.
        duration (float, optional): Duration of each GIF frame in seconds. Defaults to 0.5.
        pgn_file (bool, optional): Specify whether pgn contains a pgn string [False] or filepath [True]. Defaults to False.
    """
    def __init__(self, pgn: str, reverse: bool=False, duration: float=0.5, pgn_file: bool=False):
        self._stockfish = None
        self._analysis = False
        self._enable_arrows = False
        self._pieces = {}
        self._duration = duration
        self._reverse = reverse
        self._ws_color = '#f0d9b5' # setting the private property to not trigger the setter
        self._bs_color = '#b58863' # setting the private property to not trigger the setter
        self.board_size = 480
        self.bar_size = 30
        self.graph_size = 81
        self.max_eval = 1000

        if pgn_file:
            self._game = chess.pgn.read_game(open(pgn))
        else:
            self._game = chess.pgn.read_game(StringIO(pgn))
        if self._game.end().ply() < 1:
            raise ValueError(f"PGN did not evaluate to a game with any moves. It is likely that the PGN is invalid, "
                             f"or a filepath was provided instead (set pgn_file=True)\n\n"
                             f"pgn_file: {pgn_file} ({'Filepath excepted' if pgn_file == True else 'PGN string expected'})\n\n"
                             f"Provided PGN:\n{pgn}")
        self._board = self._game.board()

    @property
    def board_size(self) -> int:
        """(int) Size of the board in pixels. Defaults to 480."""
        return self._board_size

    @board_size.setter
    def board_size(self, bsize):
        self._board_size = floor(bsize/8)*8
        self._sq_size = self._board_size // 8
        self._pieces = {}
        self._create_square_images()
    
    @property
    def bar_size(self) -> int:
        """(int) Width of the evaluation bar in pixels. Defaults to 30."""
        return self._bar_size
    
    @bar_size.setter
    def bar_size(self, bar_size):
        self._bar_size = bar_size

    @property
    def graph_size(self) -> int:
        """(int) Height of the evaluation graph in pixels. Defaults to 81."""
        return self._graph_size

    @graph_size.setter
    def graph_size(self, graph_size):
        self._graph_size = graph_size
    
    @property
    def ws_color(self) -> str:
        """(str) Color of the white squares. Defaults to '#f0d9b5'."""
        return self._ws_color

    @ws_color.setter
    def ws_color(self, color):
        self._ws_color = color
        self._create_square_images(black=False)
    
    @property
    def bs_color(self) -> str:
        """(str) Color of the black squares. Defaults to '#b58863'"""
        return self._bs_color
    
    @bs_color.setter
    def bs_color(self, color):
        self._bs_color = color
        self._create_square_images(white=False)

    @property
    def max_eval(self) -> int:
        """(int) Maximum position evaluation in centipawns. Defaults to 1000."""
        return self._max_eval
    
    @max_eval.setter
    def max_eval(self, maximum):
        self._max_eval = maximum

    @property
    def enable_arrows(self) -> bool:
        """(bool) Whether drawing of move arrows is enabled."""
        return self._enable_arrows

    @enable_arrows.setter
    def enable_arrows(self, enable: bool):
        self._enable_arrows = enable

    def _create_square_images(self, white: bool=True, black: bool=True):
        """Generates the square images for pasting onto the board

        Args:
            white (bool, optional): Whether to generate the white square image. Defaults to True.
            black (bool, optional): Whether to generate the black square image. Defaults to True.
        """
        if white:
            self._ws = Image.new('RGBA', (self._sq_size, self._sq_size), self.ws_color)
        if black:
            self._bs = Image.new('RGBA', (self._sq_size, self._sq_size), self.bs_color)

    def enable_evaluation(self, path_to_stockfish='stockfish', depth: int=18, threads: int=1, memory: int=1024):
        """Enable stockfish evaluation

        Args:
            path_to_stockfish (str, optional): Path to stockfish binary. Defaults to 'stockfish'.
            depth (int, optional): Depth of stockfish evaluation. Defaults to 18.
            threads (int, optional): Number of threads to use in stockfish evaluation. Defaults to 1.
            memory (int, optional): Amount of memory to use in stockfish evaluation in Mb. Defaults to 1024.
        """
        try:
            self._stockfish = Stockfish(path_to_stockfish,parameters={"Threads": threads, "Hash": memory})
        except FileNotFoundError:
            print(f"Stockfish was not found at the specified path: {path_to_stockfish}")
        else:
            self._stockfish.set_depth(depth)
            self._analysis = True

    def _get_square_position(self, square: int, center: bool=False) -> tuple:
        """Returns the coordinates of a given square

        Args:
            square (int): Square number in range 0 (a1) to 63 (h8)
            centre (bool, optional): Whether coordinates are top left corner or centre. Defaults to False.

        Returns:
            (int, int): Tuple with x,y coordinate of the top left corner or center of the square
        """
        row = floor(square/8)
        column = square-(row*8)
        if self._reverse:
            if center:
                return ((7-column)*self._sq_size+(self._sq_size/2), row*self._sq_size+(self._sq_size/2))
            else:
                return ((7-column)*self._sq_size, row*self._sq_size)
        else:
            if center:
                return (column*self._sq_size+(self._sq_size/2), (7-row)*self._sq_size+(self._sq_size/2))
            else:
                return (column*self._sq_size, (7-row)*self._sq_size)

    def _get_square_color(self, square: int) -> bool:
        """Returns the color of a given square

        Args:
            square (int): Square number in range 0 (a1) to 63 (h8)

        Returns:
            bool: True if square is white, False if square is black
        """
        return square % 2 != floor(square/8) % 2

    def _piece_string(self, piece: object) -> str:
        """Returns the filename corresponding to a piece letter

        Args:do
            piece (object): python-chess piece object

        Returns:
            str: piece filename
        """
        p = piece.symbol()
        if p.isupper():
            return "w%s" % p.lower()
        else:
            return "b%s" % p.lower()

    def _draw_board(self):
        """Redraws the entire board"""
        if self._analysis:
            self._board_image = Image.new('RGBA',(self.board_size + self.bar_size,self.board_size + self.graph_size))
        else:
            self._board_image = Image.new('RGBA',(self.board_size,self.board_size))
        self._draw_changes(list(chess.SQUARES))

    def _draw_changes(self, changes: list):
        """Redraws the listed squares

        Args:
            changes (list): List of ints denoting chess squares
        """
        for square in changes:
            self._draw_square(square)
        if self._analysis:
            self._draw_evaluation()
    
    def _draw_square(self, square: int) -> None:
        """Draws the specified square

        Args:
            square (int): Int denoting a chess square
        """
        crd = self._get_square_position(square)
        if self._get_square_color(square):
            self._board_image.paste(self._ws, crd)
        else:
            self._board_image.paste(self._bs, crd)
        p = self._board.piece_at(square)
        if not p is None:
            self._board_image.paste(self._get_piece_image(p), crd, self._get_piece_image(p))

    def _get_piece_image(self, piece: str) -> object:
        """Loads a piece image or returns a piece image if it has already been loaded

        Args:
            piece (str): single character string denoting a chess piece

        Returns:
            object: PIL image object
        """
        piece_string = self._piece_string(piece)
        try:
            return self._pieces[piece_string]
        except KeyError:
            self._pieces[piece_string] = Image.open(BytesIO(pkgutil.get_data(__name__, f"assets/{piece_string}.png"))).resize((self._sq_size, self._sq_size)) 
            return self._pieces[piece_string]

    def _draw_arrow(self, square1: int, square2: int, color: str='green'):
        """Draw an arrow between two squares

        Args:
            square1 (int): Index of square from
            square2 (int): Index of square to
            color (str, optional): Arrow color: green, blue or red. Defaults to 'green'.
        """
        def rotate_around_point(point, radians, origin=(0, 0)):
            x, y = point
            ox, oy = origin
            qx = ox + cos(radians) * (x - ox) + sin(radians) * (y - oy)
            qy = oy + -sin(radians) * (x - ox) + cos(radians) * (y - oy)
            return qx, qy

        def shorten_line(c1, c2, pix):
            dx = c2[0] - c1[0]
            dy = c2[1] - c1[1]
            l = sqrt(dx*dx+dy*dy)
            if l > 0:
                dx /= l
                dy /= l
            dx *= l-pix
            dy *= l-pix
            return (c1,(c1[0]+dx, c1[1]+dy))

        arrow_mask = Image.new('RGBA', self._board_image.size)
        arrow = {
            'green': (0, 255, 0, 100),
            'blue':  (0, 0, 255, 100),
            'red':   (255, 0, 0, 100)
        }
        from_crd = self._get_square_position(square1, center=True)
        to_crd = self._get_square_position(square2, center=True)
        draw = ImageDraw.Draw(arrow_mask)
        # draw arrow line
        draw.line(shorten_line(from_crd, to_crd, self._sq_size/2), fill=arrow[color], width=floor(self._sq_size/4))
        
        # draw arrow head
        x0, y0 = from_crd
        x1, y1 = to_crd
        line_degrees = -atan2(y1-y0, x1-x0)
        c1 = to_crd
        c2 = rotate_around_point((x1-self._sq_size/2, y1-self._sq_size/3), line_degrees, c1)
        c3 = rotate_around_point((x1-self._sq_size/2, y1+self._sq_size/3), line_degrees, c1)
        draw.polygon([c1, c2, c3], fill=arrow[color])
        
        self._board_image = Image.alpha_composite(self._board_image, arrow_mask)
    
    def _draw_evaluation(self):
        bar_width = self.bar_size
        bar_height = self.board_size
        self._stockfish.set_fen_position(self._board.fen())
        evaluation = self._stockfish.get_evaluation()
        if evaluation['type'] == "cp":
            evstring  = '{0:+.{1}f}'.format(round(float(evaluation['value'])/100,1),1)
            if evaluation['value'] > 0:
                evalu = min(evaluation['value'],self.max_eval)
            else:
                evalu = max(evaluation['value'],-self.max_eval)
        else:
            evstring = "M%s" % evaluation['value']
            if evaluation['value'] >= 0: # white ahead or is checkmate
                if evaluation['value'] == 0 and not self._board.outcome().winner: # if M0 and .winner == False, black won
                    evalu = -self.max_eval
                else: # white ahead or has won (M0)
                    evalu = self.max_eval
            else: # black ahead
                evalu = -self.max_eval

        if evalu > 0:
            evstringcolor = "black"
            evstringy = 0 if self._reverse else bar_height
            evstringanchor = "ma" if self._reverse else "md"
        else:
            evstringcolor = "white"
            evstringy = bar_height if self._reverse else 0
            evstringanchor = "md" if self._reverse else "ma"

        self._eval_history.append(evalu)
        evalu = -((evalu-self.max_eval)*bar_height)/(2*self.max_eval)

        draw = ImageDraw.Draw(self._board_image)
        draw.rectangle([(self.board_size,0),(self.board_size+bar_width-1,self.board_size-1)],fill="white")
        if self._reverse:
            draw.rectangle([(self.board_size,self.board_size-evalu),(self.board_size+bar_width-1,self.board_size-1)],fill="black")
        else:
            draw.rectangle([(self.board_size,0),(self.board_size+bar_width-1,evalu)],fill="black")
        font = ImageFont.truetype(BytesIO(pkgutil.get_data(__name__, "fonts/Carlito-Regular.ttf")), 10)
        draw.text((self.board_size+bar_width/2,evstringy),evstring,font=font,fill=evstringcolor,anchor=evstringanchor)

    def _draw_graph(self):
        points = []
        graph_image = Image.new('RGBA', (self.board_size + self.bar_size, self.graph_size))
        draw = ImageDraw.Draw(graph_image)
        for move_num, evalu in enumerate(self._eval_history):
            points.append(self._get_graph_position(evalu,move_num))
            if move_num > 0:
                zprev = self._get_graph_position(0,move_num-1)
                znew = self._get_graph_position(0,move_num)
                if evalu * self._eval_history[move_num-1] < 0: # eval symbols different => crossing the zero line
                    zinter = self._line_intersection((points[move_num-1],points[move_num]),(zprev,znew))
                    draw.polygon([zprev,points[move_num-1],zinter],fill="#514f4c" if self._eval_history[move_num-1] < 0 else "#7f7e7c")
                    draw.polygon([zinter,points[move_num],znew],fill="#514f4c" if self._eval_history[move_num] < 0 else "#7f7e7c")
                else:
                    draw.polygon([zprev,points[move_num-1],points[move_num],znew],fill="#514f4c" if self._eval_history[move_num] < 0 else "#7f7e7c")
        draw.line(points,fill='white',width=1)
        draw.line([(0,self.graph_size/2),(self.board_size+self.bar_size,self.graph_size/2)],fill="grey",width=1)
        return graph_image

    def _get_graph_position(self, evalu: float, move: int) -> tuple:
        """Returns the position of a point on the evaluation graph

        Args:
            evalu (float): Position evaluation
            move (int): Move number

        Returns:
            tuple: Tuple containing x,y coordinates of the graph position
        """
        x = ((self.board_size + self.bar_size)/self._num_moves)*move
        y = -((evalu-self.max_eval)*(self.graph_size-1))/(2*self.max_eval)
        return (floor(x),floor(y))

    def _line_intersection(self, line1: tuple, line2: tuple) -> tuple:
        """Returns the intersection point of two lines, or False if no intersection

        Args:
            line1 (tuple): Line 1 defined by a tuple containing two x,y tuples
            line2 (tuple): Line 2 defined by a tuple containing two x,y tuples

        Returns:
            tuple: A tuple contianing the x,y coordinates 
        """
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)

        if div == 0: # no intersection
            return False

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return x, y

    def generate(self, output_file: str):
        """Output GIF

        Args:
            output_file (str): Full path and filename of output file
        """
        self._eval_history = list()
        self._num_moves = self._game.end().ply()
        self._draw_board()
        frames = [self._board_image.copy()]
        for move in self._game.mainline_moves():
            prev = [self._board.piece_at(sq) for sq in chess.SQUARES]
            self._board.push(move)
            changed = [sq for sq in chess.SQUARES if self._board.piece_at(sq) != prev[sq]]
            if self.enable_arrows:
                self._draw_board()
                self._draw_arrow(move.from_square, move.to_square, color='blue')
                if self._board.is_check():
                    for sq in self._board.checkers():
                        self._draw_arrow(sq, self._board.king(self._board.turn), color='red')
            else:
                self._draw_changes(changed)
            frames.append(self._board_image.copy())

        if self._analysis:
            graph_image = self._draw_graph()
            for m in range(0,len(frames)):
                g = graph_image.copy()
                x,y = self._get_graph_position(self._eval_history[m],m)
                draw = ImageDraw.Draw(g)
                draw.ellipse([(x-3,y-3),(x+3,y+3)],fill="red")
                frames[m].paste(g,(0,self.board_size))

        last_frame = frames[-1].copy()
        for _ in range(20):
            frames.append(last_frame)

        frames[0].save(output_file,
                       format="GIF",
                       append_images=frames[1:],
                       optimize=True,
                       save_all=True,
                       duration=int(self._duration*1000),
                       loop=0)

    def output_image(self, image): # dump an image for bug testing
        print("Saving image")
        image.save("output.png", format="PNG")