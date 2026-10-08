#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export PR13_DIR=/docs
"${PYTHON_EXE:-python3}" scripts/create_vfs.py
./run.sh --vfs data/deep.zip --script scripts/stage4_ok.txt
./run.sh --vfs data/deep.zip --script scripts/stage5_ok.txt
for script in scripts/errors/*.txt scripts/stage5_error.txt; do
    if ./run.sh --vfs data/deep.zip --script "$script"; then
        exit 1
    fi
done
