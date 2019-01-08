# -*- coding: utf-8 -*-
"""
Created on Sat Sep  1 12:57:26 2018

@author: mckaydjensen
"""

from nltk.tokenize import TweetTokenizer
import json
import re
#from collections import Counter

def tokenize_status_text(text):
    tokenizer = TweetTokenizer()
    return tokenizer.tokenize(text.lower())


#Uniqueness not guaranteed
def simple_hash(text, hashspace_size):
    if type(text) is str or type(text) is bytes:
        text = [text]
    tokenized_text = [tokenize_status_text(t) for t in text]
    encoded_text = [[hash(w) % (hashspace_size - 1) + 1 for w in t] \
                     for t in tokenized_text]
    return encoded_text


def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as reader:
        return json.load(reader)


def import_data(sexist_source, control_source, glove_preproc=True):
    #Import data from source files
    sexist_tweets = [x for x in load_json(sexist_source) if x]
    control_tweets = [x for x in load_json(control_source) if x]
    #Combine and add markers
    #0 = not sexist; 1 = sexist
    all_tweets = sexist_tweets + control_tweets
    if glove_preproc:
        all_tweets = [glove_preprocess(t) for t in all_tweets]
    markers = [1]*len(sexist_tweets) + [0]*len(control_tweets)
    return all_tweets, markers


def glove_preprocess(text):
    """
    adapted from https://nlp.stanford.edu/projects/glove/preprocess-twitter.rb
    and from https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/discussion/50350
    """
    # Different regex parts for smiley faces
    eyes = "[8:=;]"
    nose = "['`\-]?"
    text = re.sub(r'(?:https?|www\.)\S+', '<URL>', text)
    hashtags = re.findall(r'#[^\s]+', text)
    for hashtag in hashtags:
        replacement = ''
        if hashtag.upper() == hashtag:
            replacement = '<HASHTAG> {} <ALLCAPS>'.format(hashtag)
        else:
            replacement = '<HASHTAG> ' + re.sub(r'(?<=\w)(?=[A-Z])', ' ', hashtag)
        try:
            text = re.sub(hashtag, replacement, text)
        except:
            print('Problem with hashtag {}... skipping.'.format(hashtag))
    text = re.sub("\[\[User(.*)\|", '<USER>', text)
    text = re.sub("<3", '<HEART>', text)
    text = re.sub("[-+]?[.\d]*[\d]+[:,.\d]*", "<NUMBER>", text)
    text = re.sub(eyes + nose + "[Dd)]", '<SMILE>', text)
    text = re.sub("[(d]" + nose + eyes, '<SMILE>', text)
    text = re.sub(eyes + nose + "p", '<LOLFACE>', text)
    text = re.sub(eyes + nose + "\(", '<SADFACE>', text)
    text = re.sub("\)" + nose + eyes, '<SADFACE>', text)
    text = re.sub(eyes + nose + "[/|l*]", '<NEUTRALFACE>', text)
    text = re.sub("/", " / ", text)
    text = re.sub("[-+]?[.\d]*[\d]+[:,.\d]*", "<NUMBER>", text)
    text = re.sub("([!]){2,}", "! <REPEAT>", text)
    text = re.sub("([?]){2,}", "? <REPEAT>", text)
    text = re.sub("([.]){2,}", ". <REPEAT>", text)
    pattern = re.compile(r"(.)\1{2,}")
    text = pattern.sub(r"\1" + " <ELONG>", text)
    
    return text