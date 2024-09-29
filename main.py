from billboard.get_top_songs import get_top_100, get_top_100_wikipedia

from genius.utils import get_lyrics_url, get_taboo_lyrics

# Get Top 100 Artists Based on Year

years = list(range(1960, 2024))

for year in ["2023"]:
    # TODO: Parallelize computations using multi-threads or multiprocessing
    # 4 x 25 or 2 x 50
    
    # Get Top 100 Songs
    df_artists = get_top_100_wikipedia(year)
    df_artists.to_csv("test2.csv")

    # Get Genius URLs to extract lyrics
    urls = []
    index = 1
    for row in df_artists.itertuples():
        url = get_lyrics_url(row.song, row.artist)
        print(index, url)
        urls.append(url)
        index += 1
    df_artists["lyric_url"] = urls
    
    # Extract Lyrics and Keep Count of Explicit Curse/"Taboo" Words
    taboo_list = []
    for row in df_artists.itertuples():
        taboo_dict = get_taboo_lyrics(row.lyric_url)
        taboo_list.append(taboo_dict)
        print(taboo_dict)

    df_artists["taboo_dict"] = taboo_list
    df_artists.to_csv(f"top-songs-{year}.csv")
    break
