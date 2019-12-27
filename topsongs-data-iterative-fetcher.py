from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import datetime
import time as t

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
cookies = cookies = { 'sessionid': '123..'}
now = datetime.datetime.now()
songdata = pd.DataFrame(columns=['Title','Artist','Peak','Number of weeks in top ten','Year'])
for i in range(1958,int(now.year)+1):
    html = requests.get('https://en.wikipedia.org/wiki/List_of_Billboard_Hot_100_top-ten_singles_in_' + str(i),cookies=cookies,headers=headers).text
    soup = BeautifulSoup(html, 'lxml')
    my_table = soup.find('table',{'class':'wikitable sortable'})

    Titles = []
    swiftcount = 0 # Keeps track of where repeat artists with rowspans greater than 1 should be inserted.
    drakecontingency = 0 # Used to keep track of how many rows have the same artist when the rowspan is greater than 1.

    # The following code mines the first table found on the Wikipedia page and extracts only table elements that do not correspond to a month and date. We don't care about the exact month and day that the song achieved Top 10 glory or their peak date. Furthermore, the way Wikipedia's tables are formatted, there are occasionally multiple songs that were all entered on the same day, and that date is listed only once, which creates problems for our script later down the road.

    try:
        tds = my_table.findAll('td')
    except:
        my_table = soup.find('table',{'class':'wikitable'}) # Catch a case where the table is stored as a wikitable instead of a wikitable sortable.
        tds = my_table.findAll('td')

    for td in tds:
        try:
            d = datetime.datetime.strptime(td.get_text()[:-1], "%B %d") # Check if the current string is a Month Day format.
        except ValueError:
            try:
                d = datetime.datetime.strptime(td.get_text()[:td.get_text().rfind('(')-1], "%B %d") # Catch a rare case where a song from the previous year charted again.
            except ValueError:
                try:
                    d = datetime.datetime.strptime(td.get_text()[:td.get_text().rfind('[')-1], "%B %d") # Catch a rare case where a song's top ten entry date has an annotation.
                except ValueError:
                    try:
                        if td.attrs['rowspan']:
                            taylorswift = td.get_text()[:-1]
                            swiftcount = 5
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
                                swiftcount = 4;
                        if swiftcount > 0:
                            swiftcount = swiftcount-1;
                        Titles.append(td.get_text()[:-1]) # Drop the newline character present at the end of every single entry.

    nptitles = np.asarray(Titles).copy()
    numsongs = int(np.prod(nptitles.shape)/4) # Find out how many songs are in this list.
    reshaped = nptitles.reshape(numsongs,4) # Reshape the array based on the number of songs and the number of columns.
    newdata = pd.DataFrame(reshaped)
    newdata.columns = ['Title','Artist','Peak','Number of weeks in top ten']
    newdata['Year'] = str(i)
    newdata['Title'] = [j[1:j.rfind('\"')] for j in newdata['Title']] # Drops quotation marks and annotations in Title.
    if(i == now.year):
        cleanweeks = []
        for j in newdata['Number of weeks in top ten']: # This code searches the number of weeks in top ten column for asterisks and eliminates them. This is only a 
            try:                                         # problem in the current year.
                cleanweeks.append(int(j[:j.rindex('*')]))
            except :
                cleanweeks.append(int(j))
        newdata['Number of weeks in top ten'] = cleanweeks
    songdata = songdata.append(newdata, ignore_index=True)
    print('Data for ' + str(i) + ' acquired!')
    t.sleep(15) # Delay between requests, for politeness' sake.

songdata.to_csv(path_or_buf='data/top10songs.csv',index=False) # Export our data table.