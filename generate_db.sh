#!/bin/bash

# Note: renumber.py must be run first.

# Check for non-interactive mode flag.
if [[ "$1" = "--noninteractive" ]]
then
    NONINTERACTIVE=true
    shift
fi

# Check for xml-only mode flag (exclusive with "--noninteractive").
if [[ "$1" = "--xmlonly" ]]
then
    XMLONLY=true
    shift
fi

# Concatenate data into one xml file.
cat mem-00-header.xml mem-01-b.xml mem-02-ch.xml mem-03-D.xml mem-04-gh.xml mem-05-H.xml mem-06-j.xml mem-07-l.xml mem-08-m.xml mem-09-n.xml mem-10-ng.xml mem-11-p.xml mem-12-q.xml mem-13-Q.xml mem-14-r.xml mem-15-S.xml mem-16-t.xml mem-17-tlh.xml mem-18-v.xml mem-19-w.xml mem-20-y.xml mem-21-a.xml mem-22-e.xml mem-23-I.xml mem-24-o.xml mem-25-u.xml mem-26-suffixes.xml mem-27-extra.xml mem-28-footer.xml > mem.xml

# Ensure entries are numbered first.
MISSING_IDS=$(grep "_id\"><" mem.xml)
if [[ ! -z "$MISSING_IDS" ]]
then
    echo "Missing IDs: run renumber.py."
    echo
    exit
fi

if [[ $XMLONLY ]]
then
    exit
fi

# Write database version number.
VERSION=$(cat VERSION)
echo Writing database version $VERSION...
sed -i -e "s/\[\[VERSION\]\]/$VERSION/" mem.xml

# Convert from xml to sql instructions.
./xml2sql.pl > mem.sql
sed -i -e 's/INSERT INTO "mem"/INSERT INTO mem/g' mem.sql

# Print any entries with duplicate columns.
grep "ARRAY" mem.sql

# Print any parts of speech accidentally entered into the definition.
POS_DEFINITION_MIXUP=$(grep -B2 "definition\">\(v\|n\|adv\|conj\|ques\|sen\|excl\)[:<]" mem.xml)
if [[ ! -z "$POS_DEFINITION_MIXUP" ]]
then
    echo "Part of speech information entered into definition:"
    echo "$POS_DEFINITION_MIXUP"
    echo
fi

# Print any empty German definitions.
MISSING_DE=$(grep -B3 "definition_de\"><" mem.xml)
if [[ ! -z "$MISSING_DE" ]]
then
    echo "Missing German definitions:"
    echo "$MISSING_DE"
    echo
fi

# Print any broken references.
BROKEN_REFERENCES=$(./xml2json.py 2> >(sort|uniq) > /dev/null)
if [[ ! -z "$BROKEN_REFERENCES" ]]
then
    echo "Broken references:"
    echo "$BROKEN_REFERENCES"
    echo
fi

# Pause (in case of error).
if [[ ! $NONINTERACTIVE && (! -z "$POS_DEFINITION_MIXUP" || ! -z "$MISSING_DE") ]]
then
    read -n1 -r -p "Press any key to continue..."
    echo
fi

# Create db binary.
if [[ -f qawHaq.db ]]
then
    if [[ ! $NONINTERACTIVE ]]
    then
        # If the db already exists, show a diff.
        sqlite3 qawHaq.db .dump > old-mem.sql
        sed -i -e 's/INSERT INTO "mem"/INSERT INTO mem/g' old-mem.sql
        # This is necessary after sqlite3 v3.19.
        # See: https://stackoverflow.com/questions/44989176/sqlite3-dump-inserts-replace-function-in-dump-change-from-3-18-to-3-19
        sed -i -e "s/replace(//g" old-mem.sql
        sed -i -e "s/,'\\\\n',char(10))//g" old-mem.sql
        sed -i -e "s/\\\\n/\n/g" old-mem.sql
        vimdiff old-mem.sql mem.sql
        read -n1 -r -p "Press any key to generate new db..."
        echo
    fi
    mv qawHaq.db qawHaq.db~
fi
sqlite3 qawHaq.db < mem.sql

# Sanity check.
# TODO: Refactor the creation of old-mem.sql and sanity.sql into function.
sqlite3 qawHaq.db .dump > sanity.sql
sed -i -e 's/INSERT INTO "mem"/INSERT INTO mem/g' sanity.sql
sed -i -e "s/replace(//g" sanity.sql
sed -i -e "s/,'\\\\n',char(10))//g" sanity.sql
sed -i -e "s/\\\\n/\n/g" sanity.sql
IN_OUT_DIFF=$(diff mem.sql sanity.sql)
if [[ ! -z "$IN_OUT_DIFF" ]]
then
    echo "Sanity check failed, entries possibly missing or out of order:"
    echo "$IN_OUT_DIFF"
    echo
fi

# Pause (in case of error).
if [[ ! $NONINTERACTIVE ]]
then
    read -n1 -r -p "Press any key to delete temporary files..."
    echo
fi

# Clean up temporary files.
rm mem.xml
rm mem.sql
rm mem_processed.xml
rm sanity.sql
rm -f old-mem.sql
rm -f qawHaq.db~
