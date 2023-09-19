import os
import json
import base64
from requests import post, get
from dotenv import load_dotenv
from datetime import datetime

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
        print(authorization_url)

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


def get_recently_played(token, starting_date, limit=50):
    url = "https://api.spotify.com/v1/me/player/recently-played"
    headers = get_auth_header(token)
    timestamp_ms = int(starting_date.timestamp()) * 1000
    query = f"?limit={limit}&after={timestamp_ms}"

    all_recently_played = []

    while True:
        query_url = url + query
        result = get(query_url, headers=headers)
        json_result = json.loads(result.content)["items"]
        all_recently_played.extend(json_result)

        if len(json_result) < limit:
            break
        else:
            # Update the after timestamp for the next page
            last_played_item = json_result[-1]
            timestamp_ms = int(datetime.strptime(
                last_played_item["played_at"], "%Y-%m-%dT%H:%M:%SZ").timestamp()) * 1000
            query = f"?limit={limit}&after={timestamp_ms}"

    return all_recently_played


# Function to get genre information for a track
def get_track_genre(access_token, track_id):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = get_auth_header(access_token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    if "genres" in json_result:
        return json_result["genres"]
    else:
        return []


# Function to get genre information for an artist
def get_artist_genres(access_token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = get_auth_header(access_token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    if "genres" in json_result:
        return json_result["genres"]
    else:
        return []


if __name__ == "__main__":
    access_token = get_token()
    start_date = datetime(2023, 9, 17)
    recently_played = get_recently_played(access_token, start_date)

    # Print the recently played songs
    for idx, item in enumerate(recently_played):
        song_name = item["track"]["name"]
        artist_name = item["track"]["artists"][0]["name"]
        print(f"{idx + 1}. {song_name} by {artist_name}")
