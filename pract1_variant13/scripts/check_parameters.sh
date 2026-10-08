#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export PR13_DIR=/docs
"${PYTHON_EXE:-python3}" scripts/create_vfs.py
./run.sh --vfs data/deep.zip --script scripts/vfs_smoke.txt
./run.sh --vfs "data/path with spaces.zip" --script scripts/vfs_smoke.txt
printf 'exit\n' | ./run.sh --vfs data/deep.zip
if ./run.sh --script scripts/vfs_smoke.txt; then
    exit 1
fi
if ./run.sh --vfs data/deep.zip --script scripts/no_such_script.txt; then
    exit 1
fi
if ./run.sh --vfs data/deep.zip --script scripts/stage2_error.txt; then
    exit 1
fi
