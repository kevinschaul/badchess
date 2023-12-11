#!/usr/bin/env python

from concurrent.futures import ThreadPoolExecutor
import fcntl
import logging
from math import inf
import os
import random
import select
import sys
import queue
from typing import Tuple

import chess

from badchess.tree import Tree

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


def find_best_move(board: chess.Board, depth=3) -> Move:
    # Build out a move tree
    move_tree = build_move_tree(board, depth=depth)

    moves_list = minimax(move_tree, board.turn == chess.WHITE)
    logging.info(f"moves_list: {moves_list}")
    return moves_list[0]


def minimax(move_tree: Tree, is_cur_move_white: bool) -> Moves:
    """
    Returns a list of moves that are estimated to be the best,
    by maximizing strength for white and minimizing strength for
    black (or the reverse, if `is_cur_move_white` is False).
    """
    return _minimax(move_tree, [], is_cur_move_white)[1]


def _minimax(
    move_tree: Tree, moves_list: Moves, is_cur_move_white: bool
) -> StrengthAndMoves:
    moves_list = moves_list.copy()
    cur_move_tree = move_tree
    for move in moves_list:
        cur_move_tree = cur_move_tree.get_child(move)
        if not cur_move_tree:
            raise KeyError

    # Base case. We know the strength.
    if not cur_move_tree.children:
        return (cur_move_tree.strength, moves_list)

    else:
        possible_moves = []
        for move in cur_move_tree.children:
            next_moves_list = moves_list.copy()
            next_moves_list.append(move.name)
            possible_moves.append(
                _minimax(move_tree, next_moves_list, not is_cur_move_white)
            )

        if is_cur_move_white:
            # Find the max strength
            best_move = random.choice(max_strength_moves(possible_moves))
        else:
            # Find the min strength
            best_move = random.choice(min_strength_moves(possible_moves))
        return best_move


def max_strength_moves(moves: list[StrengthAndMoves]):
    """
    Returns a list of moves with the maximum strength, including ties.
    moves is a tuple containing the strength and move sequence.
    """
    moves_sorted = sorted(moves, key=lambda x: x[0], reverse=True)
    return [move for move in moves_sorted if move[0] == moves_sorted[0][0]]


def min_strength_moves(moves: list[StrengthAndMoves]):
    """
    Returns a list of moves with the minimum strength, including ties.
    moves is a tuple containing the strength and move sequence.
    """
    moves_sorted = sorted(moves, key=lambda x: x[0], reverse=False)
    return [move for move in moves_sorted if move[0] == moves_sorted[0][0]]


def build_move_tree(board: chess.Board, depth=1) -> Tree:
    if depth > MAX_DEPTH:
        raise ValueError(f"Depth > {MAX_DEPTH} is asking for trouble")
    return _build_move_tree(board, depth=depth)


def _build_move_tree(
    board: chess.Board, depth=1, _current_depth=1, _move="root"
) -> Tree:
    tree = Tree(name=_move)

    for move in board.legal_moves:
        move_uci = move.uci()
        new_board = board.copy(stack=False)
        new_board.push_uci(move_uci)

        if _current_depth == depth:
            # If we are at max depth, this move node is a leaf
            move_node = Tree(name=move_uci)
        else:
            # Otherwise let's build a subtree with this move
            move_node = _build_move_tree(
                new_board.copy(stack=False),
                depth=depth,
                _current_depth=_current_depth + 1,
                _move=move_uci,
            )

        # Calculate the strength for this move
        move_node.strength = estimate_strength(new_board)

        # Add it to the tree
        tree.add_child(move_node)

    return tree


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
