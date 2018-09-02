# -*- coding: utf-8 -*-
"""
Created on Fri Aug 31 16:46:11 2018

@author: mckaydjensen
"""

import json
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn import linear_model
from sklearn import metrics
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.externals import joblib

#local packages
import text_processing as tp
import twitter

class SexismClassifier(object):
    
    def __init__(self, pickled_model='model.pkl',
                 metadata='model_metadata.json'):
        
        self.classifier = joblib.load(pickled_model)
        
        with open('model_metadata.json', 'r', encoding='utf-8') as fh:
            metadata = json.load(fh)
        self.vectorizer = None
        if metadata['features'] == 'count':
            self.vectorizer = CountVectorizer(analyzer='word',
                                         tokenizer=tp.tokenize_status_text)
        elif metadata['features'] == 'tfidf':
            self.vectorizer = TfidfVectorizer(analyzer='word', max_features=5000,
                                         tokenizer=tp.tokenize_status_text)
        self.vectorizer.fit(metadata['training_text'])
        
    
    def rebuild_model(self, sexist_src, control_src, features='count',
                      report=True):
        #Import data
        tweets, markers = tp.import_data(sexist_src, control_src)
        #Separate into train and test sets
        train_x, validate_x, train_y, validate_y = train_test_split(tweets,
                                                                    markers)
        
        #Set up features
        xtrain_features, xvalid_features = None, None
        if features == 'count':
            self.vectorizer = CountVectorizer(analyzer='word',
                                        tokenizer=tp.tokenize_status_text)
        elif features == 'tfidf':
            # word-level TfidfVectorizer
            self.vectorizer = TfidfVectorizer(analyzer='word', max_features=5000,
                                        tokenizer=tp.tokenize_status_text)
        else:
            print('features argument must be "count" or "tfidf"')
            return
        self.vectorizer.fit(tweets)
        xtrain_features =  self.vectorizer.transform(train_x)
        xvalid_features =  self.vectorizer.transform(validate_x)
        
        self.classifier = linear_model.LogisticRegression()
        self.classifier.fit(xtrain_features, train_y)
        
        #Pickle model
        joblib.dump(self.classifier, 'model.pkl')
        #Save other data about the model
        metadata = {'features': features, 'training_text': tweets}
        with open('model_metadata.json', 'w', encoding='utf-8') as fh:
            json.dump(metadata, fh, ensure_ascii=False)
        
        #Predict the labels on validation dataset
        predictions = self.classifier.predict(xvalid_features)
        
        if report:
            print('Accuracy:',
                  metrics.accuracy_score(validate_y, predictions))
            print('Classification Report:\n',
                  metrics.classification_report(validate_y, predictions))
        
        
    def predict(self, text):
        if type(text) in (bytes, str):
            text = [text]
        features = self.vectorizer.transform(text)
        return self.classifier.predict(features)



def process_data(source_filename):
    data = twitter.load_results(source_filename)
    df = pd.DataFrame({
                'text': [tweet['text'] for tweet in data],
                'place': [twitter.reduce_place(tweet['place']) for tweet in data],
                'timestamp': [tweet['timestamp'] for tweet in data]
            })
    clf = SexismClassifier()
    predictions = clf.predict(df['text'])
    df['is_sexist'] = predictions
    return df