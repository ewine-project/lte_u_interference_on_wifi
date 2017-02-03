Impact of LTE-U on WiFi
============================

Cellular network operators like Verizon are starting to offload data traffic in unlicensed 5 GHz ISM spectrum using
LTE Unlicensed (LTE-U). However, this part of the radio spectrum is also used by IEEE 802.11 standards, e.g. 802.11a/ac/ax.
Multiple studies have been carried out to identify the effects of LTE-U on WiFi. In particular, Jindal et al.
showed, as LTE-U duty-cycling does not implement listen before talk mechanisms (LBT), it can under some conditions
even disproportionately reduce WiFi throughput performance. Moreover, interference from LTE-U with moderate power can 
be even more harmful to WiFi than high-power interference.

To be able to cope with this impact and its effects, an approach that fist, enables Wi-Fi to detect the LTE-U
interference and second, enables to quantify the effective available medium airtime of each link (downlink and uplink)
during runtime, is needed. Afterwards, this knowledge enables to apply rapid interference management techniques such as
assignment of radio channels to WiFi APs. Furthermore, information about the exact timings of the LTE-U ON and OFF phases allows to apply techniques like
interference-aware packet scheduling, i.e. transmission during LTE-U OFF phases, and adaptive channel bonding, i.e. using
secondary channel during LTE-U OFF phases only.

The task is to achieve the aforementioned using information available at the MAC layer in a passive approach.

## Experiment setup

Our system model is shown below. Here we have a WiFi BSS consisting of a single AP serving a single client station. 
In addition there is a co-located LTE-U BS operating in the DL using the same unlicensed radio spectrum as the WiFi
BSS.

![system model](system_model_lteu_detailed.png)

## Traces:

We analyzed the impact of LTE-U BS signal on WiFi communication for different configurations, i.e. LTE-U signal strengths 
and duty-cycles. 

Two measurement campaigns have been performed:

wiplus_dl_lte-fb_20161223

- LTE with backlogged trafﬁc ,i.e. a full buffer traffic model is used.

wiplus_dl_lte-vb-rnd9_2016122

- Variable LTE-U traffic: The setup is as in previous experiment with a ﬁxed duty cycle of 33% but
with variable buffer trafﬁc model, i.e. the LTE-U ON phase was loaded uniform random between 30 % and 100 % which
corresponds to an effective LTE-U duty cycle of 16%.

The measurements of each parameter settings, i.e. different interfering LTE-U signal strengths and duty-cycles, is contained in a folder. 

Each folder contains the following four files:

config.json

- additional parameter settings encoded in JSON, example is given below

iometer.pklz

- TBD.

iperf3.pklz

- UDP downlink throughput measured at the WiFi AP
- Note: the normalized UDP throughput of the WiFi link under LTE-U interference, relative to the non-interfered WiFi link, corresponds
to the effective available medium airtime for the WiFi link. This is the ground truth to be predicted using MAC layer information at the WiFi AP side only (see below). 

regmon.pklz

- Information available at the MAC layer (at WiFi AP). The data was captured using the RegMon tool; see [regmon](https://github.com/thuehn/RegMon) website for more information.

## Scripts:

See tools/read_trace.py

	cd tools
	python3 read_trace.py

The meta data of a particular run can be obtained by calling:

    config_data = cfg.load_config(fname)
    meta_data = cfg.get_meta_data_from_fname(config_data['common']['meas_name'])

Here is an example for the return values.

The first is a json object:

    {   'common': {   'data_dir': '/measurements/wiplus_dl_lte-fb_20161223',
                      'meas_name': 'wifi=11a-5240mhz-15dbm-noani-siso_L2Probe=False_ICMPProbe=False_IPerf=udp-90M-dl=True_lteu=64qam_duty50-on80ms-off80ms-9dbm_RMres=0.50_runt=30',
                      'runtime': 30,
                      'update_interval': 1000.0},
        'icmp': {   'cpu_use': 2,
                    'destination': '192.168.2.2',
                    'enable': False,
                    'interval': 1,
                    'packet_size': 0},
        'iometer': {   'cpu_use': 0,
                       'iface': 'ath0',
                       'result_file': 'iometer.pklz',
                       'sampling_interval': 100.0},
        'iperf3': {   'bandwidth': '90M',
                      'cpu_use': 2,
                      'downlink': True,
                      'enable': True,
                      'result_file': 'iperf3.pklz',
                      'sampling_interval': 100.0,
                      'server': '192.168.2.2'},
        'l2probe': {   'cpu_use': 0,
                       'destination': '64:66:b3:6f:8d:42',
                       'enable': False,
                       'iface': 'mon0',
                       'interval': 1},
        'regmon': {   'cpu_use': 1,
                      'iface': 'ath0',
                      'result_file': 'regmon.pklz',
                      'sampling_interval': 0.5},
        'tcpdump': {'cpu_use': 3, 'iface': 'mon1', 'result_file': 'tcpdump.pcap'}}

Here we see configurations for e.g. Iperf and regmon. The sampling_interval is in milliseconds.

Whereas the second a Python dictionary:

    {   'ICMPProbe': ['False'],
        'IPerf': ['udp', '90M', 'dl', 'True'],
        'L2Probe': ['False'],
        'RMres': ['0.50'],
        'lteu': ['64qam', 'duty50', 'on80ms', 'off80ms', '9dbm'],
        'runt': ['30'],
        'wifi': ['11a', '5240mhz', '15dbm', 'noani', 'siso']}

Here IPerf was using UDP with bitrate of 90M in downlink.
The LTE-U configuration was 64QAM, duty cycle of 50% with a CSAT cycle length of 80+80=160ms, with ON phase of 80ms and LTE-U tx power of 9dBm.
The WiFi configuration was 802.11a, channel 48 (5240MHz), Tx power of 15 dBm, SISO and Atheros ANI disabled.

## Detectors:

A simple energy-based detector is provided; see tools/ed_detector.py