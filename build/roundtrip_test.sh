#!/bin/bash
#
# CI test: the XML and YAML pipelines must produce the same database.
#
# Both `generate_db.sh` (from mem-*.xml) and `generate_db_yaml.sh` (from
# entries/*.yaml) write ``qawHaq.db`` and ``EXTRA`` at the repo root.
# If either drifts, the app's data becomes format-dependent. This test
# runs both and diffs a canonical SQL dump plus the EXTRA file, so any
# real divergence fails CI.

set -euo pipefail

cd "$(dirname "$0")/.."
SOURCE_DIR=$PWD
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/klingon-roundtrip.XXXXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

dump_db() {
    # sqlite3 .dump output is deterministic for a fixed row order.
    # Both pipelines feed rows in `_id` order, so dumps must match byte-for-byte.
    sqlite3 "$1" .dump > "$2"
}

# The "up-to-date" shortcuts in both scripts skip regeneration when
# qawHaq.db is newer than the sources. Force a full build by deleting it.
rm -f "$SOURCE_DIR/qawHaq.db" "$SOURCE_DIR/EXTRA"

echo "==> Running XML pipeline (generate_db.sh)"
"$SOURCE_DIR/generate_db.sh" --noninteractive
dump_db "$SOURCE_DIR/qawHaq.db" "$TMP_DIR/xml.sql"
cp "$SOURCE_DIR/EXTRA" "$TMP_DIR/xml.EXTRA"

# Delete so the YAML pipeline doesn't skip via its mtime shortcut.
rm -f "$SOURCE_DIR/qawHaq.db" "$SOURCE_DIR/EXTRA"

echo "==> Running YAML pipeline (generate_db_yaml.sh)"
"$SOURCE_DIR/generate_db_yaml.sh" --noninteractive
dump_db "$SOURCE_DIR/qawHaq.db" "$TMP_DIR/yaml.sql"
cp "$SOURCE_DIR/EXTRA" "$TMP_DIR/yaml.EXTRA"

echo "==> Comparing SQL dumps"
if ! diff -u "$TMP_DIR/xml.sql" "$TMP_DIR/yaml.sql" > "$TMP_DIR/sql.diff"; then
    echo "FAIL: SQL dumps differ between XML and YAML pipelines" >&2
    head -50 "$TMP_DIR/sql.diff" >&2
    echo "(showing first 50 lines; full diff in $TMP_DIR/sql.diff)" >&2
    exit 1
fi

echo "==> Comparing EXTRA"
if ! diff -u "$TMP_DIR/xml.EXTRA" "$TMP_DIR/yaml.EXTRA"; then
    echo "FAIL: EXTRA differs between XML and YAML pipelines" >&2
    exit 1
fi

echo "==> Also checking build/renumber_yaml.py --check"
python3 "$SOURCE_DIR/build/renumber_yaml.py" --check

echo "PASS: XML and YAML pipelines produce identical output"
