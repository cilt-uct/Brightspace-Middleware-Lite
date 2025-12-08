#! /bin/bash

source base.sh

pre-commit &&
python -m ruff check .
# python -m ruff format --check .
