"""
tweepy stream
created 28 Aug 2018 by Mckay Jensen
"""

import tweepy
import json
import re

import pandas as pd

from http.client import IncompleteRead
from urllib3.exceptions import ProtocolError

#Credentials to access the Twitter API.
ACCESS_TOKEN = '925129859206062080-QhH3e0Hj4DVHD2wuEqHj2M2fbTmHEbe'
ACCESS_SECRET = 'w91jUCV0RcSLYQbyCQDHeFLDdPQZhUU3WlKX20vhREApc'
CONSUMER_KEY = 'paMrcoKtIGPRBdyBBZTR4Xfnw'
CONSUMER_SECRET = 'VS7O7B1eVcuTNtjXmbjzZGR1M66hrediieTqQiYu2tgw2wu6qO'


auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)


US_GEOBOX = [-125,25,-66,48]
HAWAII_GEOBOX = [-160.4,18.8,-154.8,22.3]
ALASKA_GEOBOX = [-165,54.5,-129.8,71.5]

states = {
            'AL': 'Alabama',
            'AK': 'Alaska',
            'AZ': 'Arizona',
            'AR': 'Arkansas',
            'CA': 'California',
            'CO': 'Colorado',
            'CT': 'Connecticut',
            'DE': 'Delaware',
            'DC': 'District of Columbia',
            'FL': 'Florida',
            'GA': 'Georgia',
            'HI': 'Hawaii',
            'ID': 'Idaho',
            'IL': 'Illinois',
            'IN': 'Indiana',
            'IA': 'Iowa',
            'KS': 'Kansas',
            'KY': 'Kentucky',
            'LA': 'Louisiana',
            'ME': 'Maine',
            'MD': 'Maryland',
            'MA': 'Massachusetts',
            'MI': 'Michigan',
            'MN': 'Minnesota',
            'MS': 'Mississippi',
            'MO': 'Missouri',
            'MT': 'Montana',
            'NE': 'Nebraska',
            'NV': 'Nevada',
            'NH': 'New Hampshire',
            'NJ': 'New Jersey',
            'NM': 'New Mexico',
            'NY': 'New York',
            'NC': 'North Carolina',
            'ND': 'North Dakota',
            'OH': 'Ohio',
            'OK': 'Oklahoma',
            'OR': 'Oregon',
            'PA': 'Pennsylvania',
            'RI': 'Rhode Island',
            'SC': 'South Carolina',
            'SD': 'South Dakota',
            'TN': 'Tennessee',
            'TX': 'Texas',
            'UT': 'Utah',
            'VT': 'Vermont',
            'VA': 'Virginia',
            'WA': 'Washington',
            'WV': 'West Virginia',
            'WI': 'Wisconsin',
            'WY': 'Wyoming'
         }


def clean_status_text(text, remove_hashtags=False, remove_handles=False,
                      remove_urls=False, ascii_only=False):
    #Replace &amp; with &
    text = re.sub(r'&amp;?', '&', text)
    #Replace $gt; with > and &lt; with <
    text = re.sub('&gt;', '>', text)
    text = re.sub('&lt;', '<', text)
    #Handle other options
    if remove_urls:
        text = re.sub(r'https?.*?(?= |$)', '', text)
    if remove_hashtags:
        text = re.sub(r'#.*?(?= |$)', '', text)
    if remove_handles:
        text = re.sub(r'@.*?(?= |$)', '', text)
    #Condense whitespace
    text = re.sub(r'\s+', ' ', text)
    #Return processed text
    if ascii_only:
        return text.encode('ascii', 'ignore')
    else:
        return text


def clean_status(status):
    if type(status) is tweepy.models.Status:
        status = status._json
    #The full tweet text is for some reason stored in different places
        #depending on the type of tweet.
    if status['truncated']:
        text = status['extended_tweet']['full_text']
    elif 'retweeded_status' in status and status['retweeted_status']['truncated']:
        text = status['retweeted_status']['extended_tweet']['full_text']
    else:
        text = status['text']
    res = {
            'text': clean_status_text(text),
            'id': status['id'],
            'is_retweet': 'retweeted_status' in status,
            'place': status['place'],
            'lang': status['lang'],
            'timestamp': status['created_at']
          }
    return res




