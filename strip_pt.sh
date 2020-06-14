#!/bin/bash
sed -i -E ':a;N;$!ba;s:      <column name="[^"]*_pt">[^<]*</column>\n::g' mem-*.xml
