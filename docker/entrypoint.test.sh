#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running test suite..."

exec pytest --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml -v