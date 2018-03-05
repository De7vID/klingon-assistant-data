#!/bin/bash
if [ $# -eq 0 ]
then
        echo "Usage: `basename $0` {letters}"
        exit
fi
EDITCMD="view -p "
for letter in "$@"
do
        EDITCMD="$EDITCMD mem-*-$letter.xml "
done
$EDITCMD
