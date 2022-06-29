from __future__ import print_function
import pickle
import os.path
import io
import os
import time
import json
import random
import shutil
import requests
import http.client
import httplib2
from mimetypes import MimeTypes
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from moviepy.editor import VideoFileClip, concatenate_videoclips

from simple_term_menu import TerminalMenu
import concurrent.futures

################################################################################
# YOUTUBE STUFF
# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.

httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
  http.client.IncompleteRead, http.client.ImproperConnectionState,
  http.client.CannotSendRequest, http.client.CannotSendHeader,
  http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
################################################################################

# How many concurrent threads to check for processing videos
MAX_THREADS = 5


class DriveAPI:
    global SCOPES

    # Define the scopes
    SCOPES = ['https://www.googleapis.com/auth/drive',
              'https://www.googleapis.com/auth/youtube']

    def __init__(self):

        self.slack_hook = None
        self.parent_folder = None
        # grab variables from secrets file
        if not os.path.exists('secrets.json'):
            exit("Missing 'secrets.json'")

        with open('secrets.json', 'r') as secrets_file:
            secrets_data = json.load(secrets_file)
            self.slack_hook = secrets_data.get('slack_hook')
            self.parent_folder = secrets_data.get('parent_folder')

        # Variable self.creds will
        # store the user access token.
        # If no valid token found
        # we will create one.
        self.creds = None

        # The file token.pickle stores the
        # user's access and refresh tokens. It is
        # created automatically when the authorization
        # flow completes for the first time.

        # Check if file token.pickle exists
        if os.path.exists('token.pickle'):

            # Read the token from the file and
            # store it in the variable self.creds
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)

        # If no valid credentials are available,
        # request the user to log in.
        if not self.creds or not self.creds.valid:

            # If token is expired, it will be refreshed,
            # else, we will request a new one.
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Save the access token in token.pickle
            # file for future usage
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

    def findFolder(self):
        # Connect to the API service
        self.service = build('drive', 'v3', credentials=self.creds)

        # request a list of first N files or
        # folders with name and id from the API.

        folderPicked = False
        parentFolder = self.parent_folder # start with master folder from secrets.json
        curName = "2022 Film"
        while not folderPicked:
            results = self.service.files().list(q=f"'{parentFolder}' in parents and mimeType = 'application/vnd.google-apps.folder'",
                                                spaces="drive",
                                                fields="files(id, name)").execute()
            items = results.get('files', [])

            if len(items) == 0:
                # no subfolders! Potentially done, prompt user
                done = input(f"No subfolders detected! Splice '{curName}' (y/n)? ")
                if done == 'y':
                    folderPicked = True
                else:
                    # TODO: restart seach process
                    exit(0)

            else:
                # print a list of files
                print("Folders available: \n")
                for i, item in enumerate(items):
                    print(f"({i}): {item.get('name')}")
                selection_id = int(input("Jump to number: "))
                parentFolder = items[selection_id].get('id')
                curName = items[selection_id].get('name')

        return parentFolder, curName


    def downloadFilm(self, folder_id):
        # make dl directory if necessary
        if not os.path.exists("staging"):
            os.makedirs("staging")

        # remove existing files
        for file in os.scandir("staging"):
            os.remove(file.path)

        results = self.service.files().list(q=f"'{folder_id}' in parents",
                                            spaces="drive",
                                            fields="files(id, name)").execute()
        files = results.get('files', [])

        for file in files:
            print(f"Downloading {file.get('name')}...")
            file_id = file.get('id')
            dl_path = f"staging/{file.get('name')}"
            print("begin")
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download %d%%." % int(status.progress() * 100))

            fh.seek(0)
            # Write the received data to the file
            with open(dl_path, 'wb') as f:
                shutil.copyfileobj(fh, f)

    def get_clip_names(self):
        clipNames = [file.name for file in os.scandir("staging") if '.DS_Store' not in file.name]
        clipNames.sort()
        return clipNames

    def spliceFilm(self):
        # create list of loaded-in clips
        clipNames = self.get_clip_names()
        clips = []
        for clipName in clipNames:
            print(f"Processing {clipName}")
            vid = VideoFileClip(f"staging/{clipName}")
            clips.append(vid)

        # concatenate clips and save
        final = concatenate_videoclips(clips)
        final.write_videofile("staging/__merged.MP4")


    def format_desc(self):
        print("Generating chapters...")
        # get names and durations
        clipNames = self.get_clip_names()
        clipNames.sort()
        durations = []
        for clipName in clipNames:
            print(f"Formatting {clipName}")
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
            timeStr = time.strftime('%H:%M:%S', time.gmtime(curTime))
            clipString = f"{timeStr} {name}\n"
            desc += clipString
            # increment time and do again
            curTime += dur
        print("Chapters generated")
        return desc


    def initialize_upload(self, name="tempTitle", chapters=True):
        file = "staging/__merged.MP4"
        if not os.path.exists(file):
            exit("Missing __merged.MP4 in staging/")

        # format description
        if chapters:
            desc = self.format_desc()
        else:
            desc = "Filmspliced!"

        body=dict(
            snippet=dict(
                title=name,
                description=desc,
                tags=None
            ),
            status=dict(
                privacyStatus='unlisted',
                selfDeclaredMadeForKids=False
            )
        )

        # Connect to the API service
        self.service = build('youtube', 'v3', credentials=self.creds)
        # Call the API's videos.insert method to create and upload the video.
        insert_request = self.service.videos().insert(part=",".join(body.keys()),
                                                      body=body,
                                                      media_body=MediaFileUpload(file, chunksize=-1, resumable=True))

        self.resumable_upload(insert_request, name)

    # FROM YOUTUBE API DOCUMENTATION
    # This method implements an exponential backoff strategy to resume a failed upload.
    def resumable_upload(self, insert_request, name):
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                print("Uploading file...")
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print(f"Video id '{response['id']}' was successfully uploaded.")
                    else:
                        exit("The upload failed with an unexpected response: %s" % response)
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                         e.content)
                else:
                    raise
            except RETRIABLE_EXCEPTIONS as e:
                error = "A retriable error occurred: %s" % e

            if error is not None:
                print(error)
                retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            if not response:
                # sleep and retry if unsuccessful
                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print(f"Sleeping {sleep_seconds} seconds and then retrying...")
                time.sleep(sleep_seconds)

        if 'id' in response:
            # success; sleep till processed and notify slack
            self.sleep_till_processed(response['id'], name)


    def sleep_till_processed(self, vid_id, name):
        max_attempts = 10000
        # Call the API's videos.insert method to create and upload the video.
        request = self.service.videos().list(part="processingDetails",id=str(vid_id))
        status = None
        print("Checking processing status...")
        for attempt in range(max_attempts):
            time.sleep(60) # sleep 5 mins
            response = request.execute()
            status = response['items'][0]['processingDetails']['processingStatus']
            if status == 'processing':
                print("Still processing...")
            elif status == 'succeeded':
                print("Done! Sending message to slack")
                self.send_success_message(vid_id, name)
                break


    def get_uploads_playlist_id(self):

        channels_response = self.service.channels().list(
            mine=True,
            part='contentDetails'
        ).execute()

        # Only functions with single channels - will only return the first channels results
        for response in channels_response.get('items'):
            return response['contentDetails']['relatedPlaylists']['uploads']

    def get_processing_video_ids(self,uploads_playlist_id):
        upload_playlist_responses = self.service.playlistItems().list(part="snippet", playlistId=uploads_playlist_id).execute()

        snippet_ids_and_titles = [
            (
                response['snippet']['resourceId']['videoId'],
                response['snippet']['title']
            )
            for response in upload_playlist_responses.get('items')]
        return [(video_id, title) for video_id, title in snippet_ids_and_titles if self.is_processing(video_id)]

    def is_processing(self, video_id):
        processing_details = self.service.videos().list(part="processingDetails",id=str(video_id)).execute().get('items')
        for processing_detail in processing_details:
            return processing_detail['processingDetails']['processingStatus'] == 'processing'


    def monitor_processing(self, processing_video_ids):
        # worker_count = min(len(processing_video_ids), MAX_THREADS)
        # print(processing_video_ids)
        # with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        #     executor.map(self.sleep_till_processed, processing_video_ids)
        for video_id, video_name in processing_video_ids:
            self.sleep_till_processed(video_id, video_name)

    def send_success_message(self, vid_id, name):
        message = f"Video '{name}' has been filmspliced! Dap up www.youtube.com/watch?v={vid_id}"
        payload = {'text': message}
        x = requests.post(self.slack_hook, json = payload)

    def resume_monitoring(self):
        #TODO: Separate this from the google drive calls
        self.service = build('youtube', 'v3', credentials=self.creds)
        uploads_playlist_id = self.get_uploads_playlist_id()
        if not uploads_playlist_id:
            print("No uploads playlist found for this user")
            exit(1)
        processing_video_ids = self.get_processing_video_ids(uploads_playlist_id)
        print(f"Monitoring processing on these videos {processing_video_ids}")
        self.monitor_processing(processing_video_ids)
        print("Done!")

