import os
import subprocess
import re
import sys
import time
import tempfile

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

# Get all of the clip names in the staging directory
def get_clips():
    clips = []
    for file in os.scandir("staging"):
        if file.name[-3:] == "MP4" and file.name != "__merged.MP4":
            clips.append(file.name)
    clips.sort()
    return clips

# Generate youtube video description
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


def execute_splice(directory):
    # Check if directory exists
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)

    # Get list of video files in the directory
    video_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    video_files.sort()  # Sort the files alphanumerically

    # Prepare the input for ffmpeg
    input_list = [f"file '{os.path.abspath(os.path.join(directory, f))}'" for f in video_files]
    input_text = "\n".join(input_list)

    # Create a temporary file for ffmpeg input
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(input_text)
        temp_file_path = temp_file.name

    # Prepare the ffmpeg command
    ffmpeg_command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", temp_file_path,
        "-c", "copy",
        "staging/__merged.MP4"
    ]

    # Execute ffmpeg command
    try:
        subprocess.run(ffmpeg_command, check=True)
        print("Video concatenation completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during video concatenation: {e}")
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)
