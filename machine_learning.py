# -*- coding: utf-8 -*-
"""
Created on Fri Aug 31 16:46:11 2018

@author: mckaydjensen
"""


import pandas as pd
import json

from sklearn.model_selection import train_test_split
from sklearn import linear_model
from sklearn import metrics
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.externals import joblib

#local package
import text_processing


def rebuild_model(sexist_src, control_src, features='count', report=True):
    
    #Import data
    tweets, markers = text_processing.import_data(sexist_src, control_src)
    #Separate into train and test sets
    train_x, validate_x, train_y, validate_y = train_test_split(tweets, markers)
    
    #Set up features
    xtrain_features, xvalid_features = None, None
    if features == 'count':
        countVect = CountVectorizer(analyzer='word',
                                    tokenizer=text_processing.tokenize_status_text)
        countVect.fit(tweets)
        xtrain_features =  countVect.transform(train_x)
        xvalid_features =  countVect.transform(validate_x)
    elif features == 'tfidf':
        # word-level TfidfVectorizer
        tfidfVect = TfidfVectorizer(analyzer='word', max_features=5000,
                                    tokenizer=text_processing.tokenize_status_text)
        tfidfVect.fit(tweets)
        xtrain_features =  tfidfVect.transform(train_x)
        xvalid_features =  tfidfVect.transform(validate_x)
    else:
        print('features argument must be "count" or "tfidf"')
        return
    
    classifier = linear_model.LogisticRegression()
    classifier.fit(xtrain_features, train_y)
    
    #Pickle model
    joblib.dump(classifier, 'model.pkl')
    #Save other data about the model
    metadata = {'features': features, 'training_text': tweets}
    with open('model_metadata.json', 'w', encoding='utf-8') as fh:
        json.dump(metadata, fh, ensure_ascii=False)
    
    #Predict the labels on validation dataset
    predictions = classifier.predict(xvalid_features)
    
    if report:
        print('Accuracy:',
              metrics.accuracy_score(validate_y, predictions))
        print('Classification Report:\n',
              metrics.classification_report(validate_y, predictions))



def unpickle_model(filename='model.pkl'):
    return joblib.load(filename)


def predict(text):
    classifier = unpickle_model()
    with open('model_metadata.json', 'r', encoding='utf-8') as fh:
        metadata = json.load(fh)
    vectorizer = None
    if metadata['features'] == 'count':
        vectorizer = CountVectorizer(analyzer='word',
                                     tokenizer=text_processing.tokenize_status_text)
    elif metadata['features'] == 'tfidf':
        vectorizer = TfidfVectorizer(analyzer='word', max_features=5000,
                                     tokenizer=text_processing.tokenize_status_text)
    vectorizer.fit(metadata['training_text'])
    if type(text) in (bytes, str):
        text = [text]
    features = vectorizer.transform(text)
    return classifier.predict(features)