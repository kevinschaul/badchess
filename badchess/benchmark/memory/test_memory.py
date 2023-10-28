import chess
from badchess.main import (
    build_move_tree,
)

board_init = chess.Board()

def test_build_move_tree_depth_2():
    build_move_tree(board_init, depth=2)

def test_build_move_tree_depth_3():
    build_move_tree(board_init, depth=3)

def test_build_move_tree_depth_4():
    build_move_tree(board_init, depth=4)
