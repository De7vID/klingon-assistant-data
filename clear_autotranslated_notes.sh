#!/bin/bash
# Check for MacOS and use GNU-sed if detected.
if [[ "$(uname -s)" = "Darwin" ]]
then
    SED=gsed
else
    SED=sed
fi

${SED} -i -E ':a;N;$!ba;s:<column name="notes_([^"]*)">[^<]* \[AUTOTRANSLATED\]</column>:<column name="notes_\1"></column>:g' mem-*.xml
