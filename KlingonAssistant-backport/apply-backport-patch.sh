#!/bin/sh
cp ../KlingonAssistant/src/org/tlhInganHol/android/klingonassistant/*.java src/org/tlhInganHol/android/klingonassistant/
cp ../KlingonAssistant/res/menu/options_menu.xml res/menu/
patch -p1 < backport.patch

