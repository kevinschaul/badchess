from math import inf
import chess
from badchess.main import (
    estimate_strength,
    find_best_move,
)


def test_estimate_strength_initial():
    board = chess.Board()
    assert estimate_strength(board) == 0


def test_estimate_strength_mate_white():
    board = chess.Board(fen="8/8/2k5/Q2Q4/8/8/8/4K3 b - - 9 5")
    assert estimate_strength(board) == inf


def test_estimate_strength_mate_black():
    board = chess.Board(fen="8/8/2K5/q2q4/8/8/8/4k3 w - - 9 5")
    assert estimate_strength(board) == -inf


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
