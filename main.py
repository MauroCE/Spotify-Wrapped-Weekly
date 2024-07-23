import os
import json
import base64
from requests import post, get
from dotenv import load_dotenv
import datetime

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = "http://localhost:8888/callback"
refresh_token_file = "refresh_token.txt"  # File to store and retrieve the refresh token


def get_token():
    """Obtains a token using the Authorization Code flow. If a `refresh_token` is available,
    it will be read and passed to the API. Otherwise, a refresh token will be obtained manually
    and the user will need to authorize via the link printed to console and then grab the
    authorization `code` from the redirect URI."""
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
            "scope": "user-read-recently-played",
        }
        authorization_url = auth_url + "?" + "&".join([f"{k}={v}" for k, v in auth_params.items()])

        print("Please visit the following URL to authorize your application:", authorization_url)

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
    """Reads a refresh token from files, if it exists, or else returns None."""
    try:
        with open(refresh_token_file, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None


def write_refresh_token(refresh_token: str) -> None:
    with open(refresh_token_file, "w") as file:
        file.write(refresh_token)


def get_auth_header(token: str) -> dict:
    return {"Authorization": "Bearer " + token}


def get_audio_features(token: str, track_id: str) -> dict:
    """Retrieve audio features for a track, given a token.

    Parameters
    ----------
    :param token: Authorization token obtained from Spotify API using `get_token()` above.
    :type token: str
    :param track_id: ID of track for which we want to grab data.
    :type track_id: str

    Return
    ------
    :return: Dictionary of audio features, see API documentation for fields.
    :rtype: dict
    """
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    return json.loads(result.content)


def get_recently_played_with_audio_features(token: str, starting_date: datetime.datetime, limit: int = 50):
    """Grabs specific fields of recently played songs. Currently, we only grab track ID, track name, track artist name,
    track artist id, track duration (in millisecond), and time at which song was played at (UTC).

    Parameters
    ----------

    :param token: Spotify API authorization token.
    :type token: str
    :param starting_date: Date from which we want to grab data from, typically will be start of the current week.
    :type starting_date: datetime
    :param limit: Limit of songs fetched from the API from starting date. Currently, the Spotify API only stores the
    last 50 songs.
    :type limit: int

    Return
    ------
    :return: Dictionary containing information about recently played songs.
    :rtype: dict
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
    return json.loads(result.content)["items"]


if __name__ == "__main__":
    access_token = get_token()
    start_date = datetime.datetime(2023, 9, 17)
    recent_songs = get_recently_played_with_audio_features(access_token, start_date)
