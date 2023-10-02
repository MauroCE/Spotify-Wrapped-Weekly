from flask import Flask, render_template, send_from_directory, url_for
from main import get_token, get_recently_played_with_audio_fearures, get_auth_header
from datetime import datetime, timedelta, date, time
import os
import json
from collections import defaultdict
from flask_caching import Cache
from functools import wraps
from requests import RequestException
from requests import get
import pickle
import numpy as np
import pytz
from tzlocal import get_localzone
import pendulum
import pandas as pd


app = Flask(__name__)

port = int(os.environ.get("PORT", 8000))  # Use 5000 as the default port, 8000 when run locally

# Configure Flask-Caching
# Configure Flask-Caching with the 'filesystem' cache type and specify the cache directory
# app.config['CACHE_TYPE'] = 'filesystem'
# app.config['CACHE_DIR'] = 'cache' #'SpotifyAPI/cache'  # Relative path to the cache directory
# cache = Cache(app)
TIMEOUT = 60  # in seconds. Set it to 10 minutes


# Decorator to handle API request errors and rate limiting
def handle_api_errors(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except RequestException as e:
            # Handle network or API rate limit exceeded errors
            # Implement error handling and retry logic here if needed
            print(f"API Request Error: {e}")
            return None  # or raise a custom exception

    return decorated_function


# Function to make API requests with error handling and rate limiting
@handle_api_errors
def api_get(url, headers=None, params=None):
    response = get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


# Function to get genre information for a track
#@cache.cached(timeout=TIMEOUT, key_prefix="track_genre")  # Cache the result for one day (adjust as needed)
@handle_api_errors
def get_track_genre(access_token, track_id):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = get_auth_header(access_token)
    result = api_get(url, headers=headers)
    if result and "genres" in result:
        return result["genres"]
    else:
        return []


# Function to get genre information for an artist
# @cache.cached(timeout=TIMEOUT, key_prefix="artist_genre")  # Cache the result for one day (adjust as needed)
@handle_api_errors
def get_artist_genres(access_token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = get_auth_header(access_token)
    result = api_get(url, headers=headers)
    if result and "genres" in result and "popularity" in result:
        return result["genres"], result["popularity"]
    else:
        return []


def group_songs_by_artist(recently_played, access_token, genres_by_artistid, popularity_by_artistid={}):
    """This function can definitely be improved. I think I just need to avoid repeating artists.
    Besides, I could just grab the songs genres really."""
    # Create a dictionary to store songs grouped by artist and their genres
    artist_dict = defaultdict(lambda: {"songs": [], "genres": [], "popularity": 0.0})

    new_artist_genres = {}
    new_artist_popularities = {}

    for ix, item in enumerate(recently_played):
        artist_name = item["track"]["artists"][0]["name"] #item["track"]["artists"][0]["name"]
        song_name = item["track"]["name"]

        # Retrieve artist details to get genre information
        artist_id = item["track"]["artists"][0]["id"] #item["track"]["artists"][0]["id"]
        if artist_id in genres_by_artistid.keys() and artist_id in popularity_by_artistid:
            # Grab genres and popularity from stored data
            genres = genres_by_artistid[artist_id]
            popularity = popularity_by_artistid[artist_id]
        else:
            # Grab genres and popularity from API and add it to the dictionaries above
            genres, popularity = get_artist_genres(access_token, artist_id)
            new_artist_genres[artist_id] = genres
            new_artist_popularities[artist_id] = popularity
            print("Missing: ", artist_name, artist_id, genres, popularity)

        # Artist dictionary contains artist_name: {"songs": [], "genres": [], "popularity": []}
        artist_dict[artist_name]["songs"].append(song_name)
        artist_dict[artist_name]["genres"].extend(genres)
        artist_dict[artist_name]["popularity"] = popularity

    # Update pickled data for id:genres
    genres_by_artistid.update(new_artist_genres)
    with open("genres_by_artistid.pkl", "wb") as file:
        pickle.dump(genres_by_artistid, file)

    # Update pickled data for id: popularity
    popularity_by_artistid.update(new_artist_popularities)
    with open("popularity_by_artistid.pkl", "wb") as file:
        pickle.dump(popularity_by_artistid, file)

    # Convert the dictionary into a list of dictionaries
    artist_list = [{"artist": artist, "songs": data["songs"], "genres": data["genres"], "popularity": data["popularity"]} for artist, data in artist_dict.items()]

    return artist_list


def calculate_time_distribution(recently_played):
    # Initialize a list to store the count of songs for each hour of the day
    time_distribution = [0] * 24

    for item in recently_played:
        played_at = datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ")  # Updated format string
        hour = played_at.hour
        time_distribution[hour] += 1

    return time_distribution


def get_top_artists_images(access_token, top_artists_ids):
    """Grabs images from top artist ids."""
    artist_images = []
    for artist_id in top_artists_ids:
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        headers = get_auth_header(access_token)
        result = api_get(url, headers=headers)
        artist_images.append(result["images"][0]["url"])
    return artist_images


class NoSongsPlayedThisWeekError(Exception):
    pass


def tz_diff(home, away, on=None):
    """
    Return the difference in hours between the away time zone and home.

    `home` and `away` may be any values which pendulum parses as timezones.
    However, recommended use is to specify the full formal name.
    See https://gist.github.com/pamelafox/986163

    As not all time zones are separated by an integer number of hours, this
    function returns a float.

    As time zones are political entities, their definitions can change over time.
    This is complicated by the fact that daylight savings time does not start
    and end on the same days uniformly across the globe. This means that there are
    certain days of the year when the returned value between `Europe/Berlin` and
    `America/New_York` is _not_ `6.0`.

    By default, this function always assumes that you want the current
    definition. If you prefer to specify, set `on` to the date of your choice.
    It should be a `Pendulum` object.

    This function returns the number of hours which must be added to the home time
    in order to get the away time. For example,
    ```python
    >>> tz_diff('Europe/Berlin', 'America/New_York')
    -6.0
    >>> tz_diff('Europe/Berlin', 'Asia/Kabul')
    2.5
    ```
    """
    if on is None:
        on = pendulum.today()
    diff = (on.set(tz=home) - on.set(tz=away)).total_hours()

    # what about the diff from Tokyo to Honolulu? Right now the result is -19.0
    # it should be 5.0; Honolulu is naturally east of Tokyo, just not so around
    # the date line
    if abs(diff) > 12.0:
        if diff < 0.0:
            diff += 24.0
        else:
            diff -= 24.0

    return diff


@app.route('/')
#@cache.cached(timeout=TIMEOUT, key_prefix="recently_played")  # Cache the result for one day (adjust as needed)
def index():
    access_token = get_token()

    # Grab recently-played songs from the API
    # Heroku server: UTC timezone
    # Spotify played at: UTC timezone
    # UTC is currently behind by 1 hour wrt UK timezone
    # UTC is the same as UK timezone. There are multiple things at play.
    # Spotify records in UTC, which is the same as UK timezone. However, Heroku server is in a different timezone.
    uk_timezone = pytz.timezone('Europe/London')
    today = datetime.now(uk_timezone).date()
    current_week_start = today - timedelta(days=today.weekday())
    start_date = datetime.combine(current_week_start, time.min)  # Monday 00:00. Midnight of Monday of the curr week in the UK
    start_date_utc = start_date + timedelta(hours=tz_diff("Europe/London", "utc"))  # Transform to UTC since this is how played_at is stored in Spotify data
    start_date_utc = start_date_utc.replace(tzinfo=None)
    recently_played = get_recently_played_with_audio_fearures(access_token, start_date_utc)

    # Transform recently-played songs from API into played_at:track dictionary
    api_songs = {item['played_at']: item['track'] for item in recently_played}
    print("Retrieved {} songs from the API.".format(len(api_songs.keys())))

    # Grab file-stored songs, potentially these are older than the 50th song saved on Spotify
    try:
        with open("this_weeks_songs.pkl", "rb") as file:
            file_songs = pickle.load(file)
    except FileNotFoundError:
        file_songs = {}  # if it doesn't exist, set it to an empty dictionary
    print("Retrieved {} songs from file.".format(len(file_songs.keys())))
    file_songs_dates = np.array([datetime.strptime(d, "%Y-%m-%dT%H:%M:%S.%fZ") for d in file_songs.keys()])

    # Merge songs from api and file-stored
    all_songs = file_songs | api_songs
    print("Total unique songs retrieved: {}".format(len(all_songs.keys())))
    # Delete file-stored songs that are older than Monday midnight and hence belong to previous week
    song_dates_to_delete = np.where(file_songs_dates < start_date_utc)[0]
    if len(song_dates_to_delete) > 0:
        for d_ix in song_dates_to_delete:
            del all_songs[file_songs_dates[d_ix].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z']
        print("Deleted {} songs.".format(len(song_dates_to_delete)))
    if len(all_songs) == 0:
        raise NoSongsPlayedThisWeekError

    # Update file so it does not contain deleted songs
    with open("this_weeks_songs.pkl", "wb") as file:
        pickle.dump(all_songs, file)

    # Grab artist_id:genres dictionary
    with open("genres_by_artistid.pkl", "rb") as file:
        genres_by_artistid = pickle.load(file)

    # Grab artist_id:popularity dictionary
    try:
        with open("popularity_by_artistid.pkl", "rb") as file:
            popularity_by_artistid = pickle.load(file)
    except FileNotFoundError:
        popularity_by_artistid = {}

    # Now transform data into the correct format
    this_weeks_songs = []
    for (key, item) in all_songs.items():
        if np.all([item['artists'][i]['name'] != 'Pinkfong' for i in range(len(item['artists']))]):
            this_weeks_songs.append({'track': item, 'played_at': key})

    # Compute artists counts (my new function). Recall this_weeks_songs is a list of dictionaries and d['track'] has
    # keys 'artists', 'id', 'name' where if you grab d['track']['artists'] it has keys 'id' and 'name'.
    artist_counts = defaultdict(int)
    artist_names_by_id = {}
    artist_ids_by_name = {}
    for item in this_weeks_songs:
        for subitem in item['track']['artists']:
            artist_counts[subitem['name']] += 1
            artist_names_by_id[subitem["id"]] = subitem["name"]
            artist_ids_by_name[subitem["name"]] = subitem["id"]

    # Grab top artists
    top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:4] # grab only 4
    top_artists = [item[0] for item in top_artists]
    top_artists_ids = [artist_ids_by_name[name] for name in top_artists]

    # Dictionary for images (top artists)
    top_artists_images_urls = get_top_artists_images(access_token, top_artists_ids)
    top_artists_images_by_name = {top_artists[i]: top_artists_images_urls[i] for i in range(len(top_artists))}

    # Compute total listening time (in seconds)
    total_playtime = 0.0
    for song in this_weeks_songs:
        total_playtime += song['track']['duration_ms']
    total_playtime = int(total_playtime // (60*1000))   # total playtime in minutes

    # Group songs by artist
    artist_data = group_songs_by_artist(this_weeks_songs, access_token, genres_by_artistid, popularity_by_artistid)

    # Compute mean popularity score
    hipster_score = int(100 - np.mean([item["popularity"] for item in artist_data]))

    # Calculate the time distribution
    time_distribution_data = calculate_time_distribution(this_weeks_songs)

    # Pass the genre data to the HTML template
    genre_data = [item["genres"] for item in artist_data]
    all_genres = np.array([item for sublist in genre_data for item in sublist])
    genre_data = json.dumps(genre_data)

    # TOP GENRES
    genres_counts = zip(*np.unique(all_genres, return_counts=True))
    top_genres = sorted(genres_counts, key=lambda x: x[1], reverse=True)[:4]
    top_genres = [tup[0].capitalize() for tup in top_genres]
    genre_colors = ["#F2542D", "#5603AD", "#F6F740", "#74D3AE"]  # red, purple, yellow, light sea green

    n_songs = sum(time_distribution_data)

    # try storing time distribution data into csv format
    time_data_df = pd.DataFrame({'hour': np.arange(1, 25), 'count': time_distribution_data})
    time_data_df.to_csv("static/time_distribution.csv", index=False)

    # Render the HTML template with the recently played songs data
    return render_template('index.html', artist_data=artist_data, start_date=start_date, time_distribution_data=time_distribution_data,
                           genre_data=genre_data, n_songs=n_songs, artist_counts=artist_counts, top_artists=top_artists,
                           top_artists_images_by_name=top_artists_images_by_name, total_playtime=total_playtime,
                           top_genres=top_genres, genre_colors=genre_colors, hipster_score=hipster_score)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'image'),
                               'favicon.ico', mimetype='image/png')


if __name__ == '__main__':
    DEBUG_FLAG = False
    app.run(host="0.0.0.0", port=port, debug=DEBUG_FLAG)
