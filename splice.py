# import the required libraries
from __future__ import print_function
import pickle
import os.path
import io
import os
import time
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
from moviepy.editor import *

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


class DriveAPI:
    global SCOPES

    # Define the scopes
    SCOPES = ['https://www.googleapis.com/auth/drive',
              'https://www.googleapis.com/auth/youtube']

    def __init__(self):

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
        parentFolder = '1z6Igio7OykVw6YQXYDk97rbkeeCiLkb_' # start with BMO film as parent folder
        curName = "BMo Film"
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

    def spliceFilm(self):
        # create list of loaded-in clips
        clipNames = [file.name for file in os.scandir("staging")]
        clipNames.sort()
        clips = []
        for clipName in clipNames:
            vid = VideoFileClip(f"staging/{clipName}")
            clips.append(vid)

        # concatenate clips and save
        final = concatenate_videoclips(clips)
        final.write_videofile("staging/__merged.MP4")

    def initialize_upload(self, name="tempTitle"):
        file = "staging/__merged.MP4"
        if not os.path.exists(file):
            exit("Missing __merged.MP4 in staging/")

        body=dict(
            snippet=dict(
                title=name,
                description="Filmspliced!",
                tags=None
            ),
            status=dict(
                privacyStatus='unlisted'
            )
        )

        # Connect to the API service
        self.service = build('youtube', 'v3', credentials=self.creds)
        # Call the API's videos.insert method to create and upload the video.
        insert_request = self.service.videos().insert(part=",".join(body.keys()),
                                                      body=body,
                                                      media_body=MediaFileUpload(file, chunksize=-1, resumable=True))

        self.resumable_upload(insert_request)

    # FROM YOUTUBE API DOCUMENTATION
    # This method implements an exponential backoff strategy to resume a failed upload.
    def resumable_upload(self, insert_request):
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

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print(f"Sleeping {sleep_seconds} seconds and then retrying...")
            time.sleep(sleep_seconds)


if __name__ == "__main__":
    obj = DriveAPI()
    existingFiles = [file.name for file in os.scandir("staging")]
    if len(existingFiles) > 0:
        # existing work in staging
        if "__merged.MP4" in existingFiles:
            # splicing done already
            ans = input("previous merge detected. Resume upload?(y/n) ")
            if ans == 'y':
                obj.initialize_upload()
            else:
                exit(0)
        else:
            # splicing not done
            ans = input("files in staging. Resume merge?(y/n) ")
            if ans == 'y':
                obj.spliceFilm()
                obj.initialize_upload()
            else:
                exit(0)
    else:
        # no existing work
        toSplice, name = obj.findFolder()
        obj.downloadFilm(toSplice)
        obj.spliceFilm()
        obj.initialize_upload(name=name)
