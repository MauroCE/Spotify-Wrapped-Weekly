import os
import json
import base64
from requests import post, get
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pickle

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = "http://localhost:8888/callback"
refresh_token_file = "refresh_token.txt"  # File to store and retrieve the refresh token


def get_token():
    """Grabs Access Token"""
    token_url = "https://accounts.spotify.com/api/token"

    # Check if a refresh token is already stored
    refresh_token = read_refresh_token()

    if refresh_token:
        # Use the refresh token to get new access token
        token_params = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
    else:
        # Generate the authorization URL
        auth_url = "https://accounts.spotify.com/authorize"
        auth_params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "user-read-recently-played",  # Add the required scope
        }
        authorization_url = auth_url + "?" + "&".join([f"{k}={v}" for k, v in auth_params.items()])

        print("Please visit the following URL to authorize your application:")

        # After user authorization, you will receive an authorization code
        authorization_code = input("Enter the authorization code from the URL: ")

        # Exchange the authorization code for an access token and refresh token
        token_params = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": redirect_uri,
        }

    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    token_headers = {
        "Authorization": "Basic " + auth_base64,
    }

    result = post(token_url, headers=token_headers, data=token_params)

    # Transform to dictionary
    json_result = json.loads(result.content)
    token = json_result["access_token"]

    if "refresh_token" in json_result:
        # Store the refresh token for future use
        write_refresh_token(json_result["refresh_token"])

    return token


def read_refresh_token():
    try:
        with open(refresh_token_file, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None


def write_refresh_token(refresh_token):
    with open(refresh_token_file, "w") as file:
        file.write(refresh_token)


def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def get_audio_features(token, track_id):
    """Retrieve audio features for a track."""
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    return json.loads(result.content)


def get_recently_played_with_audio_fearures(token, starting_date, limit=50):
    """Notice that one cannot specify both after and before.
    I need a storage system for songs during the week. Spotify only saves the last 50 songs, so I need to make sure
    that I constantly save songs based on the timestamp of when they were `played_at`. The minimal information I need to
    store is the song id, artist id, and played_at. With these three information I can then gain access to the artist
    genres as well as other things, such as mood.

    The way I store this information is crucial because it should allow me to be as efficient as possible with checking
    if I have downloaded new songs or not. I should check if it is possible to have timestamps as dictionary keys, and
    importantly I should check that this works as expected using the `datetime` module.

    Seems to be working. Should be enough to store songs in the dictionary based on the played_at value.
    """
    # Build the query using fields, limit and after
    url = "https://api.spotify.com/v1/me/player/recently-played"
    timestamp_ms = int(starting_date.timestamp()) * 1000
    query = f"?limit={limit}&after={timestamp_ms}"
    query += "&fields=track.id,track.name,track.artists.name,track.artists.id,track.duration_ms,played_at"
    query_url = url + query
    # GET request and extract results
    headers = get_auth_header(token)
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["items"]
    # For each result, find audio features
    
    recently_played_songs = json_result

    print(recently_played_songs[0])

    return recently_played_songs


if __name__ == "__main__":
    access_token = get_token()
    start_date = datetime(2023, 9, 17)
