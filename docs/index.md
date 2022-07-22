## Purpose

Many Ultimate teams ([Brown](https://www.brown.edu/Athletics/Mens_Ultimate/index.html) included) film their games and/or practices and store the footage in Google Drive.
However, it is not ideal to watch the footage back clip by clip in the Drive video player.
YouTube is far preferable in order to take advantage of features like playlists, chapters, and sharing links with timestamps.

So, to facilitate this, I built FilmSplice! It works in three steps:
1. Download footage from Google Drive
2. Stich clips together into single .MP4 file
3. Upload merged footage to YouTube

## Extra Features
### Slack integration
Many teams use slack to communicate.
FilmSplice supports a slack hook as an optional parameter, and can send messages to a slack channel when film is done processing

### Playlists
Teams often have separate playlists for different tournaments, seasons, or even just games/practices.
FilmSplice allows users to select a playlist to automatically add the spliced footage to prior to uploading

## Challenges and Takeaways

The most difficult part of this project was learning how to use the Google APIs for Drive and YouTube.
Through trial and error, I have learned a lot about how HTTP requests work and how to interface with external code.
My python coding skills have also improved, as has my understanding of how to build and deploy websites and documentation
