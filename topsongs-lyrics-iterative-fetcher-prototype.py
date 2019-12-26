from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import nltk
import string
import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# The goal of this prototype is to use the code from the fetching prototype to iteratively read the lyrics of the entire 2019 table and append
# the new information to the dataframe.

songdata = pd.read_csv('data/2019top10songs.csv')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
cookies = { 'sessionid': '123..'}
url = 'https://www.azlyrics.com/lyrics/'
uniquewords = []
totalwords = []

for i in range(len(songdata)):
    artist = songdata['Artist'][i] # artist1 and artist2 are the most common ways azlyrics represents artist names. artist1 removes spaces while artist2 replaces
                                   # them with a dash. artist3 and artist4 handle the way that Wikipedia presents collaborations.
    artist1 = ''.join(artist.split()).lower().replace('\'','').replace('!','').replace('.','').replace('+','').replace('ñ','n')
    artist2 = artist.lower().replace('\'','').replace(' ','-').replace('!','').replace('.','').replace('+','').replace('ñ','n')
    artistl = [artist1, artist2, artist1[:artist1.rfind('and')], artist2[:artist2.rfind('-and')], artist2[:artist2.rfind('featuring')], artist1[:artist1.rfind(',')], artist1[artist1.find(','):artist1.rfind('and')], artist1[artist1.rfind('and')+3:]]
    title = ''.join(songdata['Title'][i].split()).lower().replace('\'','').replace(',','').replace('!','') # azlyrics seems to represent all song titles in the same way.
    artistl = [artist1, artist2, artist1[:artist1.rfind('and')], artist2[:artist2.rfind('-and')], artist1[:artist1.rfind('featuring')], artist2[:artist2.rfind('featuring')], artist1[:artist1.rfind(',')], artist1[artist1.find(',')+1:artist1.rfind('and')], artist1[artist1.rfind('and')+3:],artist1[artist1.find('the')+3:]]
    # The first three entries of the above list are standard single artist titles. The next three handle cases of collaborations between two artists. The next four after that handle collaborations between three artists. The last entry handles a rare case where Wikipedia includes a "the" in the artist name and azlyrics does not.
    title = ''.join(songdata['Title'][i].split()).lower().replace('\'','').replace(',','').replace('!','').replace('ñ','n') # azlyrics seems to represent all song titles in the same way.
    titlel = [title, 'a' + title, 'the' + title] # However, there are very rare cases, such as 'Holly Jolly Christmas', where azlyrics includes an 'a' or a 'the' at the beginning of a song and Wikipedia does not. These cases will only be tested if all of the artist configurations fail.
    for j in range(len(titlel)):
        for k in range(len(artistl)):
            if requests.get(url + artistl[k] + '/' + titlel[j] + '.html').status_code == 200:
                html = requests.get(url + artistl[k] + '/' + titlel[j] + '.html',cookies=cookies,headers=headers).text
                soup = BeautifulSoup(html, 'lxml')
                break
        if requests.get(url + artistl[k] + '/' + titlel[j] + '.html').status_code == 200:
            break
        if 'bts' in artistl:
            if requests.get(url + 'bangtanboys' + '/' + titlel[j] + '.html').status_code == 200:
                html = requests.get(url + 'bangtanboys' + '/' + titlel[j] + '.html',cookies=cookies,headers=headers).text
                soup = BeautifulSoup(html, 'lxml')
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

    uniquewords.append(len(set(stem_text)))

    totalwords.append(len(my_text))

songdata['Unique Words'] = uniquewords
songdata['Total Words'] = totalwords

songdata.to_csv(path_or_buf='data/2019top10songswordcounts.csv',index=False) # Export our complete data table for 2019.