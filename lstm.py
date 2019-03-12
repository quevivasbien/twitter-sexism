# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 10:55:11 2019

@author: mckaydjensen
"""

import sys
import json
import numpy as np
import text_processing

from keras.models import Sequential
from keras.layers import Embedding, LSTM, Dense, Dropout
from keras.optimizers import Adam

from sklearn import metrics
from sklearn.utils import class_weight


EMB_WEIGHTS_FILE = 'embedding_weights.npy'
TRAINING_DATA = 'training_data/NAACL_revised.csv'

ERROR_STATS_FILE = 'ppvs_and_fors.json'

np.random.seed(152)



def prob_to_class(predictions, cutoff=0.5):
    return np.array([1 if p[0] > cutoff else 0 for p in predictions])


def get_metrics(y_test, y_predicted, normalize_conf_matrix=True):
    precision = metrics.precision_score(y_test, y_predicted,
                                            average='weighted')
    recall = metrics.recall_score(y_test, y_predicted, average='weighted')
    f1 = metrics.f1_score(y_test, y_predicted, average='weighted')
    confusion_matrix = metrics.confusion_matrix(y_test, y_predicted)
    if normalize_conf_matrix:
        confusion_matrix = confusion_matrix / np.sum(confusion_matrix)
    return precision, recall, f1, confusion_matrix


#Given a list of binary confusion matrices, return the positive predictive
    # values (i.e. precision) and the false ommission rates for each matrix
def get_PPV_and_FOR(confusion_matrices):
    if len(confusion_matrices) == 1:
        confusion_matrices = [confusion_matrices]
    PPVs = [cm[1][1] / (cm[0][1] + cm[1][1]) for cm in confusion_matrices]
    FORs = [cm[1][0] / (cm[0][0] + cm[1][0]) for cm in confusion_matrices]
    return PPVs, FORs


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
    #model.summary()
    return model



def evaluate_model(X, y, emb_weights, train_embedding=True,
                   batch_size=500, epochs=20, folds=10, verbose=True):
    
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
    precisions = []
    recalls = []
    f1s = []
    confusion_matrices = []
    
    #Evaluate on each fold
    for i in range(folds):
        X_train = np.concatenate([X_folds[j] \
                                  for j in range(folds) if j != i])
        y_train = np.concatenate([y_folds[j] \
                                  for j in range(folds) if j != i])
        X_test = X_folds[i]
        y_test = y_folds[i]
        model = build_model(emb_weights, train_embedding)
        model.fit(X_train, y_train, batch_size=batch_size,
                  epochs=epochs, validation_data=(X_test, y_test),
                  class_weight=class_weights, verbose=int(verbose))
        y_predicted = prob_to_class(model.predict(X_test))
        precision, recall, f1, conf_matrix = get_metrics(y_test, y_predicted)
        if verbose:
            print('Scores for fold {}:'.format(i))
            print('Precision:', precision)
            print('Recall:', recall)
            print('F1 score:', f1)
            print('Confusion matrix:\n{}'.format(conf_matrix))
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        confusion_matrices.append(conf_matrix)
    return precisions, recalls, f1s, confusion_matrices



def train_model(X, y, emb_weights, train_embedding=True, batch_size=500,
                epochs=20):
    class_weights = class_weight.compute_class_weight('balanced',
                                                      np.unique(y), y)
    model = build_model(emb_weights, train_embedding)
    #Train on all the available labeled data
    model.fit(X, y, batch_size=batch_size, epochs=epochs,
              class_weight=class_weights)
    return model



if __name__ == '__main__':
    
    if len(sys.argv) < 2 or (sys.argv[1] != 'eval' and sys.argv[1] != 'train'):
        print('input "python lstm.py eval" to test config with k-fold eval.\n'
              'input "python lstm.py train FILENAME" to train model and save to'
              ' FILENAME. If FILENAME arg is excluded, default is "model.h5".')
        sys.exit()
        
    X, y = text_processing.load_and_prepare_data(TRAINING_DATA)
    emb_weights = np.load(EMB_WEIGHTS_FILE)
        
    if sys.argv[1] == 'eval':
        p, r, f, cm = evaluate_model(X, y, emb_weights)
        print('Average scores:')
        print('Precision: {}\nRecall: {}\nF1 score: {}'.format(np.mean(p),
              np.mean(r), np.mean(f)))
        #Save positive predictive values and false omission rates to a json
        # file. These will be useful later.
        PPVs, FORs = get_PPV_and_FOR(cm)
        with open(ERROR_STATS_FILE, 'w') as fh:
            json.dump({'PPV': PPVs, 'FOR': FORs}, fh)
    elif sys.argv[1] == 'train':
        model = train_model(X, y, emb_weights)
        filename = sys.argv[2] if len(sys.argv) > 2 else 'model.h5'
        model.save(filename)
    