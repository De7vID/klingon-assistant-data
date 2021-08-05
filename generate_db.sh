#!/bin/bash

# Get the directory with the original data.
SOURCE_DIR=$PWD

# Sanity check that the export to Anki script isn't broken.
# TODO: Check not only that the script succeeds, but that the output is as
# expected.
./export_to_anki.py --test > /dev/null
if [[ ! $? = 0 ]]; then
    echo "Anki export is broken."
    exit
fi

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

# Check whether qawHaq.db exists and is at least as new as the source files.
ALREADY_UP_TO_DATE=true
if [[ ! -f $SOURCE_DIR/qawHaq.db ]]; then
    ALREADY_UP_TO_DATE=
else
    for f in $SOURCE_DIR/mem-*.xml
    do
        [[ "$f" -nt $SOURCE_DIR/qawHaq.db ]] && ALREADY_UP_TO_DATE=
    done
    [[ $SOURCE_DIR/VERSION -nt $SOURCE_DIR/qawHaq.db ]] && ALREADY_UP_TO_DATE=
fi
if [[ $ALREADY_UP_TO_DATE ]] && [[ ! $XMLONLY ]]
then
    echo "qawHaq.db is up-to-date."
    exit
fi
if [[ ! $XMLONLY ]]
then
    echo "Generating qawHaq.db."
else
    echo "Generating mem.xml."
fi

# Check for MacOS and use GNU-sed if detected.
if [[ "$(uname -s)" = "Darwin" ]]
then
    SED=gsed
else
    SED=sed
fi

# Copy files into temporary directory, renumber, and concatenate data into one
# xml file.
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp/}klingon-assistant-data.XXXXXXXX")
cp $SOURCE_DIR/mem-*.xml $TMP_DIR
cp $SOURCE_DIR/clear_autotranslated_notes.sh $TMP_DIR
cp $SOURCE_DIR/renumber.py $TMP_DIR
cd $TMP_DIR
./clear_autotranslated_notes.sh
./renumber.py
cat mem-00-header.xml mem-01-b.xml mem-02-ch.xml mem-03-D.xml mem-04-gh.xml mem-05-H.xml mem-06-j.xml mem-07-l.xml mem-08-m.xml mem-09-n.xml mem-10-ng.xml mem-11-p.xml mem-12-q.xml mem-13-Q.xml mem-14-r.xml mem-15-S.xml mem-16-t.xml mem-17-tlh.xml mem-18-v.xml mem-19-w.xml mem-20-y.xml mem-21-a.xml mem-22-e.xml mem-23-I.xml mem-24-o.xml mem-25-u.xml mem-26-suffixes.xml mem-27-extra.xml mem-28-examples.xml mem-29-footer.xml > $TMP_DIR/mem.xml
cp $TMP_DIR/EXTRA $SOURCE_DIR
cd $SOURCE_DIR

# Write the ID of the first entry in the "extra" section to the KlingonContentDatabase.java file.
JAVA_FILE="$SOURCE_DIR/../app/src/main/java/org/tlhInganHol/android/klingonassistant/KlingonContentDatabase.java"
if [[ ! -f $JAVA_FILE ]]; then
    echo "Info: KlingonContentDatabase.java not updated."
else
    ${SED} -i -e "s/\(private static final int ID_OF_FIRST_EXTRA_ENTRY = \).*;/\1$(cat EXTRA);/" $JAVA_FILE
fi

# We only want the xml file for debugging purposes, so stop.
if [[ $XMLONLY ]]
then
    cp $TMP_DIR/mem.xml $SOURCE_DIR
    exit
fi

# Ensure entries are numbered first.
MISSING_IDS=$(grep "_id\"><" $TMP_DIR/mem.xml)
if [[ ! -z "$MISSING_IDS" ]]
then
    echo "Missing IDs: run renumber.py."
    echo
    exit
fi

# Write database version number.
VERSION=$(cat VERSION)
echo Writing database version $VERSION...
${SED} -i -e "s/\[\[VERSION\]\]/$VERSION/" $TMP_DIR/mem.xml

# Convert from xml to sql instructions.
./xml2sql.pl $TMP_DIR > $TMP_DIR/mem.sql
${SED} -i -e 's/INSERT INTO "mem"/INSERT INTO mem/g' $TMP_DIR/mem.sql

# Print any entries with duplicate columns.
grep "ARRAY" $TMP_DIR/mem.sql

