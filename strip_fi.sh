#!/bin/bash
sed -i -E ':a;N;$!ba;s:      <column name="[^"]*_fi">[^<]*</column>\n::g' mem-*.xml
