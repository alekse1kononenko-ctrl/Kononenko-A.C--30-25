#!/bin/sh
set -eu
if [ "$#" -ne 2 ]; then
    echo 'Usage: demo_smoke.sh PATH_TO_EXECUTABLE EVIDENCE_DIRECTORY' >&2
    exit 2
fi
app=$1
output=$2
mkdir -p "$output"
profile=$(mktemp -d "$output/profile.XXXXXXXX")
"$app" --scenario first --save "$profile/shop.json" --screens "$output"
"$app" --scenario restore --save "$profile/shop.json" --screens "$output"
printf '%s' 'broken-json' > "$profile/damaged.json"
"$app" --scenario damaged --save "$profile/damaged.json" --screens "$output"
test "$(cat "$profile/damaged.json")" = 'broken-json'
