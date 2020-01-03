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
import lyricsgenius
genius = lyricsgenius.Genius("your_token_here")
genius.remove_section_headers = True
genius.verbose = False

if path.exists('data/top10songswordcounts.csv'): #This code block checks to see if the iterative fetcher has already gotten some results, and picks up where it left off rather than starting from the beginning each time.
    songdata = pd.read_csv('data/top10songswordcounts.csv')
    init_index = int((songdata['Unique Words'] == 9999).idxmax())
else:
    songdata = pd.read_csv('data/top10songs.csv')
    songdata['Unique Words'] = 9999
    songdata['Total Words'] = 9999
    init_index = 0

instrumentalindices = [1,5,24,27,51,56,80,93,101,110,162,177,190,231,286,307,329,353,365,383,410,433,434,466,472,533,556,565,621,733,753,1041,1043,1049,1092,
                        1102,1123,1135,1195,1379,1392,1423,1455,1494,1515,1561,1584,1757,1804,1857,1877,1949,1950,2071,2111,2278,2292,2576,2806,2620]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
cookies = { 'sessionid': '123..'}
url = 'https://www.azlyrics.com/lyrics/'
failcount = 0

try:
    for i in range(init_index, len(songdata)):
        if int(songdata['Unique Words'][i]) != 9999 or i in instrumentalindices: # If data has already been acquired for this entry, skip it and go to the next one.
            continue
        artist = songdata['Artist'][i] # artist1 and artist2 are the most common ways azlyrics represents artist names. artist1 removes spaces while artist2 replaces them with a dash.
        artist1 = ''.join(artist.split()).lower().replace('\'','').replace('!','').replace('.','').replace('+','').replace('ñ','n').replace('é','e').replace('ö','o').replace('ü','u')
        artist2 = artist.lower().replace('\'','').replace(' ','-').replace('!','').replace('.','').replace('+','').replace('ñ','n').replace('é','e').replace('ö','o').replace('ü','u')
        artistl = []
        if ', ' in artist: # Handles cases where there are three listed artists.
            artistl.append(artist1[:artist1.rfind(',')])
            artistl.append(artist1[artist1.find(',')+1:artist1.rfind('and')])
            artistl.append(artist1[artist1.rfind('and')+3:])
        elif ' with ' in artist:
            artistl.append(artist1[:artist1.rfind('with')])
            artistl.append(artist2[:artist2.rfind('-with')])
        elif ' and ' in artist: # Handles cases where there are two listed artists.
            artistl.append(artist1[:artist1.rfind('and')])
            artistl.append(artist2[:artist2.rfind('-and')])
            if ' featuring ' in artist: # Handles a case with multiple featured artists.
                artistl.append(artist1[:artist1.rfind('featuring')])
                artistl.append(artist2[:artist2.rfind('featuring')])
            artistl.append(artist1) # Cases where 'and' is in the artist name, ex. 'Tones and I'
        elif '&' in artist: # Handles cases where there are two listed artists.
            artistl.append(artist1[:artist1.rfind('&')])
            artistl.append(artist2[:artist2.rfind('-&')])
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
            if 'the' in artist:
                artistl.append(artist1[artist1.find('the')+3:]) # Handles a rare case where Wikipedia includes a "the" in the artist name and azlyrics does not.
        titlel = []
        title = ''.join(songdata['Title'][i].split()).lower().replace('\'','').replace(',','').replace('.','').replace('!','').replace('?','').replace('ñ','n').replace('é','e') # azlyrics seems to represent all song titles in the same way.
        titlel.append(title.replace('(','').replace(')','')) # Removal of parentheses is handled here because logic checks for parentheses in title later.
        if 'Holly Jolly Christmas' in title: # Handles the Holly Jolly Christmas scenario.
            titlel.append('a' + title)
        if 'futsal' in title:
            titlel.insert(0,'futsalshuffle') # Handles a unique case where the Wikipedia song title includes a number and the azlyrics song title does not.
        if '(' in title: # Handles song titles with parenthetical alternate titles.
            titlel.append(title[title.find('(')+1:title.rfind(')')])
            titlel.append(title[:title.find('(')])
            titlel.append(title[title.rfind(')'):])
        if '\" / \"' in songdata['Title'][i]:
            titlel.append(title[:title.find('\"')])
            titlel.append(title[title.rfind('\"'):])
        success = False
        geniusl = []
        if ', ' in artist: # Handles cases where there are three listed artists.
            geniusl.append(artist[:artist.rfind(',')])
            geniusl.append(artist[artist.find(',')+1:artist1.rfind(' and ')])
            geniusl.append(artist[artist.rfind(' and ')+5:])
        elif ' with ' in artist:
            geniusl.append(artist[:artist.rfind(' with')])
        elif ' and ' in artist: # Handles cases where there are two listed artists.
            geniusl.append(artist[:artist.rfind(' and')])
            if ' featuring ' in artist: # Handles a case with multiple featured artists.
                geniusl.append(artist[:artist.rfind(' featuring ')])
            geniusl.append(artist) # Cases where 'and' is in the artist name, ex. 'Tones and I'
        elif ' & ' in artist: # Handles cases where there are two listed artists.
            geniusl.append(artist[:artist.rfind(' &')])
            if ' featuring ' in artist: # Handles a case with multiple featured artists.
                geniusl.append(artist[:artist.rfind(' featuring ')])
            geniusl.append(artist) # Cases where 'and' is in the artist name, ex. 'Tones and I'
        elif ' featuring ' in artist: # Handles cases where there is a featured artist.
            geniusl.append(artist[:artist.rfind(' featuring ')])
        else: # Handles cases where there is one artist (which is most of them)
            if 'the' in artist:
                geniusl.append(artist[artist.find('the ')+4:])
            if 'The' in artist:
                geniusl.append(artist[artist.find('The ')+4:])
            geniusl.append(artist)
            if 'Miss' in artist: # Catches the wily Toni Fisher.
                geniusl.append(artist[artist.find('Miss ')+5])
            if 'Show' in artist:
                geniusl.append(artist[artist.find('The ')+4:artist.rfind(' Show')]) # Handles some cases from the 50s and 60s.
        for j in range(len(titlel)):
            for k in range(len(artistl)):
                if requests.get(url + artistl[k] + '/' + titlel[j] + '.html').status_code == 200:
                    html = requests.get(url + artistl[k] + '/' + titlel[j] + '.html',cookies=cookies,headers=headers).text
                    soup = BeautifulSoup(html, 'lxml')
                    success = True
                    t.sleep(3)
                    break
                t.sleep(3)
            if success: # Escapes the outer loop when URL succeeds without using a second request.
                break
            if j == len(titlel) - 1:
                print('Song ' + songdata['Title'][i] + ' by ' + artist + ' at position ' + str(i) + ' not found on azlyrics!')
        
        if success:
            my_text = soup.find('div',attrs={'class': None}).text.replace('\n',' ')[3:] # Extract lyrics text from the azlyrics page and replace newlines with spaces. Also, eliminate the \r tag and space at the beginning.
            my_text = word_tokenize(my_text)
            my_text = [j.lower() for j in my_text if not re.fullmatch('[' + string.punctuation + ']+', j)] #Remove tokens that are just punctuation.
        
        if success == False: # Use this method second because it is less precise and has a risk of returning false results.
            for l in range(len(geniusl)):
                try:
                    if genius.search_song(songdata['Title'][i],geniusl[l]) != None:
                        while True:
                            try:
                                currentsong = genius.search_song(songdata['Title'][i],geniusl[l])
                                t.sleep(1)
                                break
                            except:
                                pass
                        success = True
                        t.sleep(3)
                        break
                    t.sleep(3)
                    if '\" / \"' in songdata['Title'][i]:
                        if genius.search_song(songdata['Title'][i][songdata['Title'][i].find('\"'):],geniusl[l]) != None:
                            while True:
                                try:
                                    currentsong = genius.search_song(songdata['Title'][i][songdata['Title'][i].find('\"'):],geniusl[l])
                                    t.sleep(1)
                                    break
                                except:
                                    pass
                            success = True
                            t.sleep(3)
                            break
                        if genius.search_song(songdata['Title'][i][:songdata['Title'][i].rfind('\"')],geniusl[l]) != None:
                            while True:
                                try:
                                    currentsong = genius.search_song(songdata['Title'][i][:songdata['Title'][i].rfind('\"')],geniusl[l])
                                    t.sleep(1)
                                    break
                                except:
                                    pass
                            success = True
                            t.sleep(3)
                            break
                except:
                    continue
                if success == True:
                    my_text = currentsong.lyrics
                    my_text = word_tokenize(my_text)
                    my_text = [i.lower() for i in my_text if not re.fullmatch('[' + string.punctuation + ']+', i)] #Remove tokens that are just punctuation.

        if success == False:
            print('Song ' + songdata['Title'][i] + ' by ' + artist + ' at position ' + str(i) + ' not found!')
            failcount += 1
        
        port_stem = PorterStemmer() # The following code will stem the words in the lyrics. This means that, for example, "stop", "stopping", and "stops" will only count as one unique word.

        stem_text = []

        for k in range(len(my_text)):
            stem_text.append(port_stem.stem(my_text[k]))

        if success:
            songdata['Unique Words'][i] = len(set(stem_text))
            songdata['Total Words'][i] = len(my_text)
            print('Data on song ' + str(songdata['Title'][i]) + ' by artist ' + str(songdata['Artist'][i]) + ' successfully acquired! ' + str(len(set(stem_text))) + ' ' + str(len(my_text)))
except:
    print('Exception occurred at position ' + str(i) + '!')
    songdata.to_csv(path_or_buf='data/top10songswordcounts.csv',index=False,mode='w+') # Export our in progress data table.


songdata.to_csv(path_or_buf='data/top10songswordcounts.csv',index=False,mode='w+') # Export our complete data table.
if failcount != 1:
    print('Operation complete! ' + str(failcount) + ' songs missing!')
else:
    print('Operation complete! ' + str(failcount) + ' song missing!')