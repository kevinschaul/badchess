import chess
from badchess.main import (
    build_move_tree,
    estimate_strength,
    add_strength_to_tree,
    minimax,
)

FEN_MORPHY_DEFENCE = (
    "r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4"
)


def test_estimate_strength_initial():
    board = chess.Board()
    assert estimate_strength(board) == 0


def test_build_move_tree_initial_depth_1():
    board = chess.Board()
    move_tree = build_move_tree(board, depth=1)
    assert len(move_tree.children) == 20
    assert move_tree.children[0].children == []


def test_build_move_tree_initial_depth_2():
    board = chess.Board()
    move_tree = build_move_tree(board, depth=2)
    assert len(move_tree.children) == 20

    e2e4 = move_tree.get_child("e2e4")
    assert e2e4
    assert len(e2e4.children) == 20


def test_build_move_tree_initial_depth_4():
    board = chess.Board()
    move_tree = build_move_tree(board, depth=4)

    depth = 0
    move = move_tree
    while len(move.children) >= 1:
        move = move.children.pop()
        depth += 1
    assert depth == 4


def test_add_strength_to_tree_morphy_depth_1():
    board = chess.Board(fen=FEN_MORPHY_DEFENCE)
    move_tree = build_move_tree(board, depth=1)
    add_strength_to_tree(board, move_tree, depth=1)

    assert "strength" in move_tree.children[0].data

    # for move in move_tree.children:
    #     print(move.name, move.data)

    b5c6 = move_tree.get_child("b5c6")
    assert b5c6
    assert b5c6.data["strength"] == 3


def test_minimax_morphy_depth_3():
    board = chess.Board(fen=FEN_MORPHY_DEFENCE)
    move_tree = build_move_tree(board, depth=3)
    add_strength_to_tree(board, move_tree, depth=3)
    moves_list = minimax(move_tree)

    assert moves_list[0] == "b5c6"
