# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 18:59:15 2019

@author: mckaydjensen
"""

import json
from keras.preprocessing.sequence import pad_sequences
from keras.models import load_model

import text_processing as t_proc

HASHMAP_PATH = 'hashmap.json'
MODEL_PATH = 'model.h5'


#load hashmap
with open(HASHMAP_PATH, encoding='utf-8') as fh:
    hash_dict = json.load(fh)


def hash_token(t):
    hashcode = hash_dict.get(t)
    if hashcode is not None:
        return hashcode
    else:
        # Hash unknown tokens as 0
        return 0


def tokenize_and_hash(tweets):
    tweets = [t_proc.glove_preprocess(t) for t in tweets]
    tokenized = [t_proc.tokenize_status_text(t) for t in tweets]
    hashed = [[hash_token(t) for t in tweet] for tweet in tokenized]
    return hashed


#Takes a list of tweet texts and classifies them as sexist or not
def classify(tweets):
    
    tweets_hashed = tokenize_and_hash(tweets)
    tweets_padded = pad_sequences(tweets_hashed, maxlen=30) #30 required by model
    
    model = load_model(MODEL_PATH)
    classifications = model.predict(tweets_padded)
    return classifications