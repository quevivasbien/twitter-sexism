# -*- coding: utf-8 -*-
"""
Created on Sun Mar  3 13:19:18 2019

@author: mckaydjensen
"""

SOURCE_FOLDER = 'twitter_data/states'
FEATURES_FOLDER = 'twitter_data/states_features'
SEXISM_DISTS = 'twitter_data/states_features/sexism_distributions.json'

import zipfile
import json
import os
import re
import sys

import twitter
from make_predictions import get_predictions_by_location

# Takes as an argument the name of the state you want to get data for
# e.g. state='Alabama'; tries to find the zip file containing data for that
# state and gets all the features for the state. Saves all the features, by
# user in the FEATURES_FOLDER directory.
# Note that the ZIPs that this function accesses are generated by
# download_user_timelines.py and should be saved in the SOURCE_FOLDER directory
def extract_features(state):
    archive = zipfile.ZipFile('{0}/{1}.zip'.format(SOURCE_FOLDER, state), 'r')
    # save_at is the folder where the features for this state will be stored
    save_at = FEATURES_FOLDER + '/' + state
    # Create the save_at folder if it doesn't already exist
    if not os.path.exists(save_at):
        os.makedirs(save_at)
    # Extract features for each file in the archive
    for filename in archive.namelist():
        data = archive.read(filename).decode('utf-8')
        status_dicts = json.loads(data)
        features = [twitter.extract_features(s) for s in status_dicts]
        output_filename = state + '/' + re.search(r'\d.*$', filename).group()
        with open('{0}/{1}'.format(FEATURES_FOLDER, output_filename),
                  'w', encoding='utf-8') as fh:
            json.dump(features, fh, ensure_ascii=False)
    archive.close()

# Run this after running extract_features(state) to run machine learning model
# on the features for that state and make predictions on which tweets are
# sexist. Will save predictions in the same features files.
def make_predictions(state):
    features_dir = FEATURES_FOLDER + '/' + state
    if not os.path.exists(features_dir):
        print('Directory does not exist for the requested state:', state)
        return
    filenames = [features_dir + '/' + f for f in os.listdir(features_dir)]
    for f in filenames:
        get_predictions_by_location(f)

# Run this after running both of the above functions to generate a list of
# where each entry is the percent of tweets classified as sexist for each user
# from the requested state.
def get_pct_sexist(state, cutoff=0.5):
    percentages = []
    features_dir = FEATURES_FOLDER + '/' + state
    for file in os.listdir(features_dir):
        with open(features_dir + '/' + file, 'r', encoding='utf-8') as fh:
            status_dicts = json.load(fh)
        is_sexist = [int(s['prediction'] > cutoff) for s in status_dicts]
        pct_sexist = sum(is_sexist)/len(is_sexist)
        percentages.append(pct_sexist)
    return percentages


if __name__ == '__main__':
    with open(SEXISM_DISTS, 'r') as fh:
        dists = json.load(fh)
    for state in sys.argv[1:]:
        if not os.path.isfile('{0}/{1}.zip'.format(SOURCE_FOLDER, state)):
            print('File {}.zip does not exist. Skipping...'.format(state))
            continue
        print('Extracting features for {}...'.format(state))
        extract_features(state)
        print('Classifying users\' tweets as sexist/not sexist...')
        make_predictions(state)
        dists[state] = get_pct_sexist(state)
    with open(SEXISM_DISTS, 'w') as fh:
        json.dump(dists, fh)