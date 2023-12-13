#!/usr/bin/env python

from concurrent.futures import ThreadPoolExecutor
import fcntl
import logging
from math import inf
import os
import select
import sys
import queue
from typing import Tuple

import chess

# Custom types
Move = str
Moves = list[Move]
StrengthAndMoves = Tuple[float, Moves]

logging.basicConfig(
    filename="badchess.log",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s %(message)s",
)

should_exit = False

MAX_DEPTH = 4


def producer(q: queue.Queue):
    """
    Read a line from stdin, in a non-blocking way -- waiting at most
    1 second per call. Put any input lines into the queue.
    """
    lines = readlines_with_timeout(1)
    for line in lines:
        q.put(line)
        logging.debug(f"Producer: {line}")


def readlines_with_timeout(timeout: int) -> list[str]:
    """
    Return an array of lines from stdin, waiting at most `timeout` seconds.
    Note that stdin has been set to non-blocking mode in main().
    """
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)

    if rlist:
        # Data is available to read from sys.stdin
        lines = []
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            lines.append(line)
        return lines
    else:
        # Timeout reached
        return []


def consumer(q: queue.Queue, board: chess.Board, i: int):
    while not should_exit:
        try:
            line = q.get(timeout=1)
            if line:
                process_command(line, board)
        except queue.Empty:
            pass
    logging.debug(f"Consumer {i} done")


def send_command(command: str):
    logging.debug(f"Command sent: {command}")
    sys.stdout.write(f"{command}\n")
    sys.stdout.flush()


def process_command(command: str, board: chess.Board):
    logging.debug(f"Command received: {command}")
    words = command.strip().split(" ")

    if words[0] == "uci":
        process_uci()
    elif words[0] == "setoption":
        process_setoption()
    elif words[0] == "isready":
        process_isready()
    elif words[0] == "ucinewgame":
        process_ucinewgame(board)
    elif words[0] == "position":
        process_position(words, board)
    elif words[0] == "go":
        process_go(board)
    elif words[0] == "stop":
        process_stop()
    elif words[0] == "quit":
        process_quit()


def process_setoption():
    logging.warning("setoption ignored")


def process_uci():
    send_command("id name badchess")
    send_command("id author Kevin Schaul")
    send_command("uciok")


def process_isready():
    send_command("readyok")


def process_ucinewgame(board: chess.Board):
    board.reset()


def process_position(words: list[str], board: chess.Board):
    """
    position [fen <fenstring> | startpos ]  moves <move1> .... <movei>

    set up the position described in fenstring on the internal board and
    play the moves on the internal chess board.
    if the game was played  from the start position the string "startpos" will be sent
    """
    if words[1] == "startpos" and words[2] == "moves":
        board.reset()
        [board.push_uci(move) for move in words[3:]]
    elif words[1] == "fen":
        board = chess.Board(" ".join(words[2:8]))
        if len(words) >= 9 and words[8] == "moves":
            [board.push_uci(move) for move in words[9:]]


def process_go(board: chess.Board):
    move = find_best_move(board, depth=3)
    send_command(f"bestmove {move}")


def process_stop():
    # TODO stop other consumer threads
    pass


def process_quit():
    global should_exit
    should_exit = True
    logging.debug(f"exit set")


def find_best_move(board: chess.Board, depth=3):
    return alpha_beta_search(board, depth)


n_positions_searched = 0


def alpha_beta_search(board: chess.Board, depth=3):
    global n_positions_searched
    n_positions_searched = 0

    func = max_value if board.turn == chess.WHITE else min_value
    strength, move = func(board, -inf, inf, depth, 0)
    logging.info(f"n_positions_searched: {n_positions_searched}")
    logging.info(f"move: {move} strength: {strength}")

    return move


def order_moves(board):
    return sorted(board.legal_moves, key=lambda move: _order_move(board, move))


def _order_move(board, move):
    if board.piece_at(move.to_square):
        return -1
    return 0


def max_value(board: chess.Board, alpha, beta, depth, _current_depth):
    global n_positions_searched

    if depth == _current_depth:
        return (estimate_strength(board), None)
    else:
        strength = -inf
        best_move = None
        for move in order_moves(board):
            n_positions_searched += 1
            move_uci = move.uci()
            new_board = board.copy(stack=False)
            new_board.push_uci(move_uci)
            new_strength, a2 = min_value(
                new_board, alpha, beta, depth, _current_depth + 1
            )
            if new_strength > strength:
                strength = new_strength
                best_move = move_uci
                alpha = max(alpha, strength)
            if strength >= beta:
                return (strength, best_move)

        return (strength, best_move)


def min_value(board: chess.Board, alpha, beta, depth, _current_depth):
    if depth == _current_depth:
        return (estimate_strength(board), None)
    else:
        strength = inf
        best_move = None
        for move in order_moves(board):
            move_uci = move.uci()
            new_board = board.copy(stack=False)
            new_board.push_uci(move_uci)
            new_strength, a2 = max_value(
                new_board, alpha, beta, depth, _current_depth + 1
            )
            if new_strength < strength:
                strength = new_strength
                best_move = move_uci
                beta = min(beta, strength)
            if strength <= alpha:
                return (strength, best_move)

        return (strength, best_move)


def estimate_strength(board: chess.Board) -> float:
    """
    Estimate the strength of the board, from white's position.
    """
    if board.is_checkmate():
        outcome = board.outcome()
        if outcome and outcome.winner == chess.WHITE:
            return inf
        elif outcome and outcome.winner == chess.BLACK:
            return -inf

    values = {
        chess.KING: 100,
        chess.QUEEN: 9,
        chess.ROOK: 5,
        chess.BISHOP: 3,
        chess.KNIGHT: 3,
        chess.PAWN: 1,
    }
    white = sum(v * len(board.pieces(k, chess.WHITE)) for k, v in values.items())
    black = sum(v * len(board.pieces(k, chess.BLACK)) for k, v in values.items())
    return white - black


def main():
    # Set sys.stdin to non-blocking mode
    fd = sys.stdin.fileno()
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    q = queue.Queue()
    board = chess.Board()

    n_consumers = 2

    with ThreadPoolExecutor(max_workers=n_consumers + 1) as executor:
        # Set up consumers
        [executor.submit(consumer, q, board, i) for i in range(n_consumers)]

        # Set up producer
        producerFuture = executor.submit(producer, q)
        while not should_exit:
            if producerFuture.done():
                producerFuture = executor.submit(producer, q)


if __name__ == "__main__":
    main()
