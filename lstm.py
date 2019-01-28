# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 10:55:11 2019

@author: mckaydjensen
"""

import numpy as np
#import matplotlib.pyplot as plt
import text_processing

from keras.models import Sequential
from keras.layers import Embedding, LSTM, Dense, Dropout
from keras.optimizers import Adam

from sklearn import metrics
from sklearn.utils import class_weight


EMB_WEIGHTS_FILE = 'embedding_weights.npy'
TRAINING_DATA = 'training_data/NAACL_revised.csv'

np.random.seed(152)



def prob_to_class(predictions, cutoff=0.5):
    return np.array([1 if p[0] > cutoff else 0 for p in predictions])



def build_model(emb_weights, train_embedding=True):
    
    embedding = Embedding(input_dim=emb_weights.shape[0],
                          output_dim=emb_weights.shape[1],
                          weights=[emb_weights],
                          input_length=text_processing.MAX_INPUT_LENGTH,
                          trainable=train_embedding)
    
    model = Sequential()
    model.add(embedding)
    model.add(Dropout(0.25))
    model.add(LSTM(50, activation='elu'))
    model.add(Dropout(0.5))
    model.add(Dense(1, activation='sigmoid'))
    
    model.compile(loss='binary_crossentropy', optimizer=Adam(amsgrad=True),
                  metrics=['accuracy'])
    model.summary()
    return model



def evaluate_model(X, y, emb_weights, train_embedding=True,
                   batch_size=500, epochs=20, folds=5, verbose=True):
    
    #Split into folds
    #Shuffle both X and y in the same way
    assert len(X) == len(y)
    permutation = np.random.permutation(len(X))
    X, y = X[permutation], y[permutation]
    X_folds = np.array_split(X, folds)
    y_folds = np.array_split(y, folds)
    
    #Set class weights for better training
    class_weights = class_weight.compute_class_weight('balanced',
                                                      np.unique(y), y)
    
    #Create metric lists to return
    hists = []
    precisions = []
    recalls = []
    f1s = []
    
    #Evaluate on each fold
    for i in range(folds):
        X_train = np.concatenate([X_folds[j] \
                                  for j in range(folds) if j != i])
        y_train = np.concatenate([y_folds[j] \
                                  for j in range(folds) if j != i])
        X_test = X_folds[i]
        y_test = y_folds[i]
        model = build_model(emb_weights, train_embedding)
        hist = model.fit(X_train, y_train, batch_size=batch_size,
                         epochs=epochs, validation_data=(X_test, y_test),
                         class_weight=class_weights, verbose=int(verbose))
        hists.append(hist.history)
        y_predicted = prob_to_class(model.predict(X_test))
        precision = metrics.precision_score(y_test, y_predicted,
                                            average='weighted')
        recall = metrics.recall_score(y_test, y_predicted, average='weighted')
        f1 = metrics.f1_score(y_test, y_predicted, average='weighted')
        if verbose:
            print('Scores for fold {}:'.format(i))
            print('Precision:', precision)
            print('Recall:', recall)
            print('F1 score:', f1)
        precisions.append(precision)
        recalls.append(recalls)
        f1s.append(f1)
    return hists, precisions, recalls, f1s



if __name__ == '__main__':
    
    X, y = text_processing.load_and_prepare_data(TRAINING_DATA)
    emb_weights = np.load(EMB_WEIGHTS_FILE)
    
    #TODO: add argparse functionality
    evaluate_model(X, y, emb_weights)