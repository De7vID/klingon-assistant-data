#!/bin/sh
patch -p1 < KlingonAssistant/tutorial_unpatch.txt
cd KlingonAssistant
ant clean
