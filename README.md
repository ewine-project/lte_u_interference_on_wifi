Impact of LTE-U on WiFi
============================

## Experiment setup

The set-up is shown here:

![system model](system_model_lteu_detailed.png)

## Traces:

The following data was collected during the experiment for different interfering LTE-U signal strengths and LTE-U duty-cycles:

1. RegMon data collected at the WiFi AP:
See [regmon](https://github.com/thuehn/RegMon) website for more information.

2. iperf data (UDP DL throughput) collected at the WiFi AP.

The normalized UDP throughput of the WiFi link under LTE-U interference, relative to the non-interfered WiFi link, corresponds
to the effective available medium airtime for the WiFi link.

## Scripts:

See tools/read_trace.py

	cd tools
	python3 read_trace.py
