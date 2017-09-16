#!/bin/bash
./gradlew clean
cp ../KlingonAssistant/app/src/main/assets/qawHaq.db app/src/main/assets/qawHaq.db
grep -l -r "klingonassistant_v2" app/* | xargs sed -i "s/klingonassistant_v2/klingonassistant/g"
./gradlew assembleRelease
