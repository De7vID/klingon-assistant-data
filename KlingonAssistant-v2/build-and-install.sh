#!/bin/bash

# Generate the database.
# cd data
# ./generate_db.sh
# cd ..

# Build the debug build.
./gradlew assembleDebug
if [ $? -eq 0 ]
then
    # Pause before pushing.
    read -n1 -r -p "Press any key to push to device..."
    echo

    # Push to device.
    adb install -r ./app/build/outputs/apk/app-debug.apk
    adb push ./app/build/outputs/apk/app-debug.apk /sdcard/
else
    echo ERROR: Failed to compile.
fi
