import chess
from badchess.main import (
    find_best_move,
)

board_init = chess.Board()

def test_find_best_move_depth_3():
    find_best_move(board_init, depth=3)

def test_find_best_move_depth_4():
    find_best_move(board_init, depth=4)