class PipingStreamListener(tweepy.StreamListener):
    
    def __init__(self, results):
        tweepy.StreamListener(self)
        self.api = api
        self.results = results
        self.todo = 0
    
    def on_status(self, status):
        self.results.append(status._json)
        self.todo -= 1
        if self.todo <= 0:
            return False
        elif self.todo % 1000 == 0:
            print('{} statuses remaining...'.format(self.todo))
        
    def on_error(self, status):
        print('Error in Twitter Stream: ' + str(status))
        #Will stop streaming if rate limit is reached.
        if status == 420:
            return False
        
        
        
class GeolimitedRetriever(object):
    
    def __init__(self):
        self.results = []
        self.streamListener = PipingStreamListener(self.results)
        
    def run_stream(self, geobox, count=1):
        self.streamListener.todo = count
        while self.streamListener.todo > 0:
            try:
                stream = tweepy.Stream(auth=api.auth,
                                       listener=self.streamListener)
                stream.filter(locations=geobox, stall_warnings=True)
            except (IncompleteRead, ProtocolError):
                print('Something went wrong with the connection. '
                      'Ignoring and reconnecting...')
                #Ignore and reconnect
                continue
        
    def get_clean_results(self):
        clean_results = []
        for status in self.results:
            res = clean_status(status)
            clean_results.append(res)
        return clean_results


def publish_json(obj, filename):
    with open(filename, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False)


def download_results(count, savename=None,
                     geobox=US_GEOBOX+HAWAII_GEOBOX+ALASKA_GEOBOX):
    geo = GeolimitedRetriever()
    geo.run_stream(geobox, count)
    results = geo.get_clean_results()
    if savename:
        publish_json(results, savename)
    return results
    
    
#Takes a list of status IDs (ids) and returns info for each status, including
    #status text.
def get_statuses(ids):
    #split into chunks of 100 statuses each since that is the max accepted
        #by tweepy.API.statuses_lookup()
    idchunks = [ids[i:i+100] for i in range(0, len(ids), 100)]
    all_statuses = sum([api.statuses_lookup(chunk) for chunk in idchunks], [])
    all_statuses = [clean_status(status) for status in all_statuses]
    return all_statuses

def create_validation_set(approx_size, savename=None):
    #Download tweets
    statuses = download_results(approx_size)
    #Remove non-English tweets
    statuses = [s for s in statuses if s['lang'] == 'en']
    #Get text only and remove any blank entries
    status_text = [s['text'] for s in statuses]
    status_text = [t for t in status_text if t]
    if savename:
        publish_json(status_text, savename)
    return status_text

def rebuild_sexist_source(original='hatespeech-master/NAACL_SRW_2016.csv',
                          save_as='NAACL_data.csv'):
    df = pd.read_csv(original, header=None)
    sexist_status_ids = list(df[df[1] == 'sexism'][0])
    sexist_status_text = [s['text'] for s in get_statuses(sexist_status_ids)]
    neutral_status_ids = list(df[df[1] == 'none'][0])
    neutral_status_text = [s['text'] for s in get_statuses(neutral_status_ids)]
    sexist_data = pd.DataFrame({'label': 1, 'tweet': sexist_status_text})
    neutral_data = pd.DataFrame({'label': 0, 'tweet': neutral_status_text})
    all_data = pd.concat([sexist_data, neutral_data])
    all_data.to_csv(save_as)
    

#Takes a tweepy place dict
#Returns the state the place is located in.
#If the place is not in the US, will return the country.
def reduce_place(place):
    if place['country'] != 'United States':
        return place['country']
    elif place['place_type'] == 'admin':
       return place['name']
    elif place['place_type'] == 'city':
        return states[place['full_name'].split(', ')[-1]]