from strsimpy.normalized_levenshtein import NormalizedLevenshtein
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from collections import Counter
import urllib.parse
import unidecode
import requests
import os
import re
import spacy

# Environ Var
load_dotenv(".env.local")
GENIUS_API_URL = "https://api.genius.com/"
GENIUS_ACCESS_TOKEN = os.environ["GENIUS_CLIENT_ACCESS_TOKEN"]
TABOO_FILE_PATH =  os.environ["TABOO_FILE_PATH"]

# For string similarity scoring
LEVENSHTEIN = NormalizedLevenshtein()

# Lemmatization
NLP = spacy.load("en_core_web_lg")

def get_lyrics_url(song: str, artist: str) -> str | None:
    """
    Return Lyric Page URL given song and artist name using MusixMatch API.
    """
    url = GENIUS_API_URL + "search?q=" + urllib.parse.quote(f"{song}")
    headers = {
        "Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"
    }
    
    response = requests.get(url, headers=headers)
    response = response.json()
    
    if response["meta"]["status"] != 200:
        raise Exception("Error accessing API")
    
    highest_score = -1
    most_similar_track = None
    for track in response["response"]["hits"]:
        if track["type"] != "song":
            continue
                
        # If similarity scores are high, then return this track id        
        track_score = _jaccard_similarity_score(song, track["result"]["title"])
        artist_score = _levenshtein_similarity_score(artist, track["result"]["primary_artist"]["name"])
        score = track_score + artist_score
        if score >= highest_score:
            highest_score = score
            most_similar_track = track["result"]["url"]
            
    if highest_score != 2:
        print(highest_score)
    
    return most_similar_track

def _preprocess_string(string):
    """
    Lowercase and get rid of accent marks and punctuation.
    Remove (feat. [artist name]) from all strings.
    """
    # Remove (feat. [artist name]) pattern
    string = re.sub(r"\(feat\..*?\)", "", string).strip()
    
    # Remove accent marks
    string = unidecode.unidecode(string)
    
    # Remove punctuation (except alphanumeric and spaces) and convert to lowercase
    string = re.sub(r'[^a-zA-Z0-9\s]', '', string).lower()
    
    # Remove extra white spaces (leading, trailing, and multiple spaces)
    string = ' '.join(string.split())
    
    return string

def _jaccard_similarity_score(str1, str2):
    """
    Intended for artist names. Words like (feat, and, X) are often used for colloboration.
    At minimum the str1 should have the same artists as str2 if score is >=66%; unless there
    are typos or discrepenacies on agreed upon artist names.
    """
    A = set(filter(None, _preprocess_string(str1).split(" ")))
    B = set(filter(None, _preprocess_string(str2).split(" ")))
    
    conflict_words = ["feat", "featuring", "&", "x"]
    for word in conflict_words:
        if word in A:
            A.remove(word)
        if word in B:
            B.remove(word)

    C = A.intersection(B)
    D = A.union(B)
    return float(len(C))/float(len(D))

def _levenshtein_similarity_score(str1, str2):
    """
    Intended for song titles.
    """
    str1 = _preprocess_string(str1)
    str2 = _preprocess_string(str2)
    return 1 - LEVENSHTEIN.distance(str1, str2)

def get_taboo_lyrics(url: str) -> Counter:
    
    # Load Taboo Words into Set
    f = open(TABOO_FILE_PATH, 'r')
    taboo_words = taboo_words = set(word.strip() for word in f)
    f.close()
    
    # Get HTML Page from Genius
    res = requests.get(url)
    if res.status_code != 200:
        print(f"Error fetching URL: {res.status_code}")
        raise Exception("Error fetching lyric page")
    
    # Extract Lyrics
    html = BeautifulSoup(res.text, "html5lib")
    lyrics_container = html.find_all('div', attrs={"data-lyrics-container": "true"})
    words = Counter()

    for container in lyrics_container:
        lyrics_text = container.get_text(separator="\n")
        lyrics_text = lyrics_text.replace('\u205f', ' ')
        lyrics_text = re.sub(r'\[[\s\S]*?\]|[^\w\s]', '', lyrics_text).lower()
        lyrics_text = re.sub(r'\s+', ' ', lyrics_text.replace('\n', ' ')).strip()
        lyrics_lines = lyrics_text.split()
        
        # Add Taboo Words into a dictionary
        for word in lyrics_lines:
            word = str(NLP(word))
            if word in taboo_words:
                words[word] += 1 
    
    return words
            