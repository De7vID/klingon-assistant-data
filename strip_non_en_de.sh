#!/bin/bash
# Check for MacOS and use GNU-sed if detected.
if [[ "$(uname -s)" = "Darwin" ]]
then
    SED=gsed
else
    SED=sed
fsedi

${SED} -i -E ':a;N;$!ba;s:      <column name="[^"]*_(fa|sv|ru|zh_HK|pt|fi)">[^<]*</column>\n::g' mem-*.xml
