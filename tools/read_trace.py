# -*- coding: utf-8 -*-
"""
This example script reads recorded data.

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

# base folder
base_dir = '../traces/wiplus_dl_lte-fb_20161223/'

# walk through all trace files
for x in os.walk(base_dir):
    # strep through each measurement
    directory = x[0]
    print('Parsing folder %s' % directory)

    try:
        # Config
        print('Loading RegMon data...')
        fname = os.path.join(directory, 'config.json')
        cfg = Config()
        config_data = cfg.load_config(fname)
        meta_data = cfg.get_meta_data_from_fname(config_data['common']['meas_name'])
        cfg.print(config_data)
        cfg.print(meta_data)

        lte_u_dc = None
        lte_u_tx_pwr = None
        for item in meta_data['lteu']:
            if item.startswith('duty'):
                re_match = re.search(r'[^a-z][\d]',item)
                lte_u_dc = float(re_match.group()) / 100.0
            if item.endswith('dbm'):
                lte_u_tx_pwr = int(re.search(r'-?[\d]*',item).group())

        print('Configured LTE-U duty cycle: %f' % lte_u_dc)

        # RegMon
        print('Loading RegMon data...')
        fname = os.path.join(directory, config_data['regmon']['result_file'])
        regmon = RegMon()
        regmon_rawdat = regmon.load_data(fname)
        regmon_dat = regmon.decode_regmon_data(regmon_rawdat)
        regmon.show_timing_info(regmon_dat)
        #regmon.plot_data(regmon_dat)

        # Iperf
        print('Loading iperf data...')
        fname = os.path.join(directory, config_data['iperf3']['result_file'])
        iperf = Iperf3()
        iperf_rawdat = iperf.load_data(fname)
        iperf3_dat = iperf.decode_iperf3_data(iperf_rawdat)
        iperf.show_timing_info(iperf3_dat)
        norm_tx_thr = iperf.get_normalized_tx_thr(iperf3_dat, 29.0)
        real_airtime = norm_tx_thr

    except Exception as ex:
        print('Failed to parse %s, %s' % (directory, str(ex)))
        pass
