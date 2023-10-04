# badchess

A bad chess engine for learning. Implements the [UCI Protocol](https://backscattering.de/chess/uci/) for communication with chess GUIs.

Currently just plays a random legal move!

## Installation

Clone this repo, including git submodules:

    git clone --recurse-submodules https://github.com/chaconinc/MainProject

Install the python dependencies (I use pyenv, but adapt as you wish):

    pyenv virtualenv badchess
    pyenv local badchess
    pip install -r requirements.txt

## Usage

### Locally, in `xboard`

You can play against the engine in `xboard`, a chess GUI. From this repo's directory, start `xboard` with the following arguments:

    xboard -fcp badchess/badchess.py -fd . -fUCI

### As a bot on lichess.org

You can also set up your engine as a bot in [lichess](https://lichess.org). The engine will run on your computer but communicate

1. Make sure you have the files within the git submodule `lichess-bot/`. If not, try `git submodule update --init`.
2. cd into the lichess-bot directory: `cd lichess-bot`
3. Create a [lichess OAuth token](https://github.com/lichess-bot-devs/lichess-bot/wiki/How-to-create-a-Lichess-OAuth-token), storing the token as environment variable `LICHESS_BOT_TOKEN`.
4. Update your lichess account to a bot account by running `python lichess-bot.py -u`
5. Run the bot using the provided configuration file: `python lichess-bot.py --config ../lichess-bot-config.yml`
6. You should be able to find your bot on lichess.org and challenge it!


