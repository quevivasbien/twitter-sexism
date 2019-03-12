# -*- coding: utf-8 -*-
"""
Created on Fri Feb  1 10:56:01 2019

@author: mckaydjensen
"""

SOURCE_FOLDER = 'twitter_data'
DESTINATION_FOLDER = 'twitter_data/features'

import json
import os

import twitter


def extract_features(source_filename, destination_filename):
    with open(source_filename, 'r', encoding='utf-8') as fh:
        status_dicts = json.load(fh)
    features = [twitter.extract_features(s) for s in status_dicts]
    with open(destination_filename, 'w', encoding='utf-8') as fh:
        json.dump(features, fh, ensure_ascii=False)


if __name__ == '__main__':
    #Get a list of all JSON files in the source folder
    data_filenames = [f for f in os.listdir(SOURCE_FOLDER) if f[-5:]=='.json']
    #Extract features from each file and save in the destination folder
    for f in data_filenames:
        print('Extracting features from "{}"...'.format(f))
        f_in = SOURCE_FOLDER + '/' + f
        f_out = DESTINATION_FOLDER + '/' + f[:-5] + ' features.json'
        extract_features(f_in, f_out)