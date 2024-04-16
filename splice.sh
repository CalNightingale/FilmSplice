#!/bin/sh

# Check if directory argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

# Assign the directory argument to a variable
DIR=$1

# Remove clips.txt from DIR if it exists
rm "$DIR/clips.txt"

# Create list of all clips to splice
ls -1 "$DIR" | sed 's/^/file /' >> clips.txt

# Put list in specified directory so it is properly wiped on new splice
mv clips.txt "$DIR"

# execute concatenation with ffmpeg, (merged.mp4 should always end up in staging)
ffmpeg -f concat -i "$DIR/clips.txt" -c copy staging/__merged.MP4
