#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
"${PYTHON_EXE:-python3}" scripts/create_vfs.py
for name in minimal several deep; do
    ./run.sh --vfs "data/$name.zip" --script scripts/vfs_smoke.txt
done
if ./run.sh --vfs data/missing.zip --script scripts/vfs_smoke.txt; then
    exit 1
fi
if ./run.sh --vfs data/invalid.zip --script scripts/vfs_smoke.txt; then
    exit 1
fi
