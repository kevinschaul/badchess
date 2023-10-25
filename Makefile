.PHONY: run-xboard
run-xboard:
	xboard -fcp badchess/main.py -fd . -fUCI -adapterCommand 'polyglot -noini -ec "%fcp" -ed "%fd" -log true'

.PHONY: run-lichess
run-lichess:
	cd lichess-bot && python lichess-bot.py --config ../lichess-bot-config.yml

.PHONY: benchmark
benchmark:
	pytest badchess/test/test_benchmark.py \
		--benchmark-min-rounds=20 \
		--benchmark-autosave
