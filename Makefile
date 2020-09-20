
PYTHON = python3

example-2: examples/example-2.json examples/ex02.TON
	$(PYTHON) ac7maker.py examples/example-2.json examples/Ex02.AC7


run_tests: example-2

all: run_tests

PHONY: all run_tests example-2
