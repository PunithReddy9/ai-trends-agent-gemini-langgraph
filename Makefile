.PHONY: help install run clean lint format

# Default target executed when no arguments are given to make.
all: help

######################
# SETUP AND RUN
######################

install:
	pip install -r requirements.txt

run:
	python run_report.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

######################
# DEVELOPMENT
######################

lint:
	python -m flake8 src/ --max-line-length=100
	python -m mypy src/ --ignore-missing-imports

format:
	python -m black src/ --line-length=100
	python -m isort src/

######################
# HELP
######################

help:
	@echo 'AI Trends Reporter - Available Commands:'
	@echo '----'
	@echo 'install                      - install Python dependencies'
	@echo 'run                          - generate AI trends report'
	@echo 'clean                        - remove Python cache files'
	@echo 'lint                         - run code linters'
	@echo 'format                       - run code formatters'
	@echo '----'
	@echo 'Usage: make <command>'

