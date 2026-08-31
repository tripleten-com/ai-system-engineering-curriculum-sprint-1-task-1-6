#!/usr/bin/env sh
# Coldline - Task 1.1
# File: infra/scripts/preflight.sh
# Component: POSIX preflight wrapper
# Purpose: Run environment checks from a POSIX shell.
# Interacts With: infra/scripts/preflight.py
# Sprint/Task: Sprint 1 - Project 1 / Task 1.1
# Concepts: Early failure reporting
# Tools: POSIX shell, Python 3.12

set -eu
export PATH="$PWD/.tools/bin:$PATH"
python infra/scripts/preflight.py
