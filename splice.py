from __future__ import print_function
import os.path
import os
import time
import subprocess
import shutil
from google.auth.exceptions import RefreshError
from moviepy.editor import *
import whiptail as wt

from tkinter.filedialog import askdirectory

from driveapi import DriveAPI
#tk.Tk().withdraw() # part of the import if you are not using other tkinter functions
DISK_USAGE_THRESHOLD = 0.85


def spliceFilm(filmpath=f'{os.getcwd()}/staging'):
    # check if there is enough space on disk
    merged_size = sum([file.stat().st_size for file in os.scandir('staging')])
    available_space = shutil.disk_usage('staging').free
    if merged_size > available_space * DISK_USAGE_THRESHOLD:
        print(f"Cannot splice! Not enough space available on disk (need {merged_size}, {available_space} available)")
        sys.exit(1)
    # Splice film together, store in staging/__merged.MP4
    subprocess.run(['sh', 'splice.sh', filmpath])

def get_clips():
    clips = []
    for file in os.scandir("staging"):
        if file.name[-3:] == "MP4" and file.name != "__merged.MP4":
            clips.append(file.name)
    clips.sort()
    print(clips)
    return clips

def format_desc():
    print("Generating chapters...")
    # get names and durations
    clipNames = get_clips()
    durations = []
    for clipName in clipNames:
        vid = VideoFileClip(f"staging/{clipName}")
        durations.append(vid.duration)
        del vid

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
    return desc


def prompt_name(folderName):
    res = wt.Whiptail(title="Name Video", height=20, width=60).inputbox(
        msg="Enter video title", default=folderName
    )
    # if cancelled; exit
    if res[1]:
        sys.exit(0)
    return res[0]

# determine whether user wants to download from drive or locally
def prompt_fileloc():
    choice, response = wt.Whiptail(
            title="Choose Film Location", height=20, width=60
        ).menu(msg=f"Choose where the film to splice is loacted", items=["Google Drive", "Local"])
    if response:
        sys.exit(0)
    return choice

# Execute splice from scratch
def execute_splice(obj):
    # make dl directory if necessary
    if not os.path.exists("staging"):
        os.mkdir("staging")

    fileloc = prompt_fileloc()
    if fileloc == "Google Drive":
        # locate google drive folder
        toSplice, folderName = obj.findFolder()
        # ask user for name
        name = obj.prompt_name(folderName)
        # ask user for playlist
        playlist = obj.prompt_playlist(name)
        # download film from drive
        obj.downloadFilm(toSplice)
        # splice it
        obj.spliceFilm()
        # begin upload
        obj.initialize_upload(name=name,playlist=playlist)
    elif fileloc == "Local":
        # get path to film folder
        filmpath = askdirectory()
        if not filmpath:
            sys.exit(1)
        # ask user for name
        name = obj.prompt_name(filmpath.split('/')[-1])
        # ask user for playlist
        playlist = obj.prompt_playlist(name)
        # splice it
        obj.spliceFilm(filmpath=filmpath)
        # begin upload
        obj.initialize_upload(name=name,playlist=playlist)
    else:
        print("How did we get here")
        sys.exit(1)

def main():
    try:
        obj = DriveAPI()
    except RefreshError:
        # if token expired; remove it and retry
        os.remove("token.pickle")
        obj = DriveAPI()

    existingFiles = [file.name for file in os.scandir("staging")]
    options = ["new splice", "resume splice", "retry upload"]
    user_selection = obj.fzf.prompt(options)[0]
    if user_selection == "new splice":
        # new splice
        execute_splice(obj)
    elif user_selection == "resume splice":
        # resume splice
        if len(existingFiles) == 0:
            print("No files found in staging! Cannot resume splice")
            exit()
        obj.spliceFilm()
        obj.initialize_upload()
    elif user_selection == "retry upload":
        # resume upload
        if "__merged.MP4" not in existingFiles:
            print("Missing '__merged.MP4' in staging! Cannot resume upload")
            exit()
        obj.initialize_upload()


if __name__ == "__main__":
    main()
