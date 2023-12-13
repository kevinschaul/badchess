import chess
from badchess.main import (
    find_best_move,
)

fen='r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4'

def test_find_best_move_3(benchmark):
    board = chess.Board(fen)
    benchmark(find_best_move, board, 3)

def test_find_best_move_4(benchmark):
    board = chess.Board(fen)
    benchmark(find_best_move, board, 4)