def main():
    toSplice, name = obj.findFolder()
    obj.downloadFilm(toSplice)
    obj.spliceFilm()
    obj.initialize_upload(name=name)

if __name__ == "__main__":
    options = ["new splice", "resume splice", "retry upload", "resume monitoring processing"]
    terminal_menu = TerminalMenu(options)
    user_selection = terminal_menu.show()

    existingFiles = [file.name for file in os.scandir("staging")] if os.path.exists("staging") else []
    try:
        obj = DriveAPI()
    except RefreshError:
        # if token expired; remove it and retry
        os.remove("token.pickle")
        obj = DriveAPI()

    if user_selection == 0:
        # new splice
        main()
    elif user_selection == 1:
        # resume splice
        name = input("""What is the name of the video to be uploaded?\n""")
        if len(existingFiles) == 0:
            print("No files found in staging! Cannot resume splice")
            exit()
        obj.spliceFilm()
        obj.initialize_upload(name=name)
    elif user_selection == 2:
        # resume upload
        if "__merged.MP4" not in existingFiles:
            print("Missing '__merged.MP4' in staging! Cannot resume upload")
            exit()
        name = input("What is the name of the video to be uploaded?\n")
        obj.initialize_upload(name=name)
    elif user_selection == 3:
        # resume monitoring processing
        obj.resume_monitoring()
