import unittest
from gifpgn import CreateGifFromPGN
import pkgutil
from io import StringIO, BytesIO
import chess

class TestGIFPGN(unittest.TestCase):
    def test_get_square_color(self):
        self.assertTrue(CreateGifFromPGN._get_square_color(None, 8))

    def test_get_square_position(self):
        gif = CreateGifFromPGN(pkgutil.get_data(__name__, "test.pgn").decode('utf-8'))
        gif.board_size = 560
        test = gif._get_square_position(0)
        expected = (0,(560/8)*7)
        self.assertEqual(test, expected)
    
    def test_piece_string(self):
        self.assertEqual(CreateGifFromPGN._piece_string(None, chess.Piece(chess.QUEEN, chess.WHITE)), "wq")
        self.assertEqual(CreateGifFromPGN._piece_string(None, chess.Piece(chess.ROOK, chess.BLACK)), "br")

if __name__ == '__main__':
    unittest.main()