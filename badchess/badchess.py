#!/usr/bin/env python

from concurrent.futures import ThreadPoolExecutor
import logging
import random
import selectors
import sys
import queue

import chess

logging.basicConfig(
    filename="badchess.log",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s %(message)s",
)

should_exit = False


def producer(q):
    """
    Read a line from stdin. Check to see whether we should exit every second.
    """

    def read_input(stdin, mask):
        line = stdin.readline()
        if not line:
            sel.unregister(sys.stdin)
            return None
        else:
            return line.strip()

    sel = selectors.DefaultSelector()
    sel.register(sys.stdin, selectors.EVENT_READ, read_input)

    while not should_exit:
        logging.debug(f"Producer: {should_exit}")
        for key, events in sel.select(timeout=1):
            callback = key.data
            line = callback(sys.stdin, events)
            if line:
                q.put(line)
                logging.debug(f"Producer: {line}")
    logging.debug(f"Producer done")


def consumer(q, board, i):
    while not should_exit:
        logging.debug(f"Consumer {i}: {should_exit}")
        try:
            line = q.get(timeout=1)
            if line:
                logging.debug(f"Consumer: {line}")
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
    move = find_best_move(board)
    send_command(f"bestmove {move.uci()}")


def process_stop(words, board):
    # TODO stop other consumer threads
    pass


def process_quit(words, board):
    global should_exit
    should_exit = True
    logging.debug(f"exit set")


def find_best_move(board):
    move = random.choice([move for move in board.legal_moves])
    return move


def main():
    q = queue.Queue()
    board = chess.Board()

    n_consumers = 2

    with ThreadPoolExecutor(max_workers=n_consumers + 1) as executor:
        executor.submit(producer, q)
        [executor.submit(consumer, q, board, i) for i in range(n_consumers)]


if __name__ == "__main__":
    main()
