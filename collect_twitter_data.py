# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 14:15:09 2019

@author: mckaydjensen
"""

import sys
import twitter
from datetime import datetime, timedelta
from time import sleep

SAMPLE_TIME = 10
MINIBATCH_SIZE = 1000
SAVE_DIR = 'twitter_data'


#Takes a sample over a period of 10 minutes every hour
# for a specified number of hours
def main(hour_count):
    starttime = datetime.now()
    logger = open(SAVE_DIR + '/log.txt', 'a')
    for hour in range(hour_count):
        dt = starttime + timedelta(hours=hour)
        dt_plus_ten = dt + timedelta(minutes=10)
        results = []
        #Wait until we reach the start time
        while datetime.now() < dt:
            sleep(10)
        #Keep sampling until our sampling window passes
        #We don't take the same number of samples every hour since then
        # some hours (e.g. middle of the night) would be overrepresented
        while datetime.now() < dt_plus_ten:
            results += twitter.download_results(MINIBATCH_SIZE)
        timestamp = dt.strftime('%a %d-%m-%Y %H-%M-%S')
        mssg = 'Collected {0} tweets for time {1}'.format(
                                                       len(results), timestamp)
        print(mssg)
        logger.write(mssg + '\n')
        twitter.publish_json(results, SAVE_DIR + '/' + timestamp + '.json')
    logger.close()


if __name__ == '__main__':
    hour_count = int(sys.argv[1])
    main(hour_count)