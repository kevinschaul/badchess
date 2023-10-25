import chess
from badchess.main import (
    build_move_tree,
    estimate_strength,
    find_best_move,
)

FEN_MORPHY_DEFENCE = (
    "r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4"
)


def test_estimate_strength(benchmark):
    board = chess.Board()
    benchmark(estimate_strength, board)


# def test_build_move_tree(benchmark):
#     board = chess.Board()
#     benchmark(build_move_tree, board, depth=2)


def test_find_best_move(benchmark):
    board = chess.Board()
    benchmark(find_best_move, board)

def test_find_best_move_morphy(benchmark):
    board = chess.Board(FEN_MORPHY_DEFENCE)
    benchmark(find_best_move, board)
