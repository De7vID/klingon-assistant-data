#!/bin/sh
patch -p1 < KlingonAssistant/tutorial_unpatch.txt
cd KlingonAssistant
sed -i "s/\(versionName=.*\) (TTS)/\1/" AndroidManifest.xml
ant clean
