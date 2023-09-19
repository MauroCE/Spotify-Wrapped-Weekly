# Spotify Wrapped Weekly
Using Python to grab recently played songs from Spotify API and Charts.js to display a SpotifyWrapped.

# How to use this code
For this repository to work, obtain `CLIENT_ID` and `CLIENT_SECRET` from [Spotify for Developers](https://developer.spotify.com/) and create a `.env` file with 
these two variables. It should look like this:
```
CLIENT_ID="your-client-id"
CLIENT_SECRET="your-client-secret"
```
Once this is set, you can run this code locally by running `app.py`. The first time you run it, you need to give the authorization and pass the code, however the refresh
token should take care of it for future runs. Personally, I am using [Heroku](www.heroku.com) to host my Flask App, since it is cheap but works wonders.
