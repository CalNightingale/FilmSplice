THINGS TO KNOW:
NEED GOOGLE CREDENTIALS INTO FILM FOLDER YOU WANT! ALSO HAVE TO SET IT (TODO make this easier)
make a credentials.json file for them

ALSO NEED ffmpeg library to process mp4 files!


If you have issues with mobile phones and rotations (something ffmpeg does on it's own),
this commit contains a fix that hasn't been released as of 6/23/2022. To install:

`
git clone https://github.com/Zulko/moviepy
git checkout 18e9f57d1abbae8051b9aef75de3f19b4d1f0630
pip install -e  .
`