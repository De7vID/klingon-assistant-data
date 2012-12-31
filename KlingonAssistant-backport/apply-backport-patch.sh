#!/bin/sh
cp ../KlingonAssistant/src/org/tlhInganHol/android/klingonassistant/*.java src/org/tlhInganHol/android/klingonassistant/
rm src/org/tlhInganHol/android/klingonassistant/JellyBeanSpanFixTextView.java
cp ../KlingonAssistant/res/menu/options_menu.xml res/menu/
patch -p1 < backport.patch

