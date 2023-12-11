from math import inf
import chess
from badchess.main import (
    build_move_tree,
    estimate_strength,
    find_best_move,
    minimax,
)
from badchess.tree import Tree

# TODO: add tests for max_strength_moves, min_strength_moves


def test_tree_n_nodes_base():
    t = Tree()
    assert t.n_nodes() == 1


def test_tree_n_nodes_depth_2():
    t = Tree(
        children=(
            Tree(),
            Tree(),
            Tree(),
        ),
    )
    assert t.n_nodes() == 4


def test_estimate_strength_initial():
    board = chess.Board()
    assert estimate_strength(board) == 0


def test_estimate_strength_mate_white():
    board = chess.Board(fen="8/8/2k5/Q2Q4/8/8/8/4K3 b - - 9 5")
    assert estimate_strength(board) == inf


def test_estimate_strength_mate_black():
    board = chess.Board(fen="8/8/2K5/q2q4/8/8/8/4k3 w - - 9 5")
    assert estimate_strength(board) == -inf


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


def test_minimax_basic():
    move_tree = Tree(
        "root",
        children=(
            Tree("c8d7", strength=0, children=(Tree("d4d5", strength=0),)),
            Tree("c8e5", strength=3, children=(Tree("d4d7", strength=-3),)),
        ),
    )
    moves_list = minimax(move_tree, True)
    assert moves_list[0] == "c8d7"


def test_minimax_basic_reverse():
    move_tree = Tree(
        "root",
        children=(
            Tree("c8d7", strength=0, children=(Tree("d4d5", strength=0),)),
            Tree("c8e5", strength=3, children=(Tree("d4d7", strength=-3),)),
        ),
    )
    moves_list = minimax(move_tree, False)
    assert moves_list[0] == "c8e5"


def test_find_best_move_1_depth_3():
    board = chess.Board(
        fen="r1b1kb1r/2q2ppp/ppn5/2pPp3/P7/1P3NPB/3P1P1P/RNBQK2R b KQkq - 1 10"
    )

    best_move = find_best_move(board, depth=3)

    assert best_move == "c8h3"


def test_find_best_move_2_depth_3():
    board = chess.Board(fen="3k1bnr/1p2pppp/1p6/r7/PB6/7P/1PP1PP1P/R2K1B1R b - - 0 14")

    best_move = find_best_move(board, depth=3)

    assert best_move != "a5a4"


def test_staircase_mate():
    board = chess.Board(fen="8/3k4/1Q6/Q7/8/8/8/4K3 w - - 6 4")
    move_tree = build_move_tree(board, depth=3)
    moves_list = minimax(move_tree, board.turn == chess.WHITE)
    for move in moves_list:
        board.push_uci(move)

    # There are many ways to mate this position in three
    assert board.is_checkmate()
