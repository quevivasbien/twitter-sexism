# -*- coding: utf-8 -*-
"""
Created on Tue Sep 4 23:38:09 2018

@author: mckaydjensen
"""

import pandas as pd
import numpy as np

#local packages
import twitter
import text_processing

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.models import load_model

np.random.seed(152)



class SexismClassifier(object):
    
    def __init__(self, corpus_text='corpus_text.json', saved_model='model.h5'):
        self.model = load_model(saved_model)
        MAX_VOCAB_SIZE=20000
        self.tokenizer = Tokenizer(num_words=MAX_VOCAB_SIZE)
        self.tokenizer.fit_on_texts(text_processing.load_json(corpus_text))
        
   
    def prepare_text(self, text):
        text = [text_processing.glove_preprocess(t) for t in text]
        sequences = self.tokenizer.texts_to_sequences(text)
        MAX_SEQUENCE_LENGTH = 128
        data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)
        return data
    
    def predict(self, text):
        if type(text) in (bytes, str):
            text = [text]
        data = self.prepare_text(text)
        return self.model.predict(data)



def process_data(source_filename, lang=None):
    data = text_processing.load_json(source_filename)
    #Remove data with no place info
    data = [d for d in data if d['place']]
    #Filter by language if requested
    if lang:
        data = [d for d in data if d['lang'] == lang]
    df = pd.DataFrame({
                'text': [tweet['text'] for tweet in data],
                'place': [twitter.reduce_place(tweet['place']) for tweet in data],
                'timestamp': [tweet['timestamp'] for tweet in data]
            })
    clf = SexismClassifier()
    predictions = clf.predict(df['text'])
    df['is_sexist'] = predictions
    return df