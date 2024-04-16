import os
import subprocess
import re
import sys
import time

# Return clip duration in seconds
def get_clip_duration(clip_name: str) -> int:
    video_path = f"staging/{clip_name}"
    # Run the command and capture output
    command = ["ffmpeg", "-i", video_path]
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)

    # Use regular expression to search for the duration
    duration_match = re.search(r"Duration: (\d{2}:\d{2}:\d{2})", result.stderr)
    
    if duration_match:
        # Parse HH:MM:SS
        hrs, mins, secs = map(int, duration_match.group(1).split(':'))
        return hrs * 3600 + mins * 60 + secs
    # If no duration found, return a message or handle as needed
    print("Duration not found")
    sys.exit(1)

def get_clips():
    clips = []
    for file in os.scandir("staging"):
        if file.name[-3:] == "MP4" and file.name != "__merged.MP4":
            clips.append(file.name)
    clips.sort()
    return clips

def format_desc(print_desc=False):
    print("Generating chapters...")
    # get names and durations
    clipNames = get_clips()
    durations = []
    for clipName in clipNames:
        duration = get_clip_duration(clipName)
        durations.append(duration)

    # generate formatted string
    desc = "Filmspliced! Clips:\n\n"
    curTime = 0
    for name, dur in zip(clipNames, durations):
        if name == "__merged.MP4":
            # skip merged if it exists
            continue
        # format time for use in YouTube auto-chapter generation
        timeStr = time.strftime("%H:%M:%S", time.gmtime(curTime))
        clipString = f"{timeStr} {name}\n"
        desc += clipString
        # increment time and do again
        curTime += dur
    print("Chapters generated")
    if print_desc:
        print(desc)
    return desc