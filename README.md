# Installation & Setup
1. Clone this repository

2. Create a python virtual environment. Must be python3.6 or later

3. `pip install -r requirements.txt`

4. Create credentials.json in filmsplice folder.

5. Need to generate credentials as per [google's developer instructions](https://developers.google.com/workspace/guides/create-credentials#oauth-client-id)
Contact Cal for this; he can send you the credentials

6. Create secrets.json in filmsplice folder.
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

7. Ensure the following libraries are installed locally: 
* ffmpeg (check with `ffmpeg -version`)
* whiptail (check with `whiptail -version`). If on mac, install with `brew install newt`

# To Use
`python splice.py`


# Legal/Google Stuff

**Privacy Policy**

Use FilmSplice at your own risk! Your google credentials are stored purely for use to authenticate using the OAuth client
so that FilmSplice can function properly. It is your responsibility to keep your `credentials.json` file safe!

**Terms of Service**

Only use FilmSplice as a utility to download film from google drive, stitch it together, and upload it to your personal YouTube
channel. Any other usage of FilmSplice is prohibited.

