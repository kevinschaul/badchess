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

    moves_list = minimax(move_tree, board.turn == chess.WHITE)
    logging.info(f"moves_list: {moves_list}")
    return moves_list[0]


def get_tree_max(move_tree: Tree):
    """
    Finds the child node with the maximum strength. Returns a tuple with its
    strength an a list of node indices at that strength.
    """
    # Find the minimum strength
    max_strength = -inf
    for i, move in enumerate(move_tree.children):
        if move.strength >= max_strength:
            max_strength = move.strength

    # Then return all nodes that produce that minimum strength
    max_indices = []
    for i, move in enumerate(move_tree.children):
        if move.strength == max_strength:
            max_indices.append(i)
    return (max_strength, max_indices)


def get_tree_min(move_tree: Tree):
    """
    Finds the child node with the minimum strength. Returns a tuple with its
    strength an a list of node indices at that strength.

    Finds the child node with the minimum strength, and returns its strength and its index
    """
    # Find the minimum strength
    min_strength = inf
    for i, move in enumerate(move_tree.children):
        if move.strength <= min_strength:
            min_strength = move.strength

    # Then return all nodes that produce that minimum strength
    min_indices = []
    for i, move in enumerate(move_tree.children):
        if move.strength == min_strength:
            min_indices.append(i)
    return (min_strength, min_indices)


def minimax(move_tree: Tree, is_cur_move_white: bool):
    """
    Returns a list of moves that are estimated to be the best,
    by maximizing strength for white and minimizing strength for
    black (or the reverse, if `is_cur_move_white` is False).
    """
    return _minimax(move_tree, [], is_cur_move_white)[1]


def _minimax(move_tree: Tree, moves_list: list[str], is_cur_move_white: bool, depth=0):
    indent = '\t' * depth
    # logging.debug(
    #     f"{indent}_minimax depth: {depth}, moves_list: {moves_list}, is_cur_move_white: {is_cur_move_white}"
    # )
    moves_list = moves_list.copy()
    cur_move_tree = move_tree
    for move in moves_list:
        cur_move_tree = cur_move_tree.get_child(move)
        # logging.debug(f"{indent} cur_move_tree: {cur_move_tree}")
        if not cur_move_tree:
            raise KeyError

    # Base case. We know the strength.
    if not cur_move_tree.children:
        # logging.debug(f"{indent} base case!")
        # logging.debug(f"{indent} returning ({cur_move_tree.strength}, {moves_list})")
        return (cur_move_tree.strength, moves_list)

    else:
        # logging.debug(f"{indent} else case!")
        possible_moves = []
        for move in cur_move_tree.children:
            next_moves_list = moves_list.copy()
            next_moves_list.append(move.name)
            possible_moves.append(
                _minimax(move_tree, next_moves_list, not is_cur_move_white, depth=depth + 1)
            )
            # logging.debug(f"{indent} possible_moves: {possible_moves}")

        if is_cur_move_white:
            # Find the max strength
            # best_move = sorted(possible_moves, key=lambda x: x[0], reverse=True)[0]
            best_move = random.choice(max_strength_moves(possible_moves))
            # logging.info(f"{indent} white best_move: {best_move}")
        else:
            # Find the min strength
            best_move = random.choice(min_strength_moves(possible_moves))
            # logging.info(f"{indent} black best_move: {best_move}")
        return best_move


def max_strength_moves(moves):
    """
    Returns a list of moves with the maximum strength, including ties.
    moves is a tuple containing the strength and move sequence.
    """
    moves_sorted = sorted(moves, key=lambda x: x[0], reverse=True)
    return [move for move in moves_sorted if move[0] == moves_sorted[0][0]]


def min_strength_moves(moves):
    """
    Returns a list of moves with the minimum strength, including ties.
    moves is a tuple containing the strength and move sequence.
    """
    moves_sorted = sorted(moves, key=lambda x: x[0], reverse=False)
    return [move for move in moves_sorted if move[0] == moves_sorted[0][0]]


def build_move_tree(board: chess.Board, depth=1):
    if depth > MAX_DEPTH:
        raise ValueError(f"Depth > {MAX_DEPTH} is asking for trouble")
    return _build_move_tree(board, depth=depth)


def _build_move_tree(board: chess.Board, depth=1, _current_depth=1, _move="root"):
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
