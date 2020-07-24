#!/bin/bash

function get_count() {
  echo $(grep "definition_${1}\">\(.*\[AUTOTRANSLATED\]\)\?<" mem-* | wc -l)
}

DE_COUNT=$(get_count "de")
FA_COUNT=$(get_count "fa")
RU_COUNT=$(get_count "ru")
SV_COUNT=$(get_count "sv")
ZH_HK_COUNT=$(get_count "zh_HK")
PT_COUNT=$(get_count "pt")

# Note: These are sorted in order of completeness.
echo "Remaining entries:"
echo "de: $DE_COUNT"
echo "pt: $PT_COUNT"
echo "sv: $SV_COUNT"
echo "ru: $RU_COUNT"
echo "zh-HK: $ZH_HK_COUNT"
echo "fa: $FA_COUNT"
