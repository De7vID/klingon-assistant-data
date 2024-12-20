#!/bin/bash

# Determine parameters.
if [[ $# -eq 0 ]]
then
    echo "Usage: `basename $0` language [commit]"
    echo "If commit is omitted, will default to upstream/main."
    exit
fi
if [[ ! "$1" =~ ^(de|fa|sv|ru|zh_HK|pt|fi|fr)$ ]]
then
    echo "Unsupported language: $1"
    exit
fi
LANGUAGE=$1
if [[ "$2" = "" ]]
then
    echo "Comparing changes against upstream/main."
    COMMIT=$(git rev-parse upstream/main)
else
    echo "Comparing changes against commit $2"
    COMMIT=$2
fi

# Display diff.
git diff --no-ext-diff ${COMMIT} mem-*.xml | grep -P "^(\+\+\+|\+.*\"(definition|notes)_${LANGUAGE}\")"
