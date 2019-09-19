# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 14:40:01 2019

@author: mckaydjensen
"""

import numpy as np
import json

#from scipy.stats import t

CONFUSION_MATRICES = 'confusion_matrices90.json'

#Load the PPV and FOR values calculated for the model
#PPV = Positive Predictive Value (i.e. Precision)
#FOR = False Omission Rate
with open(CONFUSION_MATRICES, 'r') as fh:
    conf_matrices = np.array(json.load(fh))


def construct_alt_matrix(cm, p):
    coeffs = np.linalg.solve(cm.T, np.array([1-p, p]))
    #print(coeffs)
    return np.diag(coeffs).dot(cm)

    

def mean_and_var_of_pi_dist(p):
    alt_conf_matrices = [construct_alt_matrix(cm, p) for cm in conf_matrices]
    Pi = [cm[1][0] + cm[1][1] for cm in alt_conf_matrices]
    mean = np.mean(Pi)
    var = np.var(Pi, ddof=1)
    return mean, var


def estimate_Q(P):
    Mean, Var = [], []
    for p in P:
        mean, var = mean_and_var_of_pi_dist(p)
        Mean.append(mean)
        Var.append(var)
    pop_mean = np.mean(Mean)
    pop_var = (1 / len(Var)**2) * sum(Var)
    return pop_mean, pop_var


def pred_error(crit=0.05):
    cm = np.mean(conf_matrices, axis=0)
    alpha = (1-crit)/(cm[0,0] + cm[0,1])
    beta = crit/(cm[1,0] + cm[1,1])
    cm = np.diag([alpha, beta]).dot(cm)
    return cm[0,1] - cm[1,0]