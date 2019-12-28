from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import datetime
import time as t
import os.path
from os import path

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
cookies = cookies = { 'sessionid': '123..'}
now = datetime.datetime.now()
songdata = pd.DataFrame(columns=['Top ten entry date','Title','Artist','Peak','Peak date','Number of weeks in top ten'])
if path.exists('data/top10songs.csv'):
    currentdata = pd.read_csv('data/top10songs.csv')
    init_year = int(currentdata['Year'][len(currentdata)-1]) + 1
else:
    init_year = 1958
for i in range(init_year,int(now.year)+1):
    try:
        html = requests.get('https://en.wikipedia.org/wiki/List_of_Billboard_Hot_100_top-ten_singles_in_' + str(i),cookies=cookies,headers=headers).text
        soup = BeautifulSoup(html, 'lxml')
        my_table = soup.find('table',{'class':'wikitable sortable'})

        Titles = []
        swiftcount = 0 # Keeps track of where repeat artists with rowspans greater than 1 should be inserted.
        drakecontingency = 0 # Used to keep track of how many rows have the same artist when the rowspan is greater than 1.

        # The following code mines the first table found on the Wikipedia page and extracts all table elements other than the annotations column.

        try:
            tds = my_table.findAll('td')
        except:
            my_table = soup.find('table',{'class':'wikitable'}) # Catch a case where the table is stored as a wikitable instead of a wikitable sortable.
            tds = my_table.findAll('td')

        for td in tds:
            try:
                if td.attrs['rowspan']:
                    taylorswift = td.get_text()[:-1]
                    swiftcount = 7
                    drakecontingency = int(td.attrs['rowspan']) - 1
            except KeyError:
                pass
            if td.get_text()[0] != '[' and td.get_text()[0] and td.get_text()[0].strip(): # Drop annotations column.
                if swiftcount == 1:
                    drakecontingency = drakecontingency-1;
                    # print(taylorswift + ' appended!')
                    Titles.append(taylorswift)
                    if drakecontingency == 0:
                        taylorswift = ''
                        swiftcount = 0
                    else:
                        swiftcount = 6;
                if swiftcount > 0:
                    swiftcount = swiftcount-1;
                Titles.append(td.get_text()[:-1]) # Drop the newline character present at the end of every single entry.

        nptitles = np.asarray(Titles).copy()
        numsongs = int(np.prod(nptitles.shape)/6) # Find out how many songs are in this list.
        reshaped = nptitles.reshape(numsongs,6) # Reshape the array based on the number of songs and the number of columns.
        newdata = pd.DataFrame(reshaped)
        newdata.columns = ['Top ten entry date','Title','Artist','Peak','Peak date','Number of weeks in top ten']
        newdata['Year'] = str(i)
        newdata['Title'] = [j[1:j.rfind('\"')] for j in newdata['Title']] # Drops quotation marks and annotations in Title.
        for j in newdata['Top ten entry date']:
            if '[' in j:
                j = j[:j.rfind('[')-1] # Catch a rare case where there is an annotation in the top ten entry date.
        if(i == now.year):
            cleanweeks = []
            for j in newdata['Number of weeks in top ten']: # This code searches the number of weeks in top ten column for asterisks and eliminates them. 
                try:                                         # This is only a problem in the current year.
                    cleanweeks.append(int(j[:j.rindex('*')]))
                except:
                    cleanweeks.append(int(j))
            newdata['Number of weeks in top ten'] = cleanweeks
        songdata = songdata.append(newdata, ignore_index=True)
        print('Data for ' + str(i) + ' acquired!')
        if i == now.year:
            print('Data acquisition successful!')
        else:
            t.sleep(15) # Delay between requests, for politeness' sake.
    except:
        print('Exception occurred at year ' + str(i) + '! Operation ' + '{:.0%} completed!'.format((i-1958)/(int(now.year)-1958)))
        break

if init_year != 1958: #Check if this is the first run or not.
    songdata.to_csv(path_or_buf='data/top10songs.csv',index=False,header=False,mode='a') #Appends current data to existing file.
else:
    songdata.to_csv(path_or_buf='data/top10songs.csv',index=False,header=True,mode='w') #Creates new file with current data.