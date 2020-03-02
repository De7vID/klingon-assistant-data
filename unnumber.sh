#!/bin/bash
# Check for MacOS and use GNU-sed if detected.
if [[ "$(uname -s)" = "Darwin" ]]
then
    SED=gsed
else
    SED=sed
fi

${SED} -i 's/"_id">.*</"_id"></g' mem-*.xml
