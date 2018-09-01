# -*- coding: utf-8 -*-
"""
Created on Fri Aug 31 16:46:11 2018

@author: mckaydjensen
"""



import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence
np.random.seed(7)

max_tokens = 5000
