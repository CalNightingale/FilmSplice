#!/bin/sh

ls -1 staging | sed 's/^/file /' >> clips.txt

mv clips.txt staging

ffmpeg -f concat -i staging/clips.txt -c copy staging/__merged.mp4
