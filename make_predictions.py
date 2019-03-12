# -*- coding: utf-8 -*-
"""
Created on Fri Feb  1 12:30:12 2019

@author: mckaydjensen
"""

import json
import os

from keras.models import load_model
from text_processing import prepare_tweet_texts

ML_MODEL = 'model.h5'
FEATURES_FOLDER = 'twitter_data/features'

predictor = load_model(ML_MODEL)


def get_predictions_by_location(features_file, cutoff=0.5):
    with open(features_file, 'r', encoding='utf-8') as fh:
        features = json.load(fh)
    # If predictions haven't already been made, make predictions
    if not all('prediction' in tweet_f for tweet_f in features):
        tweet_texts = [tweet_f['text'] for tweet_f in features]
        prepared_texts = prepare_tweet_texts(tweet_texts)
        predictions = predictor.predict(prepared_texts)
        for i in range(len(features)):
            features[i]['prediction'] = float(predictions[i][0])
        # Save the file with the predictions included
        with open(features_file, 'w', encoding='utf-8') as fh:
            json.dump(features, fh, ensure_ascii=False)
    # Convert prediction probabilities to binary predictions
    predictions = [1 if tweet_f['prediction'] > cutoff else 0 \
                   for tweet_f in features]
    places = [tweet_f['place'] for tweet_f in features]
    # Compile prediction frequencies for each location
    preds_by_loc = {}
    for i in range(len(features)):
        try:
            preds_by_loc[places[i]]['sexist'] += predictions[i]
            preds_by_loc[places[i]]['total'] += 1
        except KeyError:
            preds_by_loc[places[i]] = {'sexist': predictions[i], 'total': 1}
    return preds_by_loc


def compile_master_predictions_by_location():
    feature_files = os.listdir(FEATURES_FOLDER)
    preds_by_loc = {}
    for f in feature_files:
        print('Making predictions from "{}"...'.format(f))
        new_preds = get_predictions_by_location(FEATURES_FOLDER + '/' + f)
        for loc in new_preds:
            try:
                preds_by_loc[loc]['sexist'] += new_preds[loc]['sexist']
                preds_by_loc[loc]['total'] += new_preds[loc]['total']
            except KeyError:
                preds_by_loc[loc] = {
                                        'sexist': new_preds[loc]['sexist'],
                                        'total': new_preds[loc]['total']
                                    }
    return preds_by_loc


if __name__ is '__main__':
    preds_by_loc = compile_master_predictions_by_location()
    with open('predictions_by_location.json', 'w', encoding='utf-8') as fh:
        json.dump(preds_by_loc, fh, ensure_ascii=False)