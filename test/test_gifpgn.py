import unittest
from unittest.mock import patch
from gifpgn import CreateGifFromPGN
import pkgutil
import chess
from math import floor
from random import randint
from io import BytesIO
from PIL import Image

class fakeStockfish:
    def __init__(self, path, parameters={}, fake_eval={'type': 'cp', 'value': 0}, rand_eval=False):
        self._eval = fake_eval
        self._rand_eval = rand_eval
        self._eval_num = 0
    
    def set_depth(self, depth):
        return True

    def set_fen_position(self, fen):
        return True
    
    def get_evaluation(self):
        if self._rand_eval:
            first_few = [40,100,500,-800,0,-40,1500]
            try:
                val = first_few[self._eval_num]
            except IndexError:
                val = randint(-1000,1000)
            self._eval_num += 1
            return {'type': 'cp', 'value': val}
        else:
            return self._eval

class fakeBoard(chess.Board):
    def outcome(self):
        return fakeOutcome(False)

class fakeOutcome:
    def __init__(self, outcome=False):
        self.winner = outcome

class TestGIFPGN(unittest.TestCase):
    def get_test_pgn(self):
        return pkgutil.get_data(__name__, "test.pgn").decode('utf-8')

    def test_get_square_color(self):
        self.assertTrue(CreateGifFromPGN._get_square_color(None, 8))

    def test_get_square_position(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif.board_size = 560
        test = gif._get_square_position(0)
        expected = (0,(560/8)*7)
        self.assertEqual(test, expected)

    def test_get_square_position_reverse(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'), reverse=True)
        gif.board_size = 560
        test = gif._get_square_position(0)
        expected = (560/8*7, 0)
        self.assertEqual(test, expected)

    def test_get_square_position_centre(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif.board_size = 560
        test = gif._get_square_position(8, center=True)
        expected = (560/16, (560/8)*6.5)
        self.assertEqual(test, expected)
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'), reverse=True)
        gif.board_size = 560
        test = gif._get_square_position(8, center=True)
        expected = (560/8*7.5, 560/8*1.5)
        self.assertEqual(test, expected)

    def test_piece_string(self):
        self.assertEqual(CreateGifFromPGN._piece_string(None, chess.Piece(chess.QUEEN, chess.WHITE)), "wq")
        self.assertEqual(CreateGifFromPGN._piece_string(None, chess.Piece(chess.ROOK, chess.BLACK)), "br")

    def test_invalid_pgn(self):
        with self.assertRaises(ValueError):
            gif = CreateGifFromPGN("invalid pgn")

    def test_property_board_size(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif.board_size = 560
        self.assertEqual(gif.board_size, 560)
        self.assertEqual(gif._sq_size, 70)
        self.assertEqual(gif._ws.size, (70, 70))
        self.assertEqual(gif._bs.size, (70, 70))

    def test_property_bar_size(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif.bar_size = 20
        self.assertEqual(gif.bar_size, 20)
    
    def test_property_graph_size(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif.graph_size = 100
        self.assertEqual(gif.graph_size, 100)

    def test_property_ws_color(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif.ws_color = '#ff0000'
        self.assertEqual(gif._ws.getpixel((1, 1)), (255, 0, 0, 255))

    def test_property_bs_color(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif.bs_color = '#00ff00'
        self.assertEqual(gif._bs.getpixel((1, 1)), (0, 255, 0, 255))

    def test_max_eval(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif.max_eval = 500
        self.assertEqual(gif.max_eval, 500)
        gif._stockfish = fakeStockfish('fake/path', fake_eval={'type': 'cp', 'value': -1200})
        gif._eval_history = list()
        gif._draw_board()
        gif._draw_evaluation()
        self.assertEqual(gif._eval_history[-1], -500)

    def test_draw_evaluation(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif._stockfish = fakeStockfish('fake/path', fake_eval={'type': 'mate', 'value': -3})
        gif._analysis = True
        gif._eval_history = list()
        gif._draw_board()
        gif._draw_evaluation()
        self.assertEqual(gif._board_image.getpixel((gif.board_size,1)),(0,0,0,255))
        self.assertEqual(gif._board_image.getpixel((gif.board_size,gif.board_size-1)),(0,0,0,255))
        gif._stockfish._eval =  {'type': 'mate', 'value': 1}
        gif._draw_evaluation()
        self.assertEqual(gif._board_image.getpixel((gif.board_size,1)),(255,255,255,255))
        self.assertEqual(gif._board_image.getpixel((gif.board_size,gif.board_size-1)),(255,255,255,255))
        gif._stockfish._eval =  {'type': 'mate', 'value': 0}
        gif._board = fakeBoard()
        gif._draw_evaluation()
        self.assertEqual(gif._board_image.getpixel((gif.board_size,1)),(0,0,0,255))
        self.assertEqual(gif._board_image.getpixel((gif.board_size,gif.board_size-1)),(0,0,0,255))

    def test_draw_board(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif.board_size = 560
        gif.bar_size = 30
        gif.graph_size = 81
        gif._analysis = True
        gif._stockfish = fakeStockfish('fake/path', fake_eval={'type': 'cp', 'value': -1200})
        gif._eval_history = list()
        gif._draw_board()
        self.assertEqual(gif._board_image.size, (560+30, 560+81))

    def test_draw_arrow(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif._draw_board()
        original_color = gif._board_image.getpixel(gif._get_square_position(24, center=True))
        gif._draw_arrow(24, 28, color='green')
        self.assertNotEqual(original_color, gif._board_image.getpixel(gif._get_square_position(24, center=True)))
        self.assertEqual(gif._board_image.getpixel(gif._get_square_position(24, center=True)), gif._board_image.getpixel(gif._get_square_position(26, center=True)))

    def test_generate(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif._stockfish = fakeStockfish('fake/path', rand_eval=True)
        gif._analysis = True
        gif.enable_arrows = True
        gif._board = fakeBoard()
        output_image = BytesIO()
        gif.generate(output_image)
        test_image = Image.open(output_image)
        self.assertEqual(test_image.n_frames, 8)


if __name__ == '__main__':
    unittest.main()