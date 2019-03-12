# -*- coding: utf-8 -*-
"""
Created on Sat Feb  9 13:47:13 2019

@author: mckaydjensen
"""

import json
import zipfile
import os

import twitter


USERS_FILE = 'twitter_data/users/users_by_loc.json'
SAVE_DIR = 'twitter_data/users/'

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


def get_timeline(user_id, savename=None):
    if savename is None:
        savename = SAVE_DIR + str(user_id) + '.json'
    # Check to see if file already exists before trying to download it again
    if os.path.isfile(savename):
        return savename
    all_statuses = twitter.get_user_timeline(user_id)
    if all_statuses is None:
        return None
    print('{0} tweets found for user ID {1}'.format(len(all_statuses), user_id))
    with open(savename, 'w', encoding='utf-8') as fh:
        json.dump(all_statuses, fh, ensure_ascii=False)
    return savename


if __name__ == '__main__':
    with open(USERS_FILE, 'r') as fh:
        users_by_state = json.load(fh)
    for state in STATES:
        try:
            user_ids = list(set(users_by_state[state]))
        except KeyError:
            continue
        print('Unique users for {0}: {1}'.format(state, len(user_ids)))
        filenames = []
        for user_id in user_ids:
            print('Fetching user timeline for user ID {}...'.format(user_id))
            savename = get_timeline(user_id)
            if savename is not None:
                filenames.append(savename)
        # Put each state's info in a ZIP file to keep storage space small
        zipf = zipfile.ZipFile(SAVE_DIR + state + '.zip', 'w',
                               zipfile.ZIP_DEFLATED)
        for file in filenames:
            zipf.write(file)
            # Delete file after zipping
            os.remove(file)
        zipf.close()