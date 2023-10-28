import chess
from badchess.main import (
    build_move_tree,
    estimate_strength,
    find_best_move,
    get_tree_max,
    get_tree_min,
    minimax,
)
from badchess.tree import Tree

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


def test_get_tree_max_basic_1():
    move_tree = Tree(
        "root",
        children=(
            Tree("c8d7", strength=0),
            Tree("c8e5", strength=0),
            Tree("c8h3", strength=3),
        ),
    )
    assert get_tree_max(move_tree) == (3, [2])


def test_get_tree_max_basic_2():
    move_tree = Tree(
        "root",
        children=(
            Tree("c8d7", strength=3),
            Tree("c8e5", strength=0),
            Tree("c8h3", strength=0),
        ),
    )
    assert get_tree_max(move_tree) == (3, [0])


def test_get_tree_max_ties_last():
    move_tree = Tree(
        "root",
        children=(
            Tree("c8d7", strength=0),
            Tree("c8e5", strength=3),
            Tree("c8h3", strength=3),
        ),
    )
    assert get_tree_max(move_tree) == (3, [1, 2])


def test_get_tree_max_ties_first():
    move_tree = Tree(
        "root",
        children=(
            Tree("c8d7", strength=3),
            Tree("c8e5", strength=3),
            Tree("c8h3", strength=0),
        ),
    )
    assert get_tree_max(move_tree) == (3, [0, 1])


def test_get_tree_min_basic_1():
    move_tree = Tree(
        "root",
        children=(
            Tree("c8d7", strength=0),
            Tree("c8e5", strength=3),
            Tree("c8h3", strength=3),
        ),
    )
    assert get_tree_min(move_tree) == (0, [0])


def test_get_tree_min_basic_2():
    move_tree = Tree(
        "root",
        children=(
            Tree("c8d7", strength=3),
            Tree("c8e5", strength=3),
            Tree("c8h3", strength=0),
        ),
    )
    assert get_tree_min(move_tree) == (0, [2])


def test_get_tree_min_ties_first():
    move_tree = Tree(
        "root",
        children=(
            Tree("c8d7", strength=0),
            Tree("c8e5", strength=0),
            Tree("c8h3", strength=3),
        ),
    )
    assert get_tree_min(move_tree) == (0, [0, 1])


def test_get_tree_min_ties_last():
    move_tree = Tree(
        "root",
        children=(
            Tree("c8d7", strength=3),
            Tree("c8e5", strength=0),
            Tree("c8h3", strength=0),
        ),
    )
    assert get_tree_min(move_tree) == (0, [1, 2])


def test_minimax_morphy_depth_3():
    board = chess.Board(fen=FEN_MORPHY_DEFENCE)
    move_tree = build_move_tree(board, depth=3)
    moves_list = minimax(move_tree, True)

    assert moves_list[0] == "b5c6"


def test_find_best_move_morphy_depth_3():
    board = chess.Board(fen=FEN_MORPHY_DEFENCE)
    best_move = find_best_move(board, depth=3)

    assert best_move == "b5c6"


def test_find_best_move_1_depth_3():
    board = chess.Board(
        fen="r1b1kb1r/2q2ppp/ppn5/2pPp3/P7/1P3NPB/3P1P1P/RNBQK2R b KQkq - 1 10"
    )

    best_move = find_best_move(board, depth=3)

    assert best_move == "c8h3"


# def test_find_best_move_2_depth_3():
#     board = chess.Board(fen="3k1bnr/1p2pppp/1p6/r7/PB6/7P/1PP1PP1P/R2K1B1R b - - 0 14")
#
#     best_move = find_best_move(board, depth=3)
#
#     assert best_move == "a5a8"
