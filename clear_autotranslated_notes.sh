#!/bin/bash
sed -i -E ':a;N;$!ba;s:<column name="notes_([^"]*)">[^<]* \[AUTOTRANSLATED\]</column>:<column name="notes_\1"></column>:g' mem-*.xml
