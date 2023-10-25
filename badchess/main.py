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

import chess

from badchess.tree import Tree

logging.basicConfig(
    filename="badchess.log",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s %(message)s",
)

should_exit = False

MAX_DEPTH = 4


def producer(q):
    """
    Read a line from stdin, in a non-blocking way -- waiting at most
    1 second per call. Put any input lines into the queue.
    """
    lines = readlines_with_timeout(1)
    for line in lines:
        q.put(line)
        logging.debug(f"Producer: {line}")


def readlines_with_timeout(timeout):
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


def consumer(q, board, i):
    while not should_exit:
        try:
            line = q.get(timeout=1)
            if line:
                process_command(line, board)
        except queue.Empty:
            pass
    logging.debug(f"Consumer {i} done")


def send_command(command):
    logging.debug(f"Command sent: {command}")
    sys.stdout.write(f"{command}\n")
    sys.stdout.flush()


def process_command(command, board):
    logging.debug(f"Command received: {command}")
    words = command.strip().split(" ")

    if words[0] == "uci":
        process_uci(words, board)
    elif words[0] == "setoption":
        process_setoption(words, board)
    elif words[0] == "isready":
        process_isready(words, board)
    elif words[0] == "ucinewgame":
        process_ucinewgame(words, board)
    elif words[0] == "position":
        process_position(words, board)
    elif words[0] == "go":
        process_go(words, board)
    elif words[0] == "stop":
        process_stop(words, board)
    elif words[0] == "quit":
        process_quit(words, board)


def process_setoption(words, board):
    logging.warning("setoption ignored")


def process_uci(words, board):
    send_command("id name badchess")
    send_command("id author Kevin Schaul")
    send_command("uciok")


def process_isready(words, board):
    send_command("readyok")


def process_ucinewgame(words, board):
    board.reset()


def process_position(words, board):
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


def process_go(words, board):
    move = find_best_move(board, depth=3)
    send_command(f"bestmove {move}")


def process_stop(words, board):
    # TODO stop other consumer threads
    pass


def process_quit(words, board):
    global should_exit
    should_exit = True
    logging.debug(f"exit set")


def find_best_move(board, depth=3) -> chess.Move:
    # Build out a move tree
    move_tree = build_move_tree(board, depth=depth)

    # Add strength estimates to each move
    add_strength_to_tree(board, move_tree, depth=depth)

    moves_list = minimax(move_tree)
    logging.info(f"moves_list: {moves_list}")
    return moves_list[0]


def get_tree_max(move_tree: Tree):
    """
    Finds the child node with the maximum strength. Returns a tuple with its
    strength an a list of node indices at that strength.
    """
    max_strength = -inf
    max_indices = []
    for i, move in enumerate(move_tree.children):
        if move.data["strength"] >= max_strength:
            max_strength = move.data["strength"]
            max_indices.append(i)
    return (max_strength, max_indices)


def get_tree_min(move_tree: Tree):
    """
    Finds the child node with the minimum strength. Returns a tuple with its
    strength an a list of node indices at that strength.

    Finds the child node with the minimum strength, and returns its strength and its index
    """
    min_strength = inf
    min_indices = []
    for i, move in enumerate(move_tree.children):
        if move.data["strength"] < min_strength:
            min_strength = move.data["strength"]
            min_indices.append(i)
    return (min_strength, min_indices)


def minimax(move_tree: Tree):
    moves_list = []
    is_cur_move_white = True
    cur_tree = move_tree
    cur_depth = 1

    while len(cur_tree.children):
        if is_cur_move_white:
            best_moves = get_tree_max(cur_tree)
        else:
            best_moves = get_tree_min(cur_tree)

        move = random.choice(best_moves[1])
        cur_tree = cur_tree.children[move]
        moves_list.append(cur_tree.name)

        is_cur_move_white = not is_cur_move_white
        cur_depth += 1

    return moves_list


def build_move_tree(board: chess.Board, depth=1):
    if depth > MAX_DEPTH:
        raise ValueError(f"Depth > {MAX_DEPTH} is asking for trouble")
    return _build_move_tree(board, depth=depth)


def _build_move_tree(board: chess.Board, depth=1, _current_depth=1, _move="root"):
    tree = Tree(name=_move)

    for move in board.legal_moves:
        if _current_depth == depth:
            tree.add_child(Tree(name=move.uci()))
        else:
            new_board = board.copy(stack=False)
            new_board.push_uci(move.uci())

            tree.add_child(
                _build_move_tree(
                    new_board,
                    depth=depth,
                    _current_depth=_current_depth + 1,
                    _move=move.uci(),
                )
            )

    return tree


def add_strength_to_tree(board: chess.Board, tree: Tree, depth=1):
    if depth > MAX_DEPTH:
        raise ValueError(f"Depth > {MAX_DEPTH} is asking for trouble")
    _add_strength_to_tree(board, tree, depth=depth)


def _add_strength_to_tree(board: chess.Board, tree: Tree, depth=1, _current_depth=1):
    for move in tree.children:
        new_board = board.copy(stack=False)
        new_board.push_uci(move.name)
        move.data = {"strength": estimate_strength(new_board)}

        if _current_depth < depth:
            _add_strength_to_tree(
                new_board, move, depth=depth, _current_depth=_current_depth + 1
            )


def estimate_strength(board: chess.Board):
    """
    Estimate the strength of the board, from white's position.
    """
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
