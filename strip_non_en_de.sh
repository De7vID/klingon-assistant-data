#!/bin/bash
sed -i -E ':a;N;$!ba;s:      <column name="[^"]*_(fa|sv|ru|zh_HK|pt|fi)">[^<]*</column>\n::g' mem-*.xml
