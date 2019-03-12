# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 14:40:01 2019

@author: mckaydjensen
"""

import numpy as np
import json

from scipy.stats import t

ERROR_STATS_FILE = 'ppvs_and_fors.json'

#Load the PPV and FOR values calculated for the model
#PPV = Positive Predictive Value (i.e. Precision)
#FOR = False Omission Rate
with open(ERROR_STATS_FILE, 'r') as fh:
    stats_dict = json.load(fh)
ppvs = stats_dict['PPV']
fors = stats_dict['FOR']

assert len(ppvs) == len(fors)
N = len(ppvs)

#Calculate mean of PPV and FOR
mean_ppv = np.mean(ppvs)
mean_for = np.mean(fors)

#Calculate variance of PPV and FOR
var_ppv = np.var(ppvs, ddof=1)
var_for = np.var(fors, ddof=1)

#Calculate the covariance of PPV and FOR
covar = np.cov(ppvs, fors)[0][1]


#Given the proportion of a sample that is predicted to be positive
# and the proportion that is predicted to be negative (positive_predicted and 
# negative_predicted, respectively), estimates the proportion of the sample
# that is actually positive.
def estimate_positive_proportion(positive_predicted):
    
    negative_predicted = 1 - positive_predicted
    expected_value = (mean_ppv * positive_predicted
                      + mean_for * negative_predicted)
    #Calculate the variance of the variable using propagation of uncertainty
    # f = a*A + b*B => varf = a^2 * varA + b^2 * varB + 2ab*covarAB
    var_estimate = (positive_predicted**2 * var_ppv
                    + negative_predicted**2 * var_for
                    + 2 * negative_predicted * positive_predicted * covar)
    return expected_value, var_estimate


def get_confidence_interval(expected_value, var_estimate, df=N-1, alpha=0.95):
    t_scores = t.ppf([(1-alpha)/2, (1+alpha)/2], df=df)
    return expected_value + np.sqrt(var_estimate) * t_scores


def mean_and_var_for_population(sample):
    
    n = len(sample)
    
    expected_values = []
    var_estimates = []
    for x in sample:
        expected_value, var_estimate = estimate_positive_proportion(x)
        expected_values.append(expected_value)
        var_estimates.append(var_estimate)
    
    population_exp_val = np.mean(expected_values)
    population_var_est = np.sum(var_estimates) / n**2
    
    return population_exp_val, population_var_est


def conf_interval_for_population_mean(sample, alpha=0.95):
    n = len(sample)
    population_exp_val, population_var_est = mean_and_var_for_population(sample)
    return get_confidence_interval(population_exp_val, population_var_est,
                                   df=n-1, alpha=alpha)