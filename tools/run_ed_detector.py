# -*- coding: utf-8 -*-
"""
This example script runs the simple ED detector..

@author: Olbrich, Zubow (TU Berlin)
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

from parser import Iperf3, RegMon, Config
from ed_detector import EdDetector

DEBUG = False
# base folder
base_dir = '../traces/wiplus_dl_lte-fb_20161223/'

print('Running the ED detector ... start')

all_res = []
pp = pprint.PrettyPrinter(indent=4)

for x in os.walk(base_dir):
    # strep through each measurement
    directory = x[0]
    print('Parsing folder %s' % directory)

    try:
	##
        # Config
        print('Loading config data...')
        fname = os.path.join(directory, 'config.json')
        cfg = Config()
        config_data = cfg.load_config(fname)
        meta_data = cfg.get_meta_data_from_fname(config_data['common']['meas_name'])

        lte_u_dc = None
        lte_u_tx_pwr = None
        for item in meta_data['lteu']:
            if item.startswith('duty'):
                re_match = re.search(r'[^a-z][\d]',item)
                lte_u_dc = float(re_match.group()) / 100.0
            if item.endswith('dbm'):
                lte_u_tx_pwr = int(re.search(r'-?[\d]*',item).group())

        if DEBUG:
            print('Configured LTE-U duty cycle: %f' % lte_u_dc)

	##
        # RegMon
        if DEBUG:
            print('Loading RegMon data...')
        fname = os.path.join(directory, config_data['regmon']['result_file'])
        regmon = RegMon()
        regmon_rawdat = regmon.load_data(fname)
        regmon_dat = regmon.decode_regmon_data(regmon_rawdat)
        if DEBUG:
            regmon.show_timing_info(regmon_dat)
        #regmon.plot_data(regmon_dat)

	##
        # Iperf
        if DEBUG:
            print('Loading iperf data...')
        fname = os.path.join(directory, config_data['iperf3']['result_file'])
        iperf = Iperf3()
        iperf_rawdat = iperf.load_data(fname)
        iperf3_dat = iperf.decode_iperf3_data(iperf_rawdat)
        if DEBUG:
            iperf.show_timing_info(iperf3_dat)
        norm_tx_thr = iperf.get_normalized_tx_thr(iperf3_dat, 29.0)
        real_airtime = norm_tx_thr

	##
        # Simple ED detector
        ed_detector = EdDetector()
        est_airtime = ed_detector.estimate_eff_available_airtime_wifi(regmon_dat)

        print('RESULT: LTE-U tx pwr %d, Real vs. estimated airtime (ED detector): %f | %f' % (lte_u_tx_pwr, real_airtime, est_airtime))
        all_res.append([lte_u_tx_pwr, real_airtime, est_airtime])

    except Exception as ex:
        print('Failed to parse %s, %s' % (directory, str(ex)))
        pass

print('Running the ED detector ... stop')

print('Final results for ED detector ...')
print('LTE-U TX power | real eff. airtime | estimated eff. airtime')
pp.pprint(all_res)

