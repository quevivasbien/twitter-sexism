# -*- coding: utf-8 -*-
"""
Created on Sat Sep  1 12:57:26 2018

@author: mckaydjensen
"""

import json
import re
import pandas as pd
import numpy as np

from nltk.tokenize import TweetTokenizer
from keras.preprocessing.sequence import pad_sequences

FLAGS = re.MULTILINE | re.DOTALL
HASHMAP_PATH = 'hashmap.json'
MAX_INPUT_LENGTH = 40

#load hashing dictionary
with open(HASHMAP_PATH, encoding='utf-8') as fh:
    hash_dict = json.load(fh)


#Use tweet tokenizer from NLTK to tokenize tweet text	
def tokenize_status_text(text):
    tokenizer = TweetTokenizer()
    return tokenizer.tokenize(text.lower())


def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as reader:
        return json.load(reader)


#Preprocess tweet text for best results with pretrained Glove embeddings
def glove_preprocess(text):
    """
    adapted from https://nlp.stanford.edu/projects/glove/preprocess-twitter.rb
    and from https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/discussion/50350
    """
    text = re.sub(r'&amp;?', '&', text)
    # Different regex parts for smiley faces
    eyes = "[8:=;]"
    nose = "['`\-]?"
    text = re.sub(r'(?:https?|www\.)\S+', '<URL>', text, FLAGS)
    hashtags = re.findall(r'#[^\s]+', text)
    for hashtag in hashtags:
        replacement = ''
        if hashtag.upper() == hashtag:
            replacement = '<HASHTAG> {} <ALLCAPS>'.format(hashtag)
        else:
            replacement = '<HASHTAG> ' + re.sub(r'(?<=\w)(?=[A-Z])', ' ', hashtag, FLAGS)
        try:
            text = re.sub(hashtag, replacement, text)
        except:
            print('Problem with hashtag {}... skipping.'.format(hashtag))
    text = re.sub("\[\[User(.*)\|", '<USER>', text, FLAGS)
    text = re.sub("<3", '<HEART>', text, FLAGS)
    text = re.sub("[-+]?[.\d]*[\d]+[:,.\d]*", "<NUMBER>", text, FLAGS)
    text = re.sub(eyes + nose + "[Dd)]", '<SMILE>', text, FLAGS)
    text = re.sub("[(d]" + nose + eyes, '<SMILE>', text, FLAGS)
    text = re.sub(eyes + nose + "p", '<LOLFACE>', text, FLAGS)
    text = re.sub(eyes + nose + "\(", '<SADFACE>', text, FLAGS)
    text = re.sub("\)" + nose + eyes, '<SADFACE>', text, FLAGS)
    text = re.sub(eyes + nose + "[/|l*]", '<NEUTRALFACE>', text, FLAGS)
    text = re.sub("/", " / ", text, FLAGS)
    text = re.sub("[-+]?[.\d]*[\d]+[:,.\d]*", "<NUMBER>", text, FLAGS)
    text = re.sub("([!]){2,}", "! <REPEAT>", text, FLAGS)
    text = re.sub("([?]){2,}", "? <REPEAT>", text, FLAGS)
    text = re.sub("([.]){2,}", ". <REPEAT>", text, FLAGS)
    pattern = re.compile(r"(.)\1{2,}")
    text = pattern.sub(r"\1" + " <ELONG>", text, FLAGS)
    
    return text


#Takes a token (e.g. from tokenize_status_text) and looks up its hash
# in the hash_dict	
def hash_token(t):
    hashcode = hash_dict.get(t)
    if hashcode is not None:
        return hashcode
    else:
        # Hash unknown tokens as 0
        return 0


#Takes a list of tweet strings, tokenizes them, and hashes the tokens
#Will return a list of lists of ints
def tokenize_and_hash(tweets):
    tweets = [glove_preprocess(t) for t in tweets]
    tokenized = [tokenize_status_text(t) for t in tweets]
    hashed = [[hash_token(t) for t in tweet] for tweet in tokenized]
    return hashed


def load_and_prepare_data(feature_csv):
	data = pd.read_csv(feature_csv, usecols=['label', 'text'])
	tweets = list(data.text)
	labels = np.array(data.label)
	tweets_hashed = tokenize_and_hash(tweets)
	tweets_padded = pad_sequences(tweets_hashed, maxlen=MAX_INPUT_LENGTH)
	return tweets_padded, labels