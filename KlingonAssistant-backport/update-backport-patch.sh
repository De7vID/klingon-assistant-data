#!/bin/sh

git status
echo
echo "Before continuing, please make sure the regular version is in a clean state,"
echo "and that the backport version has the merged changes."
read -n1 -r -p "Press any key to continue..."
echo

cp res/menu/*.xml ../KlingonAssistant/res/menu/
cp src/org/tlhInganHol/android/klingonassistant/*.java ../KlingonAssistant/src/org/tlhInganHol/android/klingonassistant/
git diff --no-ext-diff --relative=KlingonAssistant ../KlingonAssistant > backport.patch
git checkout ../KlingonAssistant/res/menu/*.xml
git checkout ../KlingonAssistant/src/org/tlhInganHol/android/klingonassistant/*.java
git status

