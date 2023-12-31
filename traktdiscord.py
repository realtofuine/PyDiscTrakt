# pyinstaller --clean pydisctrakt.spec

import calendar
import configparser
import json
import os.path
import sys
import time
from datetime import datetime

import requests
import tmdbsimple as tmdb
import trakt
import trakt.core
from pypresence import Presence
from trakt import init
from trakt.movies import Movie
from trakt.tv import TVEpisode, TVShow
from trakt.users import User


def UTC_time_to_epoch(timestamp):
  epoch = calendar.timegm(timestamp.utctimetuple())
  return epoch

config = configparser.ConfigParser()

CWD = os.path.abspath(os.path.dirname(sys.executable))

config.read(os.path.join(CWD, "config.ini"))

# config.read('config.ini') # for testing, uncomment this line and comment the above line

trakt.core.AUTH_METHOD = trakt.core.OAUTH_AUTH

if config['DEFAULT']['trakt.USERNAME'] == "":
    username = input("Enter your trakt username: ")
    config.set('DEFAULT', 'trakt.USERNAME', str(username))

if config['DEFAULT']['trakt.CLIENT_ID'] == "":
    print("If you do not have a client ID and secret, please visit the following url to create them. http://trakt.tv/oauth/applications")
    client_id = input("Enter your trakt client id: ")
    config.set('DEFAULT', 'trakt.CLIENT_ID', str(client_id))

if config['DEFAULT']['trakt.CLIENT_SECRET'] == "":
    print("If you do not have a client ID and secret, please visit the following url to create them. http://trakt.tv/oauth/applications")
    client_secret = input("Enter your trakt client secret: ")
    config.set('DEFAULT', 'trakt.CLIENT_SECRET', str(client_secret))

if config['DEFAULT']['trakt.OAUTH_TOKEN'] == "":
    oauth = init(config['DEFAULT']['trakt.username'], config['DEFAULT']['trakt.CLIENT_ID'], config['DEFAULT']['trakt.CLIENT_SECRET'])

    config.set('DEFAULT', 'trakt.OAUTH_TOKEN', oauth)

if config['DEFAULT']['tmdb.api_key'] == "":
    print("If you do not have a TMDB api key, please visit the following url to create one. https://www.themoviedb.org/settings/api")
    api_key = input("Enter your TMDB api key: ")

    config.set('DEFAULT', 'tmdb.api_key', api_key)

if config['DEFAULT']['discord.client_id'] == "":
    print("If you do not have a Discord client ID, please visit the following url to create one. https://discord.com/developers/applications")
    client_id = input("Enter your Discord client ID: ")

    config.set('DEFAULT', 'discord.client_id', client_id)


with open(os.path.join(CWD, "config.ini"), 'w') as configfile:
    config.write(configfile)

trakt.core.OAUTH_TOKEN = config['DEFAULT']['trakt.OAUTH_TOKEN']
trakt.core.CLIENT_ID = config['DEFAULT']['trakt.CLIENT_ID']
trakt.core.CLIENT_SECRET= config['DEFAULT']['trakt.CLIENT_SECRET']

tmdb.API_KEY= config['DEFAULT']['tmdb.api_key']
tmdb.REQUESTS_TIMEOUT = 15

s = requests.Session()
s.headers.update({'content-type': 'application/json', 'trakt-api-key': config['DEFAULT']['trakt.CLIENT_ID'], 'trakt-api-version': '2', 'Authorization' : 'Bearer ' + config['DEFAULT']['trakt.OAUTH_TOKEN']})

my = User(config['DEFAULT']['trakt.USERNAME'])

print(my)

RPC = Presence(config['DEFAULT']['discord.client_id'])

while True:
    try:
        RPC.connect() # Start the handshake loop
    except:
        print("Error connecting to Discord. Retrying in 5 seconds...")
        time.sleep(5)
        continue
    else:
        break

print(RPC.update(state="Started", details="Started!", large_image="movies"))  # Set the presence

currentTime = time.time()
while(True):
    response = s.get("https://api.trakt.tv/users/" + config['DEFAULT']['trakt.USERNAME'] + "/watching")

    show = my.watching
    if(response.status_code == 204):
        print("None")
        RPC.clear()
        time.sleep(5)
    elif isinstance(show, TVEpisode):
        endTime = UTC_time_to_epoch(datetime.strptime(response.json()['expires_at'], '%Y-%m-%dT%H:%M:%S.%fZ'))

        if(tmdb.TV(tmdb.Find(show.ids['ids']['imdb']).info == "None")):
            movie = tmdb.TV(tmdb.Search().tv(query=show.show)['results'][0]['id'])
        else:
            movie = tmdb.TV(tmdb.Find(show.ids['ids']['imdb']).info(external_source='imdb_id')['tv_episode_results'][0]['show_id'])

        movie.info()
        dets = movie.info()['name']
        url = "https://image.tmdb.org/t/p/w780" + movie.info()['backdrop_path']
        title = str(show)[13 + len(dets):]

        if show.ids['ids']['imdb'] is None:
            imdburl = "https://imdb.com"
        else:
            imdburl = "https://imdb.com/title/" + show.ids['ids']['imdb']
            
        print(RPC.update(state=title, details=dets, large_image=url, small_image="trakt", end = endTime, buttons = [{"label": "IMDB", "url": imdburl}]))
        time.sleep(5)
    elif isinstance(show, Movie):
        endTime = UTC_time_to_epoch(datetime.strptime(response.json()['expires_at'], '%Y-%m-%dT%H:%M:%S.%fZ'))
        movie = tmdb.Movies(show.to_json()['movies'][0]['ids']['tmdb'])
        movie.info()
        imdburl = "https://imdb.com/title/" + movie.info()['imdb_id']
        url = "https://image.tmdb.org/t/p/w780" + movie.info()['backdrop_path']
        print(RPC.update(details=movie.title, state="Rating: " + str(show.ratings['rating']) + " ⭐", large_image=url, small_image="trakt", end = endTime, buttons = [{"label": "IMDB", "url": imdburl}]))
        time.sleep(5)
    else:
        RPC.clear()
        print("Not a movie or TV show! File a bug report and tell what you were watching!")
        time.sleep(5)