"""
tweepy stream
created 28 Aug 2018 by Mckay Jensen
"""

import tweepy
import json
import re
from nltk.tokenize import TweetTokenizer

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
                      ascii_only=False):
    #Remove URLs:
    text = re.sub(r'https?.*?(?= |$)', '', text)
    #Handle other options
    if remove_hashtags:
        text = re.sub(r'#.*?(?= |$)', '', text)
    if remove_handles:
        text = re.sub(r'@.*?(?= |$)', '', text)
    #Return processed text
    if ascii_only:
        return text.encode('ascii', 'ignore')
    else:
        return text


def clean_status(status):
    if type(status) is tweepy.models.Status:
        status = status._json
    res = {
            'user': status['user']['id'],
            'is_retweet': 'retweeted_status' in status,
            'place': status['place'],
            'timestamp': status['created_at']
          }
    #The full tweet text is for some reason stored in different places
        #depending on the type of tweet.
    if status['truncated']:
        res['text'] = status['extended_tweet']['full_text']
    elif 'retweeded_status' in status and status['retweeted_status']['truncated']:
        res['text'] = status['retweeted_status']['extended_tweet']['full_text']
    else:
        res['text'] = clean_status_text(status['text'])
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
        self.stream = tweepy.Stream(auth=api.auth,
                                    listener=self.streamListener)
        
    def run_stream(self, geobox, count=1):
        self.streamListener.todo = count
        self.stream.filter(locations=geobox)
        
    def get_clean_results(self):
        clean_results = []
        for status in self.results:
            res = clean_status(status)
            clean_results.append(res)
        return clean_results


def download_results(count, savename=None,
                     geobox=US_GEOBOX+HAWAII_GEOBOX+ALASKA_GEOBOX):
    geo = GeolimitedRetriever()
    geo.run_stream(geobox, count)
    results = geo.get_clean_results()
    if savename:
        with open(savename, 'w', encoding='utf-8') as writer:
            json.dump(results, writer, ensure_ascii=False)
    return results

def load_results(filename):
    with open(filename, 'r', encoding='utf-8') as reader:
        return json.load(reader)
    
    
#Takes a list of status IDs (ids) and returns info for each status, including
    #status text.
def get_statuses(ids):
    #split into chunks of 100 statuses each since that is the max accepted
        #by tweepy.API.statuses_lookup()
    idchunks = [ids[i:i+100] for i in range(0, len(ids), 100)]
    all_statuses = sum([api.statuses_lookup(chunk) for chunk in idchunks], [])
    all_statuses = [clean_status(status) for status in all_statuses]
    return all_statuses



def reduce_place(place):
    if place['country'] != 'United States':
        return place['country']
    elif place['place_type'] == 'admin':
       return place['name']
    elif place['place_type'] == 'city':
        return states[place['full_name'].split(', ')[-1]]
    
    
def tokenize_status_text(text):
    tokenizer = TweetTokenizer()
    return tokenizer.tokenize(text.lower())


def create_hash_indices(text, hashspace_size):
    if type(text) is str or type(text) is bytes:
        text = [text]
    tokenized_text = [tokenize_status_text(t) for t in text]
    encoded_text = [[hash(w) % (hashspace_size - 1) + 1 for w in t] \
                     for t in tokenized_text]
    return encoded_text