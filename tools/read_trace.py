# -*- coding: utf-8 -*-
"""
This example script reads recorded data.

@author: Zubow, TU Berlin
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

### Iperf3 data ###
class Iperf3():
    def __init__(self):
        pass

    def load_data(self, fn):
        data = None
        with gzip.open(fn, 'rb') as fo:
            pkl_dat = pickle.load(fo).decode('utf-8')
            pkl_dat = re.sub('-nan', 'NaN', pkl_dat) # fix python json failure
            data = json.loads(pkl_dat)
        return data

    def decode_iperf3_data(self, dat, debug=False):
        num_samples = len(dat['intervals'])
        print('Decoding %d Iperf3 samples...' % num_samples)

        rx = False
        if (dat['start']['test_start']['reverse'] == 1):
            rx = True

        t_start_sec = int(dat['start']['cookie'].split('.')[1])
        t_start_usec = int(dat['start']['cookie'].split('.')[2])
        ktime_start = int('%d%06d000' % (t_start_sec, t_start_usec)) # nsec

        # init result matrix
        ret_dtype = np.dtype([
            ('ktime', np.uint64),
            ('rx_thrpt', np.float64),
            ('tx_thrpt', np.float64),
        ])
        ret = np.full(num_samples, np.nan, dtype=ret_dtype)

        for ival_cnt, ival in enumerate(dat['intervals']):
            ktime = ktime_start + int(float(ival['sum']['end']) * 1e9) # nsec
            thrpt = ival['sum']['bits_per_second'] / 1e6 # Mbps
            rx_thrpt = 0.0
            tx_thrpt = 0.0
            if rx:
                rx_thrpt = thrpt
            else:
                tx_thrpt = thrpt
            ret[ival_cnt] = (ktime, rx_thrpt, tx_thrpt)
        return ret

    def show_timing_info(self, iperf3_dat):
        # timing data
        iperf3_ts = iperf3_dat['ktime']
        iperf3_t_res = np.mean(np.ediff1d(iperf3_ts))  # ns
        iperf3_t_start = np.nanmin(iperf3_ts)  # ns
        iperf3_t_end = np.nanmax(iperf3_ts)  # ns
        iperf3_t_range = (iperf3_t_end - iperf3_t_start) / 1e9  # s
        print('Iperf3 start:      %d' % iperf3_t_start)
        print('Iperf3 end:        %d' % iperf3_t_end)
        print('Iperf3 resolution: %d nsec' % iperf3_t_res)
        print('Iperf3 duration:   %f sec' % iperf3_t_range)
        print('')

        iperf3_estats = {'tx_thrpt': {}, 'rx_thrpt': {}}
        iperf3_estats['tx_thrpt']['avg'] = np.nanmean(iperf3_dat['tx_thrpt'])
        iperf3_estats['rx_thrpt']['avg'] = np.nanmean(iperf3_dat['rx_thrpt'])
        print('Mean RX throughput: %.2f Mbps' % iperf3_estats['rx_thrpt']['avg'])
        print('Mean TX throughput: %.2f Mbps' % iperf3_estats['tx_thrpt']['avg'])
        print('')

### RegMon data: https://github.com/thuehn/RegMon ###
class RegMon():
    def __init__(self):
        super().__init__()

    def load_data(self, fn):
        data = []
        with gzip.open(fn, 'rb') as fo:
            while True:
                try:
                    data_part = pickle.load(fo)
                    data.extend(data_part)
                except EOFError:
                    break
        return data

    def get_regmon_fields(self, line):
        # data format:
        # kernel timestamp, TSFT (64 bit), MAC Busy (32 bit), TX busy (32 bit),
        # RX Busy (32 bit), RX Busy counts (32 bit), lower TSFT (32 bit)
        fields = line.split(' ')

        #    import struct
        #    ftsf = struct.unpack('>Q', bytes.fromhex(fields[1]))
        #    mac = struct.unpack('>L', bytes.fromhex(fields[2]))
        #    tx = struct.unpack('>L', bytes.fromhex(fields[3]))

        ktime = int(fields[0])
        ftsf = int(fields[1], 16)
        mac = int(fields[2], 16)
        tx = int(fields[3], 16)
        rx = int(fields[4], 16)
        ed = int(fields[5], 16)
        ltsf = int(fields[6], 16)
        reg7 = int(fields[7], 16)
        reg8 = int(fields[8], 16)
        reg9 = int(fields[9], 16)
        reg10 = int(fields[10], 16)
        reg11 = int(fields[11], 16)
        return (ktime, ftsf, mac, tx, rx, ed, ltsf, reg7, reg8, reg9, reg10, reg11)

    def decode_regmon_data(self, dat, debug=False):

        # remove empty lines first
        dat = list(filter(None, dat))
        print('Decoding %d RegMon samples...' % len(dat))

        # init result matrix
        ret_dtype = np.dtype([
            ('ktime', np.uint64),
            ('ktime_start', np.uint64),
            ('ktime_stop', np.uint64),
            ('d_mac', np.float64),
            ('d_tx', np.float64),
            ('d_rx', np.float64),
            ('d_idle', np.float64),
            ('d_others', np.float64),
            ('d_fack', np.float64),
            ('rel_tx', np.float64),
            ('rel_rx', np.float64),
            ('rel_idle', np.float64),
            ('rel_others', np.float64),
        ])
        ret = np.full((len(dat) - 1), np.nan, dtype=ret_dtype)

        for line_cnt, line in enumerate(dat):
            if (line_cnt == 0):

                (ktime_old, ftsf, mac_old, tx_old, rx_old, ed_old, ltsf, reg7_old, reg8_old, reg9_old, reg10_old,
                 reg11_old) = self.get_regmon_fields(line)

            elif (line_cnt > 0):

                (ktime, ftsf, mac_now, tx_now, rx_now, ed_now, ltsf, reg7_now, reg8_now, reg9_now, reg10_now,
                 reg11_now) = self.get_regmon_fields(line)
                # read_duration = ltsf - (ftsf & 0x00000000FFFFFFFF) # usec

                if (mac_now > mac_old):

                    # mac busy delta
                    d_mac = mac_now - mac_old  # in mac clock ticks

                    # tx delta
                    d_tx = tx_now - tx_old  # TX busy, in mac clock ticks
                    if (d_tx <= d_mac):
                        rel_tx = d_tx / d_mac * 100
                    else:
                        d_tx = 0
                        rel_tx = 0

                    # rx delta
                    d_rx = rx_now - rx_old  # TX busy, in mac clock ticks
                    if (d_rx <= d_mac):
                        rel_rx = d_rx / d_mac * 100
                    else:
                        d_rx = 0
                        rel_rx = 0

                    # full busy delta
                    d_ed = ed_now - ed_old  # TX busy, in mac clock ticks
                    if (d_ed <= d_mac):
                        rel_ed = d_ed / d_mac * 100
                    else:
                        d_ed = 0
                        rel_ed = 0

                    # ACK failures
                    d_fack = reg7_now

                    # calculate channel idle states, in mac clock ticks
                    d_idle = d_mac - d_ed
                    if (d_idle > 0):
                        rel_idle = d_idle / d_mac * 100
                    else:
                        d_idle = 0
                        rel_idle = 0

                    # calculate busy states that are triggered from other sources but rx & tx
                    d_others = d_ed - d_tx - d_rx
                    if (d_others > 0):
                        rel_others = d_others / d_mac * 100
                    else:
                        d_others = 0
                        rel_others = 0

                else:  # MIB reset
                    (ktime, ftsf, d_mac, d_tx, d_rx, d_ed, ltsf, reg7, reg8, reg9, reg10, reg11) = self.get_regmon_fields(
                        line)

                    # validate input data in case of a reset
                    if (d_mac - d_ed > 0):
                        d_idle = d_mac - d_ed
                    else:
                        d_idle = 0

                    if (d_ed - (d_tx + d_rx) > 0):
                        d_others = d_ed - (d_tx + d_rx)
                    else:
                        d_others = 0

                    d_fack = reg7_now

                    if (d_mac > 0):
                        rel_tx = d_tx / d_mac * 100
                        rel_rx = d_rx / d_mac * 100
                        rel_ed = d_ed / d_mac * 100
                        rel_idle = d_idle / d_mac * 100
                        rel_others = d_others / d_mac * 100
                    else:
                        rel_tx = np.nan
                        rel_rx = np.nan
                        rel_ed = np.nan
                        rel_idle = np.nan
                        rel_others = np.nan

                if debug:
                    print('%d\t%d\t%d\t%d\t%d\t%.2f%%\t%.2f%%\t%.2f%%\t%.2f%%\t[TX,RX,IDLE,OTHERS]' % (
                    ktime, d_tx, d_rx, d_idle, d_others, rel_tx, rel_rx, rel_idle, rel_others))

                ret[line_cnt - 1]['ktime'] = ktime
                ret[line_cnt - 1]['ktime_start'] = ktime_old
                ret[line_cnt - 1]['ktime_stop'] = ktime
                ret[line_cnt - 1]['d_mac'] = d_mac
                ret[line_cnt - 1]['d_tx'] = d_tx
                ret[line_cnt - 1]['d_rx'] = d_rx
                ret[line_cnt - 1]['d_idle'] = d_idle
                ret[line_cnt - 1]['d_others'] = d_others
                ret[line_cnt - 1]['d_fack'] = d_fack
                ret[line_cnt - 1]['rel_tx'] = rel_tx
                ret[line_cnt - 1]['rel_rx'] = rel_rx
                ret[line_cnt - 1]['rel_idle'] = rel_idle
                ret[line_cnt - 1]['rel_others'] = rel_others

                ktime_old = ktime
                mac_old = mac_now
                tx_old = tx_now
                rx_old = rx_now
                ed_old = ed_now

        return ret

    def show_timing_info(self, regmon_dat):
        # RegMon timing data
        regmon_ts = regmon_dat['ktime']
        regmon_t_res = np.mean(np.ediff1d(regmon_ts)) # ns
        regmon_t_start = np.nanmin(regmon_ts)
        regmon_t_end = np.nanmax(regmon_ts)
        regmon_t_range = (regmon_t_end - regmon_t_start) / 1e9 # s
        print('RegMon start:      %d' % regmon_t_start)
        print('RegMon end:        %d' % regmon_t_end)
        print('RegMon resolution: %d nsec' % regmon_t_res)
        print('RegMon duration:   %f sec' % regmon_t_range)
        print('')

    def plot_data(self, regmon_edat):

        print('Plotting results...')
        # color definitions
        c0 = (0, 0, 0, 100)
        c1 = (240, 83, 84, 100)
        c2 = (55, 168, 251, 100)
        c3 = (243, 214, 127, 100)
        c4 = (212, 118, 239, 100)
        c5 = (183, 16, 16, 100)

        matplotlib.colors.ColorConverter.colors['grafana1'] = (0.20, 0.20, 0.20)
        matplotlib.colors.ColorConverter.colors['grafana2'] = (0.31, 0.29, 0.29)
        matplotlib.colors.ColorConverter.colors['regmon_tx'] = tuple(np.array(c1[0:3]) / 256)
        matplotlib.colors.ColorConverter.colors['regmon_rx'] = tuple(np.array(c2[0:3]) / 256)
        matplotlib.colors.ColorConverter.colors['regmon_idle'] = tuple(np.array(c3[0:3]) / 256)
        matplotlib.colors.ColorConverter.colors['regmon_others'] = tuple(np.array(c4[0:3]) / 256)
        matplotlib.colors.ColorConverter.colors['regmon_fack'] = tuple(np.array(c5[0:3]) / 256)

        x_regemon = regmon_edat['ktime'] if np.any(regmon_edat['ktime']) else [np.nan]

        x_min_glob = np.uint64(np.nanmin([x_regemon[0]]))
        x_max_glob = np.uint64(np.nanmax([x_regemon[-1]]))

        fig = plt.figure(figsize=(20, 4))
        ax1 = plt.subplot(111, axisbg=(0.1843, 0.3098, 0.3098))
        # fig.patch.set_facecolor('grafana1')
        # RegMon
        ###############################################################################################
        ax = ax1
        ax.set_title('Atheros MAC State Distribution - RegMon')
        ax.set_ylabel('Relative Dwell Time [%]')

        max_samples = -1
        x = regmon_edat['ktime'][0:max_samples] - x_min_glob

        yl = np.zeros(len(x))
        y1 = regmon_edat['rel_tx'][0:max_samples]  # tx
        y2 = regmon_edat['rel_rx'][0:max_samples]  # rx
        y3 = regmon_edat['rel_idle'][0:max_samples]  # idle
        y4 = regmon_edat['rel_others'][0:max_samples]  # others
        y5 = regmon_edat['d_fack'][0:max_samples]  # ACK failures
        y5[y5 > 0] = y1[y5 > 0]

        print('Calculating RegMon results...')
        regmon_estats = {'rel_tx': {}, 'rel_rx': {}, 'rel_idle': {}, 'rel_others': {}, 'd_fack': {}}
        regmon_estats['rel_tx']['avg'] = np.nanmean(regmon_edat['rel_tx'])
        regmon_estats['rel_rx']['avg'] = np.nanmean(regmon_edat['rel_rx'])
        regmon_estats['rel_idle']['avg'] = np.nanmean(regmon_edat['rel_idle'])
        regmon_estats['rel_others']['avg'] = np.nanmean(regmon_edat['rel_others'])

        regmon_estats['d_fack']['avg'] = np.nanmean(regmon_edat['d_fack'])

        print('Mean TX dwell time: %.2f%%' % regmon_estats['rel_tx']['avg'])
        print('Mean RX dwell time: %.2f%%' % regmon_estats['rel_rx']['avg'])
        print('Mean IDLE dwell time: %.2f%%' % regmon_estats['rel_idle']['avg'])
        print('Mean OTHERS dwell time: %.2f%%' % regmon_estats['rel_others']['avg'])
        print('Mean d_fack: %.2f%%' % regmon_estats['d_fack']['avg'])

        regmon_Ts = 10 * 1e6
        width = regmon_Ts
        # ax.bar(x - width, y1, width, bottom=yl, color='regmon_tx', edgecolor='none', label='TX')
        # ax.bar(x - width, y2, width, bottom=yl+y1, color='regmon_rx', edgecolor='none', label='RX')
        # ax.bar(x - width, y3, width, bottom=yl+y1+y2, color='regmon_idle', edgecolor='none', label='IDLE')
        # ax.bar(x - width, y4, width, bottom=yl+y1+y2+y3, color='regmon_others', edgecolor='none', label='OTHERS')
        # ax.bar(x - width, y5, width, bottom=yl, color='regmon_fack', edgecolor='none', label='TX ACK FAIL')

        ax.bar(x, y1, width, bottom=yl, color='regmon_tx', edgecolor='none', label='TX')
        ax.bar(x, y2, width, bottom=yl + y1, color='regmon_rx', edgecolor='none', label='RX')
        ax.bar(x, y3, width, bottom=yl + y1 + y2, color='regmon_idle', edgecolor='none', label='IDLE')
        ax.bar(x, y4, width, bottom=yl + y1 + y2 + y3, color='regmon_others', edgecolor='none', label='OTHERS')
        ax.bar(x, y5, width, bottom=yl, color='regmon_fack', edgecolor='none', label='TX ACK FAIL')
        ax.xaxis.grid()
        ax.yaxis.grid()

        ####
        # ax.set_xlim(0, x_max_glob - x_min_glob)
        ax.set_ylim(0, max_samples / 2)

        xticklabels = (np.array(ax.get_xticks().tolist()) / 1e6).astype(np.uint64)
        ax.set_xticklabels(xticklabels)
        ax.set_ylim(0, 100)
        # text box
        ax_xmin, ax_xmax = ax.get_xlim()
        ax_ymin, ax_ymax = ax.get_ylim()
        stat_str = "TX Avg:           %05.2f%%\nRX Avg:           %05.2f%%\nIDLE Avg:        %05.2f%%\nOTHERS Avg:  %05.2f%%" % \
                   (regmon_estats['rel_tx']['avg'], regmon_estats['rel_rx']['avg'], regmon_estats['rel_idle']['avg'],
                    regmon_estats['rel_others']['avg'])
        ax.text(ax_xmax * 1.005, ax_ymax * 0.840, stat_str, size=12, rotation=0.0,
                ha="left", va="center",
                bbox=dict(boxstyle="round",
                          ec=(1., 0.5, 0.5),
                          fc=(1., 0.8, 0.8),
                          )
                )
        # legend
        objs1, labels1 = ax1.get_legend_handles_labels()
        fig.legend(objs1[::-1], labels1[::-1],
                   prop={'size': 12},
                   loc='upper center',
                   fancybox=True,
                   shadow=True,
                   ncol=6)

        plt.show()

### Config: meta data of experiment ###
class Config():
    def __init__(self):
        super().__init__()

    def load_config(self, fn):
        with open(fn, 'r') as fo:
            dat = json.load(fo)
        return dat

    def print(self, config_data):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(config_data)

# base folder
base_dir = '../traces/wiplus_dl_lte-fb_20161223/'

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
        #cfg.print(config_data)
        #sampling_interval = config_data['regmon']['sampling_interval']
        #print('sampling_interval %f' % sampling_interval)

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
    except Exception as ex:
        print('Failed to parse %s' % directory)
        pass
