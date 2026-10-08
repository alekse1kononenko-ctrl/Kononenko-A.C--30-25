#!/bin/sh
set -eu
cd "$(dirname "$0")/pract1_variant13"
exec "${PYTHON_EXE:-python3}" -m src.main "$@"
