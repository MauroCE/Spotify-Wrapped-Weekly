from flask import Flask, render_template
from main import get_token, get_recently_played, get_track_genre, get_artist_genres
from datetime import datetime, timedelta, date, time
import os
import json
from collections import defaultdict

app = Flask(__name__)

port = int(os.environ.get("PORT", 5000))  # Use 5000 as the default port




def group_songs_by_artist(recently_played, access_token):
    # Create a dictionary to store songs grouped by artist and their genres
    artist_dict = defaultdict(lambda: {"songs": [], "genres": []})

    for item in recently_played:
        artist_name = item["track"]["artists"][0]["name"]
        song_name = item["track"]["name"]

        # Retrieve artist details to get genre information
        artist_id = item["track"]["artists"][0]["id"]
        genres = get_artist_genres(access_token, artist_id)

        artist_dict[artist_name]["songs"].append(song_name)
        artist_dict[artist_name]["genres"].extend(genres)

    # Convert the dictionary into a list of dictionaries
    artist_list = [{"artist": artist, "songs": data["songs"], "genres": data["genres"]} for artist, data in artist_dict.items()]

    return artist_list


def calculate_time_distribution(recently_played):
    # Initialize a list to store the count of songs for each hour of the day
    time_distribution = [0] * 24

    for item in recently_played:
        played_at = datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ")  # Updated format string
        hour = played_at.hour
        time_distribution[hour] += 1

    return time_distribution


@app.route('/')
def index():
    # Your Spotify API code here (similar to your existing code)
    access_token = get_token()
    # Find Monday 00:00, i.e. midnight of Monday of the current week
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())
    start_date = datetime.combine(current_week_start, time.min)
    recently_played = get_recently_played(access_token, start_date)

    # Group songs by artist
    artist_data = group_songs_by_artist(recently_played, access_token)

    # Calculate the time distribution
    time_distribution_data = calculate_time_distribution(recently_played)

    # Pass the genre data to the HTML template
    genre_data = [item["genres"] for item in artist_data]
    genre_data = json.dumps(genre_data)

    # Render the HTML template with the recently played songs data
    return render_template('index.html', artist_data=artist_data, start_date=start_date, time_distribution_data=time_distribution_data, genre_data=genre_data)

# Define your get_token and get_recently_played functions here (as in your existing code)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port)
