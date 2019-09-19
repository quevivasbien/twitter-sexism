# -*- coding: utf-8 -*-
"""
Created on Sat Feb  9 13:47:13 2019

@author: mckaydjensen
"""

import json
import zipfile
import os
import sys

import twitter


USERS_FILE = 'twitter_data/users/users_by_loc.json'
SAVE_DIR = 'twitter_data/users/'
MASTER_USER_LIST = 'twitter_data/users/users.json'

SINCE_ID = 682614967963676672 # tweet id from dec 31 2015
MAX_ID = 815602308952326145 # tweet id from jan 01 2017

STATES = ['Alabama', 'Alaska',  'Arizona', 'Arkansas', 'California',
          'Colorado', 'Connecticut', 'Delaware', 'District of Columbia',
          'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana',
          'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
          'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri',
          'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey',
          'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio',
          'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
          'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah',
          'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin',
          'Wyoming']


with open(MASTER_USER_LIST, 'r') as fh:
    master_user_list = json.load(fh)


def find_users(num_of_users=1000, tweets_per_user=100,
               since_id=SINCE_ID, max_id=MAX_ID):
    print('Collecting users...')
    streamed_tweets = twitter.download_results(num_of_users)
    users = {}
    for tweet in streamed_tweets:
        place = twitter.extract_place(tweet)
        user_id = tweet['user']['id']
        if (place in STATES) and (user_id not in master_user_list):
            users[user_id] = place
    all_statuses = []
    for user_id in users:
        print('Retrieving tweets for user {}...'.format(user_id))
        statuses = twitter.get_user_timeline(user_id, count=tweets_per_user,
                                             since_id=since_id, max_id=max_id)
        if statuses is not None:
            statuses = [twitter.extract_features(s, True) for s in statuses]
            for s in statuses:
                if s['place'] not in STATES:
                    s['place'] = users[user_id]
            all_statuses += statuses
    # Update master user list
    #global master_user_list
    master_user_list.extend(list(users.keys()))
    with open(MASTER_USER_LIST, 'w') as fh:
        json.dump(master_user_list, fh)
    return all_statuses


def get_and_save_batches(zipsavename, num_of_batches, users_per_batch=1000,
                         tweets_per_user=100, since_id=SINCE_ID, max_id=MAX_ID):
    zipf = zipfile.ZipFile(SAVE_DIR + zipsavename + '.zip', 'w',
                           zipfile.ZIP_DEFLATED)
    for i in range(num_of_batches):
        statuses = find_users(users_per_batch, tweets_per_user,
                              since_id, max_id)
        zipf.writestr('batch{}.json'.format(i),
                      json.dumps(statuses, ensure_ascii=False))
    zipf.close()
        


if __name__ == '__main__':
    # Syntax is 'python download_user_timelines.py [zipsavename]
    # [num_of_batches] [[optional] users_per_batch]'
    argv = sys.argv
    zipsavename = argv[1]
    num_of_batches = int(argv[2])
    if len(argv) < 4:
        get_and_save_batches(zipsavename, num_of_batches)
    else:
        users_per_batch = int(argv[3])
        get_and_save_batches(zipsavename, num_of_batches, users_per_batch)