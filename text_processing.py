# -*- coding: utf-8 -*-
"""
Created on Sat Sep  1 12:57:26 2018

@author: mckaydjensen
"""

from nltk.tokenize import TweetTokenizer
import json
#from collections import Counter

def tokenize_status_text(text):
    tokenizer = TweetTokenizer()
    return tokenizer.tokenize(text.lower())


def simple_hash(text, hashspace_size):
    if type(text) is str or type(text) is bytes:
        text = [text]
    tokenized_text = [tokenize_status_text(t) for t in text]
    encoded_text = [[hash(w) % (hashspace_size - 1) + 1 for w in t] \
                     for t in tokenized_text]
    return encoded_text


def import_data(sexist_source, control_source):
    #Import data from source files
    with open(sexist_source, 'r', encoding='utf-8') as fh:
        sexist_tweets = [x for x in json.load(fh) if x]
    with open(control_source, 'r', encoding='utf-8') as fh:
        control_tweets = [x for x in json.load(fh) if x]
    #Combine and add markers
    #0 = not sexist; 1 = sexist
    all_tweets = sexist_tweets + control_tweets
    markers = [1]*len(sexist_tweets) + [0]*len(control_tweets)
    return all_tweets, markers