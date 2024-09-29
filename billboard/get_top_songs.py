import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

CURRENT_YEAR_URL = "https://www.billboard.com/charts/hot-100/"

def get_top_100(year:str=None) -> pd.DataFrame:
    """
    Scrape songs and artists from billboard.com Hot 100.
        If year is not provided, defaults to current month's Hot 100.
        If provided returns dataframe of Hot 100 artists of given year.
    """
    if not year:
        response = requests.get(CURRENT_YEAR_URL)
    else:
        response = requests.get(f"https://www.billboard.com/charts/year-end/{year}/hot-100-songs/")

    html = BeautifulSoup(response.text, 'html.parser')
        
    song_rows = html.find_all("div", "o-chart-results-list-row-container")

    top_songs = {}
    for index, row in enumerate(song_rows, 1):
        parent = row.find("h3", id="title-of-a-story").find_parent("li")
        song_name = parent.find("h3").text.strip()
        artist_name = parent.find("span").text.strip()
        top_songs[index] = {"artist": artist_name, "song": song_name}
    
    df = pd.DataFrame.from_dict(top_songs, orient="index")        
    return df


def get_top_100_wikipedia(year:str=None) -> pd.DataFrame:
    """
    Get Top 100 Songs off of Wikipedia.
    """
    if not year:
        response = requests.get(CURRENT_YEAR_URL)
    else:
        response = requests.get(f"https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_{year}")
    
    html = BeautifulSoup(response.text, 'html5lib')
    table = html.find("table", "wikitable").find("tbody")
    rows = table.find_all("tr")
    
    top_songs = {}
    previous_artist = None
    for index, row in enumerate(rows[1:], 1): # First element is header
        td_elmts = row.find_all("td")
        song = td_elmts[1].text.strip().strip('"')
        if len(td_elmts) == 2:
            artist = previous_artist
        else:
            artist = td_elmts[2].text.strip()
            previous_artist = artist
        
        top_songs[index] = {"artist": artist, "song": song}

    if len(top_songs) != 100: raise Exception(f"Extracted {len(top_songs)} instead of 100.")
    return pd.DataFrame.from_dict(top_songs, orient="index")
