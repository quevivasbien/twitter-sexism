# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 14:44:09 2019

@author: mckaydjensen
"""

import json
import os
import numpy as np
import pandas as pd

FEATURES_LOC = 'twitter_data/features'

def main():
    states_dict = {}
    filenames = os.listdir(FEATURES_LOC)
    for f in filenames:
        print('Extracting predictions from "{}"...'.format(f))
        with open(FEATURES_LOC + '/' + f, 'r', encoding='utf-8') as fh:
            features = json.load(fh)
        for tweet in features:
            place = tweet['place']
            score = tweet['prediction']
            try:
                states_dict[place].append(score)
            except KeyError:
                states_dict[place] = [score]
    states = states_dict.keys()[0]
    means = [np.mean(states_dict[state]) for state in states]
    stdevs = [np.std(states_dict[state], ddof=1) for state in states]
    df = pd.DataFrame({'state': states, 'mean': means, 'stdev': stdevs})
    df.to_csv('datadatadatadata.csv')
    return df