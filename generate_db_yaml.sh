#!/bin/bash

# generate_db_yaml.sh
#
# Generate qawHaq.db and qawHaq.json from YAML source files.
# This is the new YAML-based pipeline that will eventually replace generate_db.sh.
#
# Usage:
#   ./generate_db_yaml.sh [--noninteractive]
#
# The --noninteractive flag skips all prompts and diffs (for automated builds).

# Get the directory with the original data.
cd "$(dirname "$0")"
SOURCE_DIR=$PWD

# Check for non-interactive mode flag.
if [[ "$1" = "--noninteractive" ]]
then
    NONINTERACTIVE=true
    shift
fi

# Check for MacOS and use GNU-sed if detected.
if [[ "$(uname -s)" = "Darwin" ]]
then
    SED=gsed
else
    SED=sed
fi

# Check whether qawHaq.db exists and is at least as new as the YAML source files.
ALREADY_UP_TO_DATE=true
if [[ ! -f $SOURCE_DIR/qawHaq.db ]]; then
    ALREADY_UP_TO_DATE=
else
    # Check if any YAML file is newer than the database
    NEWEST_YAML=$(find $SOURCE_DIR/entries -name "*.yaml" -newer $SOURCE_DIR/qawHaq.db 2>/dev/null | head -1)
    if [[ ! -z "$NEWEST_YAML" ]]; then
        ALREADY_UP_TO_DATE=
    fi
    # Also check VERSION file
    [[ $SOURCE_DIR/VERSION -nt $SOURCE_DIR/qawHaq.db ]] && ALREADY_UP_TO_DATE=
fi

if [[ $ALREADY_UP_TO_DATE ]]
then
    echo "qawHaq.db is up-to-date."
    exit
fi

echo "Generating qawHaq.db from YAML sources."

# Create temporary directory
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/klingon-assistant-yaml.XXXXXXXX")

# Read version
VERSION=$(cat VERSION)
echo "Database version: $VERSION"

# Track if any warnings are displayed.
HAS_WARNINGS=

# ==============================================================================
# Generate SQL from YAML
# ==============================================================================

echo "Generating SQL from YAML..."
python3 $SOURCE_DIR/build/yaml2sql.py > $TMP_DIR/mem.sql 2>$TMP_DIR/yaml2sql.err

if [[ $? -ne 0 ]]; then
    echo "Error running yaml2sql.py:"
    cat $TMP_DIR/yaml2sql.err
    exit 1
fi

# Show any stderr output (entry count, etc.)
if [[ -s $TMP_DIR/yaml2sql.err ]]; then
    cat $TMP_DIR/yaml2sql.err
fi

# Apply version substitution to SQL
${SED} -i -e "s/\[\[VERSION\]\]/$VERSION/g" $TMP_DIR/mem.sql

# Normalize INSERT format to match expected output
${SED} -i -e 's/INSERT INTO "mem"/INSERT INTO mem/g' $TMP_DIR/mem.sql

# ==============================================================================
# Validation checks (adapted from generate_db.sh)
# ==============================================================================

echo "Running validation checks..."

# Check for duplicate columns (ARRAY in Perl output indicates duplicates)
DUPLICATE_COLUMNS=$(grep "ARRAY" $TMP_DIR/mem.sql)
if [[ ! -z "$DUPLICATE_COLUMNS" ]]
then
    echo "Entries with duplicate columns:"
    echo "$DUPLICATE_COLUMNS"
    echo
    HAS_WARNINGS=true
fi

# Check for untranslated entries
python3 -c "
import yaml
from pathlib import Path

