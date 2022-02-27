# import the required libraries
from __future__ import print_function
import pickle
import os.path
import io
import shutil
import requests
from mimetypes import MimeTypes
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

class DriveAPI:
    global SCOPES

    # Define the scopes
    SCOPES = ['https://www.googleapis.com/auth/drive']

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


    def FileDownload(self, file_id, file_name):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()

        # Initialise a downloader object to download the file
        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        done = False

        try:
            # Download the data in chunks
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)

            # Write the received data to the file
            with open(file_name, 'wb') as f:
                shutil.copyfileobj(fh, f)

            print("File Downloaded")
            # Return True if file Downloaded successfully
            return True
        except:

            # Return False if something went wrong
            print("Something went wrong.")
            return False

if __name__ == "__main__":
    obj = DriveAPI()
    obj.findFolder()
    #obj.FileDownload(f_id, f_name)
