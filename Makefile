.PHONY: run-xboard
run-xboard:
	xboard -fcp badchess/main.py -fd . -fUCI -adapterCommand 'polyglot -noini -ec "%fcp" -ed "%fd" -log true'

.PHONY: run-lichess
run-lichess:
	cd lichess-bot && python lichess-bot.py --config ../lichess-bot-config.yml

.PHONY: benchmark-speed
benchmark-speed:
	pytest badchess/benchmark/speed \
		--benchmark-min-rounds=20 \
		--benchmark-autosave

.PHONY: benchmark-memory
benchmark-memory:
	pytest badchess/benchmark/memory --memray \
		--stacks 1 > badchess/benchmark/memory/result.txt
