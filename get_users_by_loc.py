# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 08:56:08 2019

@author: mckaydjensen

When run will go through files in the source folder (default: twitter_data)
and fetch up to 1000 tweets for each location found. Will then retrieve user
IDs for those tweets and save them all to a JSON file.
The idea is that the users should be approximately evenly distributed by
location.
"""

import json
import os

import twitter

SOURCE_FOLDER = 'twitter_data'
OUTPUT_FILENAME = SOURCE_FOLDER + '/users/users_by_loc.json'


#Step one: loop through downloaded data to get ids for each state
#Step two: loop through the ids and query twitter for user ids
#Step three: save user ids
#Step four: fetch user timelines for each user

def get_tweet_ids_list(count_per_loc=1000):
    loc_counts = {}
    ids = []
    # Save a vector of locations as well
    locs = []
    data_filenames = [f for f in os.listdir(SOURCE_FOLDER) if f[-5:]=='.json']
    for f in data_filenames:
        f_in = SOURCE_FOLDER + '/' + f
        print('Parsing {}...'.format(f_in))
        with open(f_in, 'r', encoding='utf-8') as fh:
            status_dicts = json.load(fh)
        for status in status_dicts:
            place = twitter.extract_place(status)
            if place not in loc_counts:
                loc_counts[place] = 1
                ids.append(status['id'])
                locs.append(place)
            elif loc_counts[place] < count_per_loc:
                loc_counts[place] += 1
                ids.append(status['id'])
                locs.append(place)
    return ids, locs

# Will return tuple of user ids and places associated with given
    # list of tweet IDs
def get_user_ids(tweet_ids):
    user_ids = []
    total = len(tweet_ids)
    for i in range(0, total, 100):
        idchunk = tweet_ids[i:i+100]
        statuses = twitter.api.statuses_lookup(idchunk)
        user_ids += [(s._json['user'].get('id'),
                      twitter.extract_place(s._json)) for s in statuses]
        print('{0}/{1} user IDs found'.format(min(i+100, total), total))
    return user_ids


if __name__ == '__main__':
    tweet_ids, locs = get_tweet_ids_list()
    user_ids = get_user_ids(tweet_ids)
    all_locs = set([u[1] for u in user_ids])
    loc_dict = {loc: [] for loc in all_locs}
    for uid in user_ids:
        loc_dict[uid[1]].append(uid[0])
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as fh:
        json.dump(loc_dict, fh, ensure_ascii=False)