entries_dir = Path('$SOURCE_DIR/entries')
found = []
for yaml_file in entries_dir.rglob('*.yaml'):
    with open(yaml_file, 'r', encoding='utf-8') as f:
        content = yaml.safe_load(f)
    if not content:
        continue

    entries = []
    if 'entry' in content:
        entries = [content['entry']]
    elif 'entries' in content:
        entries = content['entries']

    for entry in entries:
        # Check all string fields for TRANSLATE
        def check_value(v, path=''):
            if isinstance(v, str) and 'TRANSLATE' in v:
                found.append(f\"{entry.get('entry_name', '?')}: {path}\")
            elif isinstance(v, dict):
                for k, sv in v.items():
                    check_value(sv, f'{path}.{k}' if path else k)
        check_value(entry)

if found:
    print('Missing translations:')
    for f in found[:20]:
        print(f'  {f}')
    if len(found) > 20:
        print(f'  ... and {len(found) - 20} more')
" 2>/dev/null
MISSED_TRANSLATE=$?
if [[ $MISSED_TRANSLATE -ne 0 ]]; then
    HAS_WARNINGS=true
fi

# ==============================================================================
# Generate JSON and validate links
# ==============================================================================

echo "Generating JSON and validating links..."
python3 $SOURCE_DIR/build/yaml2json.py > $TMP_DIR/qawHaq.json 2>$TMP_DIR/yaml2json.err

if [[ $? -ne 0 ]]; then
    echo "Error running yaml2json.py:"
    cat $TMP_DIR/yaml2json.err
    exit 1
fi

# Check for broken references (reported to stderr by yaml2json.py)
BROKEN_REFERENCES=$(grep "no entry for" $TMP_DIR/yaml2json.err | sort | uniq)
if [[ ! -z "$BROKEN_REFERENCES" ]]
then
    echo "Broken references:"
    echo "$BROKEN_REFERENCES"
    echo
    HAS_WARNINGS=true
fi

# Show other yaml2json output
grep -v "no entry for" $TMP_DIR/yaml2json.err

# ==============================================================================
# Check for warnings
# ==============================================================================

if [[ $HAS_WARNINGS ]]
then
    echo
    echo "Warnings were found. Please review the issues above."
    if [[ ! $NONINTERACTIVE ]]; then
        read -n1 -r -p "Press any key to continue anyway, or Ctrl+C to abort..."
        echo
    fi
fi

# ==============================================================================
# Pause before generating (interactive mode)
# ==============================================================================

if [[ ! $NONINTERACTIVE ]]
then
    read -n1 -r -p "Press any key to continue..."
    echo
fi

# ==============================================================================
# Create database
# ==============================================================================

if [[ -f $SOURCE_DIR/qawHaq.db ]]
then
    if [[ ! $NONINTERACTIVE ]]
    then
        # If the db already exists, show a diff.
        sqlite3 $SOURCE_DIR/qawHaq.db .dump > $TMP_DIR/old-mem.sql
        ${SED} -i -e 's/INSERT INTO "mem"/INSERT INTO mem/g' $TMP_DIR/old-mem.sql
        ${SED} -i -e "s/replace(//g" $TMP_DIR/old-mem.sql
        ${SED} -i -e "s/,'\\\\n',char(10))//g" $TMP_DIR/old-mem.sql
        ${SED} -i -e "s/\\\\n/\n/g" $TMP_DIR/old-mem.sql
        ${EDITOR:-vim} -d $TMP_DIR/old-mem.sql $TMP_DIR/mem.sql
        read -n1 -r -p "Press any key to generate new db..."
        echo
    fi
    mv $SOURCE_DIR/qawHaq.db $TMP_DIR/qawHaq.db~
fi

echo "Creating SQLite database..."
sqlite3 $SOURCE_DIR/qawHaq.db < $TMP_DIR/mem.sql

# Sanity check
sqlite3 $SOURCE_DIR/qawHaq.db .dump > $TMP_DIR/sanity.sql
${SED} -i -e 's/INSERT INTO "mem"/INSERT INTO mem/g' $TMP_DIR/sanity.sql
${SED} -i -e "s/replace(//g" $TMP_DIR/sanity.sql
${SED} -i -e "s/,'\\\\n',char(10))//g" $TMP_DIR/sanity.sql
${SED} -i -e "s/\\\\n/\n/g" $TMP_DIR/sanity.sql
IN_OUT_DIFF=$(diff $TMP_DIR/mem.sql $TMP_DIR/sanity.sql)
if [[ ! -z "$IN_OUT_DIFF" ]]
then
    echo "Sanity check failed, entries possibly missing or out of order:"
    echo "$IN_OUT_DIFF"
    echo
    echo "Temporary files: $TMP_DIR"
    echo
    exit 1
fi

# ==============================================================================
# Copy JSON output
# ==============================================================================

echo "Copying JSON output..."
# Apply version substitution to JSON
${SED} -e "s/\[\[VERSION\]\]/$VERSION/g" $TMP_DIR/qawHaq.json > $SOURCE_DIR/qawHaq.json

# ==============================================================================
# Compute EXTRA file
# ==============================================================================

# The EXTRA file contains the ID of the first entry in the "extra" section.
# This is computed from the YAML entries by finding the smallest _original_id
# among entries with section: extra.

echo "Computing EXTRA..."
EXTRA_ID=$(python3 -c "
import yaml
from pathlib import Path

entries_dir = Path('$SOURCE_DIR/entries')
extra_ids = []

for yaml_file in entries_dir.rglob('*.yaml'):
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
    except Exception:
        continue
    if not content:
        continue

    entry = content.get('entry')
    if entry and entry.get('section') == 'extra':
        extra_ids.append(entry.get('_original_id', 0))

    entries_list = content.get('entries', [])
    for entry in entries_list:
        if entry.get('section') == 'extra':
            extra_ids.append(entry.get('_original_id', 0))

if extra_ids:
    print(min(extra_ids))
else:
    print('0')
")

echo "$EXTRA_ID" > $SOURCE_DIR/EXTRA
echo "EXTRA set to $EXTRA_ID"

# ==============================================================================
# Cleanup
# ==============================================================================

if [[ ! $NONINTERACTIVE ]]
then
    read -n1 -r -p "Press any key to delete temporary files..."
    echo
fi

rm -R $TMP_DIR

echo "Done! Generated qawHaq.db and qawHaq.json from YAML sources."
echo "Entry count: $(sqlite3 $SOURCE_DIR/qawHaq.db 'SELECT COUNT(*) FROM mem')"