# Print any parts of speech accidentally entered into the definition.
POS_DEFINITION_MIXUP=$(grep -B2 "definition\">\(v\|n\|adv\|conj\|ques\|sen\|excl\)[:<]" $TMP_DIR/mem.xml)
if [[ ! -z "$POS_DEFINITION_MIXUP" ]]
then
    echo "Part of speech information entered into definition:"
    echo "$POS_DEFINITION_MIXUP"
    echo
fi

# Print any empty German definitions.
MISSING_DE=$(grep -B3 "definition_de\"><" $TMP_DIR/mem.xml | grep "entry_name")
if [[ ! -z "$MISSING_DE" ]]
then
    echo "Missing German definitions:"
    echo "$MISSING_DE"
    echo
fi

# Print any empty Portuguese definitions.
MISSING_PT=$(grep -B8 "definition_pt\"><" $TMP_DIR/mem.xml | grep "entry_name")
if [[ ! -z "$MISSING_PT" ]]
then
    echo "Missing Portuguese definitions:"
    echo "$MISSING_PT"
    echo
fi

# Print any empty Finnish definitions.
MISSING_FI=$(grep -B8 "definition_fi\"><" $TMP_DIR/mem.xml | grep "entry_name")
if [[ ! -z "$MISSING_FI" ]]
then
    echo "Missing Finnish definitions:"
    echo "$MISSING_FI"
    echo
fi

# Print any untranslated entries.
MISSED_TRANSLATE=$(grep ">TRANSLATE<" $TMP_DIR/mem.xml)
if [[ ! -z "$MISSED_TRANSLATE" ]]
then
    echo "Missing translations:"
    echo "$MISSED_TRANSLATE"
    echo
fi

# Print any mistyped colons.
COLON_TYPO=$(grep ";[nv]" $TMP_DIR/mem.xml)
if [[ ! -z "$COLON_TYPO" ]]
then
    echo "Mistyped colon:"
    echo "$COLON_TYPO"
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

# Print any sources which are not empty but don't begin with "[".
MISSED_SOURCE_BRACKET=$(grep "source\">[^\[<]" $TMP_DIR/mem.xml)
if [[ ! -z "$MISSED_SOURCE_BRACKET" ]]
then
    echo "Missing source index:"
    echo "$MISSED_SOURCE_BRACKET"
    echo
fi

# Pause (in case of error).
if [[ ! $NONINTERACTIVE && (! -z "$POS_DEFINITION_MIXUP" || ! -z "$MISSING_DE" || ! -z "$MISSING_PT" || ! -z "$BROKEN_REFERENCES") ]]
then
    read -n1 -r -p "Press any key to continue..."
    echo
fi

# Create db binary.
if [[ -f $SOURCE_DIR/qawHaq.db ]]
then
    if [[ ! $NONINTERACTIVE ]]
    then
        # If the db already exists, show a diff.
        sqlite3 $SOURCE_DIR/qawHaq.db .dump > $TMP_DIR/old-mem.sql
        ${SED} -i -e 's/INSERT INTO "mem"/INSERT INTO mem/g' $TMP_DIR/old-mem.sql
        # This is necessary after sqlite3 v3.19.
        # See: https://stackoverflow.com/questions/44989176/sqlite3-dump-inserts-replace-function-in-dump-change-from-3-18-to-3-19
        ${SED} -i -e "s/replace(//g" $TMP_DIR/old-mem.sql
        ${SED} -i -e "s/,'\\\\n',char(10))//g" $TMP_DIR/old-mem.sql
        ${SED} -i -e "s/\\\\n/\n/g" $TMP_DIR/old-mem.sql
        vimdiff $TMP_DIR/old-mem.sql $TMP_DIR/mem.sql
        read -n1 -r -p "Press any key to generate new db..."
        echo
    fi
    mv $SOURCE_DIR/qawHaq.db $TMP_DIR/qawHaq.db~
fi
sqlite3 $SOURCE_DIR/qawHaq.db < $TMP_DIR/mem.sql

# Sanity check.
# TODO: Refactor the creation of old-mem.sql and sanity.sql into function.
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
fi

# Pause (in case of error).
if [[ ! $NONINTERACTIVE ]]
then
    read -n1 -r -p "Press any key to delete temporary files..."
    echo
fi

# Clean up temporary files.
rm -R $TMP_DIR
