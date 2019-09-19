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
#Read from text file, which user must create
API_AUTH_FILE = 'api_auth.txt'
with open('api_auth.txt') as fh:
    ACCESS_TOKEN = fh.readline().rstrip()
    ACCESS_SECRET = fh.readline().rstrip()
    CONSUMER_KEY = fh.readline().rstrip()
    CONSUMER_SECRET = fh.readline().rstrip()


auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)


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


def clean_status(status, get_user_info=True, from_stream=True):
    if type(status) is tweepy.models.Status:
            status = status._json
    text = ''
    if from_stream:
        # The full tweet text is for some reason stored in different places
            # depending on the type of tweet.
        if status['truncated']:
            text = status['extended_tweet']['full_text']
        elif 'retweeted_status' in status and status['retweeted_status']['truncated']:
            text = status['retweeted_status']['extended_tweet']['full_text']
        else:
            text = status['text']
    else:
        text = status['full_text']
    place = status.get('place')
    # Take only some of the place attributes, the ones we need to identify the
        # state.
    if place is not None:
        place = {k: place[k] for k in \
                 ['full_name', 'name','place_type','country']}
    res = {
            'text': clean_status_text(text),
            'id': status['id'],
            'is_retweet': 'retweeted_status' in status,
            'place': place,
            'lang': status['lang'],
            'timestamp': status['created_at']
          }
    if get_user_info:
        res['user'] = {
                        'id': status['user'].get('id'),
                        #'description': status['user'].get('description'),
                        #'followers': status['user'].get('followers_count'),
                        'location': status['user'].get('location'),
                        #'statuses_count': status['user'].get('statuses_count')
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
        
        
        
class GeolimitedRetriever:
    
    def __init__(self):
        self.results = []
        self.streamListener = PipingStreamListener(self.results)
        
    def run_stream(self, count=1, geobox=None, languages=['en']):
        self.streamListener.todo = count
        while self.streamListener.todo > 0:
            try:
                stream = tweepy.Stream(auth=api.auth,
                                       listener=self.streamListener)
                stream.filter(locations=geobox, languages=languages,
                              stall_warnings=True)
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
    geo.run_stream(count, geobox)
    results = geo.get_clean_results()
    if savename:
        publish_json(results, savename)
    return results
    
    
#Takes a list of status IDs (ids) and returns info for each status, including
    #status text.
#WARNING! This is broken for tweets > 140 chars!! Do not use this if you need
    #the full tweet text.
def get_statuses(ids):
    #split into chunks of 100 statuses each since that is the max accepted
        #by tweepy.API.statuses_lookup()
    idchunks = [ids[i:i+100] for i in range(0, len(ids), 100)]
    all_statuses = sum([api.statuses_lookup(chunk) for chunk in idchunks], [])
    all_statuses = [clean_status(status) for status in all_statuses]
    return all_statuses


def get_user_timeline(user_id, count=1000, since_id=None, max_id=None):
    statuses = []
    try:
        for status in tweepy.Cursor(api.user_timeline, user_id=user_id,
                                    since_id=since_id, max_id=max_id,
                                    tweet_mode="extended").items(count):
            statuses.append(clean_status(status, from_stream=False))
    except tweepy.error.TweepError:
		# Assume it is a 401 (permission error). If API auth is set up
		    # properly, this probably happens because of a user-specific setting
        return None
    return statuses


#Takes a dict returned from clean_status()
#Returns the features that will be plugged into the ML model
def extract_features(status_dict, save_id=False):
    features = {
        'text': status_dict['text'],
        'is_retweet': int(status_dict['is_retweet']),
        'place': extract_place(status_dict)
        #'user_description': status_dict['user']['description'],
        #'user_followers': status_dict['user']['followers'],
        #'user_status_count': status_dict['user']['statuses_count']
    }
    if save_id:
        features['id'] = status_dict['id']
    return features
    

def rebuild_sexist_source(original='hatespeech-master/NAACL_SRW_2016.csv',
                          save_as='training_data/NAACL_data.csv'):
    df = pd.read_csv(original, header=None)
    #Query Twitter API for status info for each status ID in data source
    sexist_status_ids = list(df[df[1] == 'sexism'][0])
    sexist_statuses = get_statuses(sexist_status_ids)
    neutral_status_ids = list(df[df[1] == 'none'][0])
    neutral_statuses = get_statuses(neutral_status_ids)
    #Construct Pandas DataFrame from fetched status data
    labels = pd.Series([1]*len(sexist_statuses) + [0]*len(neutral_statuses),
                       name='label')
    all_statuses = sexist_statuses + neutral_statuses
    #Only take the relevant features
    features = pd.DataFrame([extract_features(s) for s in all_statuses])
    data = pd.concat([labels, features], axis=1)
    data.to_csv(save_as)
    

#Takes a dict returned from clean_status()
#Determines the location this tweet likely came from
#Returns the state the place is located in.
#If the place is not in the US, will return the country.
def extract_place(status):
    #Try to get the place from the place data inside the status dict
    if status['place'] is not None:
        place = status['place']
        if place['country'] != 'United States':
            return place['country']
        elif place['place_type'] == 'admin':
            return place['name']
        elif place['place_type'] == 'city':
            return states.get(place['full_name'].split(', ')[-1])
    #If the status dict has no place info, get the place from the user data
    else:
        place = status['user']['location']
        try:
            place = place.split(', ')[-1].upper()
        except AttributeError:
            return None
        if place in states:
            return states[place]
        else:
            return place