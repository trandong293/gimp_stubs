#!/usr/bin/env sh

python main.py
ruff check --select I --fix
ruff format

./post.sh
