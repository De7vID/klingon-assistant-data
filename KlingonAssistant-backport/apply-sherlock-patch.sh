#!/bin/sh
cp ../KlingonAssistant/src/org/tlhInganHol/android/klingonassistant/KlingonAssistant.java src/org/tlhInganHol/android/klingonassistant/
cp ../KlingonAssistant/src/org/tlhInganHol/android/klingonassistant/EntryActivity.java src/org/tlhInganHol/android/klingonassistant/
cp ../KlingonAssistant/res/menu/options_menu.xml res/menu/
patch -p1 < ActionBarSherlock.patch
