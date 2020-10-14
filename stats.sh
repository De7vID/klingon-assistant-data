#!/bin/bash

function get_count() {
  echo $(grep "definition_${1}\">\(.*\[AUTOTRANSLATED\]\)\?<" mem-*.xml | wc -l)
}

# Note: These are in the order the languages were added.
DE_COUNT=$(get_count "de")
FA_COUNT=$(get_count "fa")
RU_COUNT=$(get_count "ru")
SV_COUNT=$(get_count "sv")
ZH_HK_COUNT=$(get_count "zh_HK")
PT_COUNT=$(get_count "pt")
FI_COUNT=$(get_count "fi")

# Note: These are sorted in (approximate) order of completeness.
echo "Remaining entries:"
echo "de: $DE_COUNT"
echo "pt: $PT_COUNT"
echo "fi: $FI_COUNT"
echo "sv: $SV_COUNT"
echo "ru: $RU_COUNT"
echo "zh-HK: $ZH_HK_COUNT"
echo "fa: $FA_COUNT"
