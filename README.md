The goal is to evaluate the lyrics of every song that has ever made the Billboard Hot 100 Top 10 since its inception. Just for fun.

You will need a Genius API account and access token if you wish to run the lyrics fetcher.

In order to create an up to date version of my dataset and visualizations, follow these steps:

1) Install packages

2) Run topsongs-data-iterative-fetcher.py

3.
	a. Run topsongs-lyrics-iterative-fetcher.py

	b. If the lyrics fetcher is interrupted, make a copy of the log file and then run it again.

4) Once the lyrics fetcher is finished, you will have to investigate and manually correct a certain number of outliers, which are usually false positives from Genius, and outright missing songs, which will be listed in the log files. The log file I worked with when retrieving the version of the dataset on this Github is provided as an example. All you will need to do is run this code for each value that needs correcting (using a Jupyter notebook is suggested):

`import pandas as pd`

`import re`

`songdata = pd.read_csv('data/top10songslyrics.csv')`

`i = <location of outlier or missing song>`

`mylyrics = '''`
`<lyrics text here>`
`'''`

`songdata.loc[i,'Lyrics'] = re.sub(r'\[(.*?)\]','',mylyrics.replace(',',''))`

`songdata.to_csv(path_or_buf='data/top10songslyrics.csv',index=False,mode='w+')`

5) Run every cell in topsongs-visualization.ipynb

You should then have an up to date version of this analysis.

Libraries used:

BeautifulSoup

lyricsgenius

NLTK

numpy

os

pandas

re

requests

string

sys

time

wordcloud