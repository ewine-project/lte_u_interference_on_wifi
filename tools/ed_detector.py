# -*- coding: utf-8 -*-
"""
This is a simple detector which estimates the effective available airtime for
WiFi by analyzing the MAC state energy-detection without packet reception as
indicator for strong interference and is being blocked for WiFi.

@author: Zubow (TU Berlin)
"""
import re
import json
import gzip
import pickle
import os
import numpy as np
import pickle
import pprint
import matplotlib
import matplotlib.pyplot as plt

### EdDetector ###
class EdDetector():
    def __init__(self, threshold=0.1):
        self.threshold = threshold

    def estimate_eff_available_airtime_wifi(self, regmon_dat):
        # relative time spent in each bin in state interference
        intf_ratio = regmon_dat['d_others'] / regmon_dat['d_mac']
        # count the number of bins with sufficient large interference value
        vals_above_thr = intf_ratio[np.where(intf_ratio > self.threshold)]
        # take ratio between interfered bins and total bins as LTE-U duty cycle
        num_bins_in_intf = vals_above_thr.shape[0] / regmon_dat.size
        # only bins with low interference levels can be used by WiFI
        eff_available_airtime_wifi = 1 - num_bins_in_intf

        print('Estimated eff. available airtime wifi: %f' % eff_available_airtime_wifi)

        return eff_available_airtime_wifi