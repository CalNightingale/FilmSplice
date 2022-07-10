# Installation & Setup
1. Clone this repository
2. Create a python virtual environment. Must be python3.6 or later
3. `pip install -r requirements.txt`
4. Create credentials.json in filmsplice folder. Need to generate credentials as per [google's developer instructions]
(https://developers.google.com/workspace/guides/create-credentials#oauth-client-id)
Contact Cal for this; he can send you the credentials
5. Create secrets.json in filmsplice folder.
Should look like this:
```json
{
  slack_hook: [YOUR_SLACK_HOOK_URL],
  parent_folder: [YOUR_GOOGLE_DRIVE_FILM_FOLDER_ID]
}
```
`slack_hook` is optional; you can use this to send messages to your team slack when a video is uploaded.
Check out the [slack api](https://api.slack.com/messaging/webhooks) for information on setting this up.
`parent_folder` is required; this is the google drive folder ID of the master folder containing your team's film.
To find this, simply navigate to the folder in a web browser and examine the URL and find the string at the end:
`https://drive.google.com/drive/u/1/folders/FOLDER_ID`
6. Ensure the ffmpeg library is installed locally. Check if installed with `ffmpeg -version`

# To Use
`python splice.py`

