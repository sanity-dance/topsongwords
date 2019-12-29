from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import nltk
import string
import re
import time as t
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import os.path
from os import path

# The goal of this prototype is to use the code from the fetching prototype to iteratively read the lyrics of the entire 2019 table and append
# the new information to the dataframe.
if path.exists('data/2019top10songswordcounts.csv'): #This code block checks to see if the iterative fetcher has already gotten some results, and picks up where it left off rather than starting from the beginning each time.
    songdata = pd.read_csv('data/2019top10songswordcounts.csv')
    init_index = int((songdata['Unique Words'] == 9999).idxmax())
else:
    songdata = pd.read_csv('data/2019top10songs.csv')
    songdata['Unique Words'] = 9999
    songdata['Total Words'] = 9999
    init_index = 0

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
cookies = { 'sessionid': '123..'}
url = 'https://www.azlyrics.com/lyrics/'

for i in range(init_index, len(songdata)):
    if int(songdata['Unique Words'][i]) != 9999: # If data has already been acquired for this entry, skip it and go to the next one.
        continue
    artist = songdata['Artist'][i] # artist1 and artist2 are the most common ways azlyrics represents artist names. artist1 removes spaces while artist2 replaces them with a dash.
    artist1 = ''.join(artist.split()).lower().replace('\'','').replace('!','').replace('.','').replace('+','').replace('ñ','n').replace('é','e')
    artist2 = artist.lower().replace('\'','').replace(' ','-').replace('!','').replace('.','').replace('+','').replace('ñ','n').replace('é','e')
    artistl = []
    if ', ' in artist: # Handles cases where there are three listed artists.
        artistl.append(artist1[:artist1.rfind(',')])
        artistl.append(artist1[artist1.find(',')+1:artist1.rfind('and')])
        artistl.append(artist1[artist1.rfind('and')+3:])
    elif ' and ' in artist: # Handles cases where there are two listed artists.
        artistl.append(artist1[:artist1.rfind('and')])
        artistl.append(artist2[:artist2.rfind('-and')])
        if ' featuring ' in artist: # Handles a case with multiple featured artists.
            artistl.append(artist1[:artist1.rfind('featuring')])
            artistl.append(artist2[:artist2.rfind('featuring')])
        artistl.append(artist1) # Cases where 'and' is in the artist name, ex. 'Tones and I'
    elif 'bts' in artist1: # Handles that one k-pop group.
        artistl.append('bangtanboys')
    elif ' featuring ' in artist: # Handles cases where there is a featured artist.
        artistl.append(artist1[:artist1.rfind('featuring')])
        artistl.append(artist2[:artist2.rfind('featuring')])
    else: # Handles cases where there is one artist (which is most of them)
        artistl.append(artist1)
        artistl.append(artist2)
        artistl.append(artist1[artist1.find('the')+3:]) # Handles a rare case where Wikipedia includes a "the" in the artist name and azlyrics does not.
    title = ''.join(songdata['Title'][i].split()).lower().replace('\'','').replace(',','').replace('!','').replace('ñ','n').replace('é','e') # azlyrics seems to represent all song titles in the same way.
    titlel = [title, 'a' + title, 'the' + title] # However, there are very rare cases, such as 'Holly Jolly Christmas', where azlyrics includes an 'a' or a 'the' at the beginning of a song and Wikipedia does not. These cases will only be tested if all of the artist configurations fail.
    if 'futsal' in title:
        titlel.insert(0,'futsalshuffle') # Handles a unique case where the Wikipedia song title includes a number and the azlyrics song title does not.
    success = False
    for j in range(len(titlel)):
        for k in range(len(artistl)):
            if requests.get(url + artistl[k] + '/' + titlel[j] + '.html').status_code == 200:
                html = requests.get(url + artistl[k] + '/' + titlel[j] + '.html',cookies=cookies,headers=headers).text
                soup = BeautifulSoup(html, 'lxml')
                success = True
                t.sleep(5)
                break
            t.sleep(5)
        if success: # Escapes the outer loop when URL succeeds without using a second request.
            break
        if j == len(titlel) - 1:
            print('Song ' + songdata['Title'][i] + ' by ' + artist + ' at position ' + str(i) + ' not found!')

    my_text = soup.find('div',attrs={'class': None}).text.replace('\n',' ')[3:] # Extract lyrics text from the azlyrics page and replace newlines with spaces. Also, eliminate the \r tag and space at the beginning.
    # try:
    #     my_text = my_text[:my_text.rindex("[")-1] # Remove miscellaneous notes at the end of lyrics.
    # except:
    #     my_text = my_text
    my_text = word_tokenize(my_text)
    my_text = [j.lower() for j in my_text if not re.fullmatch('[' + string.punctuation + ']+', j)] #Remove tokens that are just punctuation.

    port_stem = PorterStemmer() # The following code will stem the words in the lyrics. This means that, for example, "stop", "stopping", and "stops" will only count as one unique word.

    stem_text = []

    for k in range(len(my_text)):
        stem_text.append(port_stem.stem(my_text[k]))

    if success:
        songdata['Unique Words'][i] = len(set(stem_text))
        songdata['Total Words'][i] = len(my_text)
        print('Data on song ' + str(songdata['Title'][i]) + ' by artist ' + str(songdata['Artist'][i]) + ' successfully acquired!')

songdata.to_csv(path_or_buf='data/2019top10songswordcounts.csv',index=False,mode='w+') # Export our complete data table for 2019.
print('Operation complete!')