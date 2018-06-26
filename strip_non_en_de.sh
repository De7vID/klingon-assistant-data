#!/bin/bash
sed -i -E ':a;N;$!ba;s:      <column name="[^"]*_(fa|sv|ru|zh_HK)">[^<]*</column>\n::g' mem-*.xml
