# pyinstaller --clean exefilename.spec --noconfirm

import configparser
import json
import os.path
import sys
import time

import tmdbsimple as tmdb
import trakt
import trakt.core
from pypresence import Presence
from trakt import init
from trakt.movies import Movie
from trakt.tv import TVEpisode, TVShow
from trakt.users import User

config = configparser.ConfigParser()

CWD = os.path.abspath(os.path.dirname(sys.executable))

config.read(os.path.join(CWD, "config.ini"))

# config.read('config.ini') # for testing, uncomment this line and comment the above line

trakt.core.AUTH_METHOD = trakt.core.OAUTH_AUTH

if config['DEFAULT']['trakt.USERNAME'] == "":
    username = input("Enter your trakt username: ")
    config.set('DEFAULT', 'trakt.USERNAME', str(username))

if config['DEFAULT']['trakt.CLIENT_ID'] == "":
    print("If you do not have a client ID and secret. Please visit the following url to create them. http://trakt.tv/oauth/applications")
    client_id = input("Enter your trakt client id: ")
    config.set('DEFAULT', 'trakt.CLIENT_ID', str(client_id))

if config['DEFAULT']['trakt.CLIENT_SECRET'] == "":
    print("If you do not have a client ID and secret. Please visit the following url to create them. http://trakt.tv/oauth/applications")
    client_secret = input("Enter your trakt client secret: ")
    config.set('DEFAULT', 'trakt.CLIENT_SECRET', str(client_secret))

if config['DEFAULT']['trakt.OAUTH_TOKEN'] == "":
    oauth = init(config['DEFAULT']['trakt.username'], config['DEFAULT']['trakt.CLIENT_ID'], config['DEFAULT']['trakt.CLIENT_SECRET'])

    config.set('DEFAULT', 'trakt.OAUTH_TOKEN', oauth)

if config['DEFAULT']['tmdb.api_key'] == "":
    print("If you do not have a TMDB api key. Please visit the following url to create one. https://www.themoviedb.org/settings/api")
    api_key = input("Enter your TMDB api key: ")

    config.set('DEFAULT', 'tmdb.api_key', api_key)

if config['DEFAULT']['discord.client_id'] == "":
    print("If you do not have a Discord client ID. Please visit the following url to create one. https://discord.com/developers/applications")
    client_id = input("Enter your Discord client ID: ")

    config.set('DEFAULT', 'discord.client_id', client_id)


with open('config.ini', 'w') as configfile:
    config.write(configfile)

trakt.core.OAUTH_TOKEN = config['DEFAULT']['trakt.OAUTH_TOKEN']
trakt.core.CLIENT_ID = config['DEFAULT']['trakt.CLIENT_ID']
trakt.core.CLIENT_SECRET= config['DEFAULT']['trakt.CLIENT_SECRET']

tmdb.API_KEY= config['DEFAULT']['tmdb.api_key']
tmdb.REQUESTS_TIMEOUT = 15

my = User(config['DEFAULT']['trakt.USERNAME'])

print(my)

RPC = Presence(config['DEFAULT']['discord.client_id'])

RPC.connect() # Start the handshake loop
print(RPC.update(state="Started", details="Started!", large_image="movies"))  # Set the presence

currentTime = time.time()
while(True):

    show = my.watching
    if(show is None):
        print("None")
        RPC.clear()
        currentTime = time.time()
        time.sleep(5)
    elif isinstance(show, TVEpisode):
        movie.info()
        dets = movie.info()['name']
        url = "https://image.tmdb.org/t/p/w780" + movie.info()['backdrop_path']
        title = str(show)[13 + len(dets):]
        imdburl = "https://imdb.com/title/" + show.ids['ids']['imdb']
        print(RPC.update(state=title, details=dets, large_image=url, small_image="trakt", start = currentTime, buttons = [{"label": "IMDB", "url": imdburl}]))
        time.sleep(5)
    elif isinstance(show, Movie):
        movie = tmdb.Movies(show.to_json()['movies'][0]['ids']['tmdb'])
        movie.info()
        imdburl = "https://imdb.com/title/" + movie.info()['imdb_id']
        url = "https://image.tmdb.org/t/p/w780" + movie.info()['backdrop_path']
        print(RPC.update(details=movie.title, state="Rating: " + str(show.ratings['rating']) + " ⭐", large_image=url, small_image="trakt", start = currentTime, buttons = [{"label": "IMDB", "url": imdburl}]))
        time.sleep(5)
    else:
        RPC.clear()
        print("Not a movie or TV show! File a bug report and tell what you were watching!")
        time.sleep(5)