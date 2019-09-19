# -*- coding: utf-8 -*-
"""
Created on Sat Feb  9 13:47:13 2019

@author: mckaydjensen
"""

import json
import zipfile
import sys

import twitter


USERS_FILE = 'twitter_data/users/users_by_loc.json'
SAVE_DIR = 'twitter_data/users/'
MASTER_USER_LIST = 'twitter_data/users/users.json'

SINCE_ID = 682614967963676672 # tweet id from dec 31 2015
MAX_ID = 815602308952326145 # tweet id from jan 01 2017

STATES = ['Alaska', 'Delaware', 'Idaho', 'Maine', 'Mississippi', 'Montana',
          'New Hampshire', 'New Mexico', 'North Dakota', 'South Dakota',
          'Vermont', 'West Virginia', 'Wyoming']

ALASKA = '07179f4fe0500a32'
DELAWARE = '3f5897b87d2bf56c'
IDAHO = '4723507d8ce23a60'
MAINE = '463f5d9615d7d1be'
MISSISSIPPI = '43d2418301bf1a49'
MONTANA = 'd2ddff69682ae534'
NEW_HAMPSHIRE = '226b21641df42460'
NEW_MEXICO = '71d65c0e6d94efab'
NORTH_DAKOTA = '7d893ca2441b0c21'
SOUTH_DAKOTA = 'd06e595eb3733f42'
VERMONT = '9aa25269f04766ab'
WEST_VIRGINIA = '2d83c71ce16cd187'
WYOMING = '5669366953047e51'

SMALL_STATES = [ALASKA, DELAWARE, IDAHO, MAINE, MISSISSIPPI, MONTANA, NEW_HAMPSHIRE,
                NEW_MEXICO, NORTH_DAKOTA, SOUTH_DAKOTA, VERMONT, WEST_VIRGINIA, WYOMING]
SEARCH_QUERY = ' OR '.join(['place:{}'.format(state) for state in SMALL_STATES])


with open(MASTER_USER_LIST, 'r') as fh:
    master_user_list = json.load(fh)

def get_usernames(count, query=SEARCH_QUERY, max_id=None):
    users = {}
    for status in twitter.tweepy.Cursor(twitter.api.search, q=query,
                            max_id=max_id, tweet_mode="extended").items(count):
        status = twitter.clean_status(status, from_stream=False)
        user_id = status['user']['id']
        place = twitter.extract_place(status)
        if (user_id is not None) and place in STATES \
                                        and (user_id not in master_user_list):
            users[user_id] = place
    return users
    

def find_users(user_count, tweets_per_user=100, since_id=SINCE_ID, max_id=MAX_ID):
    users = get_usernames(user_count)
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
        print('Batch {}/{}...'.format(i+1, num_of_batches))
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