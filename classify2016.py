# -*- coding: utf-8 -*-
"""
Created on Mon Mar 25 18:22:58 2019

@author: mckaydjensen
"""

USERS_FOLDER = 'twitter_data/users'
EXTRACTED_DIR = 'twitter_data/users/extracted'

import zipfile
import json
import os
import numpy as np
import pandas as pd
from keras.models import load_model

from text_processing import prepare_tweet_texts

ML_MODEL = 'model.h5'
predictor = load_model(ML_MODEL)

def extract_and_predict(zipdir, outname):
    archive = zipfile.ZipFile('{0}/{1}'.format(USERS_FOLDER, zipdir), 'r')
    all_data = []
    print('Extracting...')
    for file in archive.namelist():
        data = archive.read(file).decode('utf-8')
        dict_list = json.loads(data, encoding='utf-8')
        all_data.extend(dict_list)
    print('Classifying...')
    prepared_texts = prepare_tweet_texts([tw['text'] for tw in all_data])
    predictions = predictor.predict(prepared_texts)
    print('Rearchiving...')
    for i in range(len(all_data)):
        all_data[i]['prediction'] = float(predictions[i][0])
    with open(EXTRACTED_DIR + '/' + outname, 'w', encoding='utf-8') as fh:
        json.dump(all_data, fh, ensure_ascii=False)


def create_dataframe(save_as=None):
    data_files = os.listdir(EXTRACTED_DIR)
    data = []
    for data_file in data_files:
        with open(EXTRACTED_DIR+'/'+data_file, 'r', encoding='utf-8') as fh:
            data.extend(json.load(fh))
    data = pd.DataFrame.from_records(data,
                                     exclude=['is_retweet', 'id', 'text'])
    if save_as:
        data.to_csv(save_as)
    return data


def eval_all(save_as=None, save_counts=True, data=None):
    if data is None:
        data = create_dataframe()
    states = data['place'].unique()
    scores = []
    stdevs = []
    if save_counts:
        n = []
    for state in states:
        all_scores = data[data['place'] == state]['prediction']
        scores.append(np.mean(all_scores))
        stdevs.append(np.std(all_scores, ddof=1)/np.sqrt(len(all_scores)))
        if save_counts:
            n.append(len(all_scores))
    output = pd.DataFrame({'state': states, 'score': scores, 'stdev': stdevs})
    if save_counts:
        output['n'] = n
    if save_as is not None:
        output.to_csv(save_as)
    return output