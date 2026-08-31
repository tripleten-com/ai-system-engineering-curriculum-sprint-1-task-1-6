#!/usr/bin/env sh
# Coldline - Task 1.1
# File: infra/scripts/bootstrap.sh
# Component: POSIX bootstrap wrapper
# Purpose: Run the shared Python bootstrap from a POSIX shell.
# Interacts With: infra/scripts/bootstrap.py
# Sprint/Task: Sprint 1 - Project 1 / Task 1.1
# Concepts: Cross-platform setup
# Tools: POSIX shell, Python 3.12

set -eu
python infra/scripts/bootstrap.py
export PATH="$PWD/.tools/bin:$PATH"
uv sync --frozen
