import argparse
import csv
from lib import loader
from lib import filter_json
from lib import util
from lib import cell_helper
from lib import wifi_helper
import logging
import numpy as np
from pathlib import Path

max_lte = -1
max_nr = -1
max_wifi_2_4 = -1
max_wifi_5 = -1
max_wifi_6 = -1
output_list = list()


def cb_preprocess(obj):
    print(f"Processing... # of data: {len(obj['json'])}")

    sigcap = obj['json']
    options = obj['options']

    global max_lte, max_nr, max_wifi_2_4, max_wifi_5, max_wifi_6

    # If filter exist, filter the sigcap object
    if (options.filter is not None):
        sigcap = filter_json.filter_array(options.filter, sigcap)
        print(f"After filter, # of data: {len(sigcap)}")

    for entry in sigcap:
        # Get max LTE cells
        if (max_lte < len(entry['cell_info'])):
            max_lte = len(entry['cell_info'])

        # Get max NR cells
        if (max_nr < len(entry['nr_info'])):
            max_nr = len(entry['nr_info'])

        # Get max Wi-Fi APs
        wifi_2_4_count = 0
        wifi_5_count = 0
        wifi_6_count = 0
        for wifi_entry in entry['wifi_info']:
            if not wifi_entry["connected"]:
                match wifi_helper.get_freq_code(wifi_entry['primaryFreq']):
                    case "2.4":
                        wifi_2_4_count += 1
                    case "5":
                        wifi_5_count += 1
                    case "6":
                        wifi_6_count += 1
        if (max_wifi_2_4 < wifi_2_4_count):
            max_wifi_2_4 = wifi_2_4_count
        if (max_wifi_5 < wifi_5_count):
            max_wifi_5 = wifi_5_count
        if (max_wifi_6 < wifi_6_count):
            max_wifi_6 = wifi_6_count


def cb_process(obj):
    print(f"Processing... # of data: {len(obj['json'])}")
    if len(obj["files"]) < 10:
        print(f"Files: {','.join(obj['files'])}")

    sigcap = obj['json']
    options = obj['options']
    logging.info(options)

    global max_lte, max_nr, max_wifi_2_4, max_wifi_5, max_wifi_6, output_list

    # Compare maximum numbers with the requested maximum in the option
    if (options.max_lte is not None and options.max_lte < max_lte):
        max_lte = options.max_lte
    if (options.max_nr is not None and options.max_nr < max_nr):
        max_nr = options.max_nr
    if (options.max_wifi is not None and options.max_wifi < max_wifi_2_4):
        max_wifi_2_4 = options.max_wifi
    if (options.max_wifi is not None and options.max_wifi < max_wifi_5):
        max_wifi_5 = options.max_wifi
    if (options.max_wifi is not None and options.max_wifi < max_wifi_6):
        max_wifi_6 = options.max_wifi

    # If filter exist, filter the sigcap object
    if (options.filter is not None):
        sigcap = filter_json.filter_array(options.filter, sigcap)
        print(f"After filter, # of data: {len(sigcap)}")

    for entry in sigcap:
        if (
            not options.include_invalid_op
            and "opName" not in entry
            and "simName" not in entry
            and "carrierName" not in entry
        ):
            continue

        operator = util.get_operator_name(entry)
        if (not options.include_invalid_op and operator == "Unknown"):
            continue
        temp_out = {
            "sigcap_version": entry["version"],
            "android_version": entry["androidVersion"],
            "is_debug": entry["isDebug"],
            "uuid": entry["uuid"],
            "device_name": entry["deviceName"],
            "timestamp": entry["datetimeIso"],
            "latitude": entry["location"]["latitude"],
            "longitude": entry["location"]["longitude"],
            "altitude": entry["location"]["altitude"],
            "hor_acc": entry["location"]["hor_acc"],
            "ver_acc": entry["location"]["ver_acc"],
            "operator": operator,
            "network_type*": util.get_network_type(entry),
            "override_network_type": entry["overrideNetworkType"],
            "radio_type": entry["phoneType"],
            "nrStatus": entry["nrStatus"],
            "nrAvailable": entry["nrAvailable"],
            "dcNrRestricted": entry["dcNrRestricted"],
            "enDcAvailable": entry["enDcAvailable"],
            "nrFrequencyRange": entry["nrFrequencyRange"],
            "cellBandwidths": entry["cellBandwidths"],
            "usingCA": entry["usingCA"],
        }

        # Sensor
        if ("sensor" in entry and options.print_sensor_data):
            temp_out["sensor.deviceTempC"] = entry["sensor"]["deviceTempC"]
            temp_out["sensor.ambientTempC"] = entry["sensor"]["ambientTempC"]
            temp_out["sensor.accelXMs2"] = entry["sensor"]["accelXMs2"]
            temp_out["sensor.accelYMs2"] = entry["sensor"]["accelYMs2"]
            temp_out["sensor.accelZMs2"] = entry["sensor"]["accelZMs2"]
            temp_out["sensor.battPresent"] = entry["sensor"]["battPresent"]
            temp_out["sensor.battStatus"] = entry["sensor"]["battStatus"]
            temp_out["sensor.battTechnology"] = entry["sensor"][
                "battTechnology"]
            temp_out["sensor.battCapPerc"] = entry["sensor"]["battCapPerc"]
            temp_out["sensor.battTempC"] = entry["sensor"]["battTempC"]
            temp_out["sensor.battChargeUah"] = entry["sensor"]["battChargeUah"]
            temp_out["sensor.battVoltageMv"] = entry["sensor"]["battVoltageMv"]
            temp_out["sensor.battCurrNowUa"] = entry["sensor"]["battCurrNowUa"]
            temp_out["sensor.battCurrAveUa"] = entry["sensor"]["battCurrAveUa"]
            temp_out["sensor.battEnergyNwh"] = entry["sensor"]["battEnergyNwh"]

        # iperf
        if "iperf_info" in entry and len(entry["iperf_info"]) > 0:
            iperf_tputs = [val["tputMbps"] for val in entry["iperf_info"]]
            temp_out["iperf_tput_mean_mbps"] = np.mean(iperf_tputs)
            temp_out["iperf_tput_stddev_mbps"] = np.std(iperf_tputs)
            temp_out["iperf_target"] = next(
                (val["target"] for val in entry["iperf_info"]
                 if "target" in val and val["target"]),
                "N/A")
            temp_out["iperf_direction"] = next(
                (val["direction"] for val in entry["iperf_info"]
                 if "direction" in val and val["direction"]),
                "N/A")
            temp_out["iperf_protocol"] = next(
                (val["protocol"] for val in entry["iperf_info"]
                 if "protocol" in val and val["protocol"]),
                "N/A")
        else:
            temp_out["iperf_tput_mean_mbps"] = "NaN"
            temp_out["iperf_tput_stddev_mbps"] = "NaN"
            temp_out["iperf_target"] = "N/A"
            temp_out["iperf_direction"] = "N/A"
            temp_out["iperf_protocol"] = "N/A"

        # ping
        if "ping_info" in entry and len(entry["ping_info"]) > 0:
            ping_rtts = [val["time"] for val in entry["ping_info"]]
            temp_out["ping_rtt_mean_ms"] = np.mean(ping_rtts)
            temp_out["ping_rtt_stddev_ms"] = np.std(ping_rtts)
            temp_out["ping_target"] = next(
                (val["target"] for val in entry["ping_info"]
                 if "target" in val and val["target"]),
                "N/A")
        else:
            temp_out["ping_rtt_mean_ms"] = "NaN"
            temp_out["ping_rtt_stddev_ms"] = "NaN"
            temp_out["ping_target"] = "N/A"

        # HTTP
        if "http_info" in entry:
            temp_out["http_tput_mean_mbps"] = (
                (entry["http_info"]["bytesDownloaded"] * 8e3
                 / entry["http_info"]["durationNano"])
                if entry["http_info"]["durationNano"] > 0
                else "NaN")
            temp_out["http_target"] = (
                entry["http_info"]["targetUrl"]
                if ("targetUrl" in entry["http_info"]
                    and entry["http_info"]["targetUrl"])
                else "N/A")

        temp_out["lte_count"] = len(entry["cell_info"])

        # LTE primary
        lte_primary = next(
            (x for x in entry["cell_info"] if util.is_primary(x)), None)
        if lte_primary:
            temp_out["lte_primary_pci"] = util.clean_signal(lte_primary["pci"])
            temp_out["lte_primary_ci"] = util.clean_signal(lte_primary["ci"])
            temp_out["lte_primary_earfcn"] = util.clean_signal(
                lte_primary["earfcn"])
            temp_out["lte_primary_band*"] = cell_helper.earfcn_to_band(
                lte_primary["earfcn"])
            temp_out["lte_primary_freq_mhz*"] = cell_helper.earfcn_to_freq(
                lte_primary["earfcn"])
            temp_out["lte_primary_width_mhz"] = util.clean_signal(
                lte_primary["width"] / 1000)
            temp_out["lte_primary_rsrp_dbm"] = util.clean_signal(
                lte_primary["rsrp"])
            temp_out["lte_primary_rsrq_db"] = util.clean_signal(
                lte_primary["rsrq"])
            temp_out["lte_primary_cqi"] = util.clean_signal(
                lte_primary["cqi"])
            temp_out["lte_primary_rssi_dbm"] = util.clean_signal(
                lte_primary["rssi"])
            temp_out["lte_primary_rssnr_db"] = util.clean_signal(
                lte_primary["rssnr"])
            temp_out["lte_primary_timing"] = util.clean_signal(
                lte_primary["timing"])

            # Remove LTE primary
            entry["cell_info"] = [val for val in entry["cell_info"]
                                  if val != lte_primary]
        else:
            temp_out["lte_primary_pci"] = "NaN"
            temp_out["lte_primary_ci"] = "NaN"
            temp_out["lte_primary_earfcn"] = "NaN"
            temp_out["lte_primary_band*"] = "N/A"
            temp_out["lte_primary_freq_mhz*"] = "NaN"
            temp_out["lte_primary_width_mhz"] = "NaN"
            temp_out["lte_primary_rsrp_dbm"] = "NaN"
            temp_out["lte_primary_rsrq_db"] = "NaN"
            temp_out["lte_primary_cqi"] = "NaN"
            temp_out["lte_primary_rssi_dbm"] = "NaN"
            temp_out["lte_primary_rssnr_db"] = "NaN"
            temp_out["lte_primary_timing"] = "NaN"

        temp_out["nr_count"] = len(entry["nr_info"])

        # NR primary
        nr_primary = next(
            (x for x in entry["nr_info"] if util.is_primary(x)), None)
        if nr_primary is None and len(entry["nr_info"]) > 0:
            nr_primary = entry["nr_info"][0]
        if nr_primary:
            temp_out["nr_first_is_primary"] = (nr_primary["is_primary"]
                                               == "primary")
            temp_out["nr_first_is_signalStrAPI"] = nr_primary["isSignalStrAPI"]
            temp_out["nr_first_pci"] = util.clean_signal(
                nr_primary["nrPci"])
            temp_out["nr_first_nci"] = util.clean_signal(
                nr_primary["nci"])
            temp_out["nr_first_arfcn"] = util.clean_signal(
                nr_primary["nrarfcn"])
            temp_out["nr_first_band*"] = cell_helper.nrarfcn_to_band(
                nr_primary["nrarfcn"])
            temp_out["nr_first_freq_mhz*"] = cell_helper.nrarfcn_to_freq(
                nr_primary["nrarfcn"])
            temp_out["nr_first_ss_rsrp_dbm"] = util.clean_signal(
                nr_primary["ssRsrp"])
            temp_out["nr_first_ss_rsrq_db"] = util.clean_signal(
                nr_primary["ssRsrq"])
            temp_out["nr_first_ss_sinr_db"] = util.clean_signal(
                nr_primary["ssSinr"])
            temp_out["nr_first_csi_rsrp_dbm"] = util.clean_signal(
                nr_primary["csiRsrp"])
            temp_out["nr_first_csi_rsrq_db"] = util.clean_signal(
                nr_primary["csiRsrq"])
            temp_out["nr_first_csi_sinr_db"] = util.clean_signal(
                nr_primary["csiSinr"])

            # Remove NR primary
            entry["nr_info"] = [val for val in entry["nr_info"]
                                if val != nr_primary]
        else:
            temp_out["nr_first_is_primary"] = "N/A"
            temp_out["nr_first_is_signalStrAPI"] = "N/A"
            temp_out["nr_first_pci"] = "NaN"
            temp_out["nr_first_nci"] = "NaN"
            temp_out["nr_first_arfcn"] = "NaN"
            temp_out["nr_first_band*"] = "N/A"
            temp_out["nr_first_freq_mhz*"] = "NaN"
            temp_out["nr_first_ss_rsrp_dbm"] = "NaN"
            temp_out["nr_first_ss_rsrq_db"] = "NaN"
            temp_out["nr_first_ss_sinr_db"] = "NaN"
            temp_out["nr_first_csi_rsrp_dbm"] = "NaN"
            temp_out["nr_first_csi_rsrq_db"] = "NaN"
            temp_out["nr_first_csi_sinr_db"] = "NaN"

        # NR cells
        nr_cells = sorted(entry["nr_info"], key=lambda x: x["ssRsrp"])
        i = 1
        for cell in nr_cells:
            temp_out[f"nr_other{i}_pci"] = util.clean_signal(
                nr_primary["nrPci"])
            temp_out[f"nr_other{i}_arfcn"] = util.clean_signal(
                nr_primary["nrarfcn"])
            temp_out[f"nr_other{i}_band*"] = cell_helper.nrarfcn_to_band(
                nr_primary["nrarfcn"])
            temp_out[f"nr_other{i}_freq_mhz*"] = cell_helper.nrarfcn_to_freq(
                nr_primary["nrarfcn"])
            temp_out[f"nr_other{i}_ss_rsrp_dbm"] = util.clean_signal(
                nr_primary["ssRsrp"])
            temp_out[f"nr_other{i}_ss_rsrq_db"] = util.clean_signal(
                nr_primary["ssRsrq"])
            temp_out[f"nr_other{i}_csi_rsrp_dbm"] = util.clean_signal(
                nr_primary["csiRsrp"])
            temp_out[f"nr_other{i}_csi_rsrq_db"] = util.clean_signal(
                nr_primary["csiRsrq"])
            temp_out[f"nr_other{i}_is_signalStrAPI"] = nr_primary[
                "isSignalStrAPI"]
            i += 1
        while i < max_nr:
            temp_out[f"nr_other{i}_pci"] = "NaN"
            temp_out[f"nr_other{i}_arfcn"] = "NaN"
            temp_out[f"nr_other{i}_band*"] = "N/A"
            temp_out[f"nr_other{i}_freq_mhz*"] = "NaN"
            temp_out[f"nr_other{i}_ss_rsrp_dbm"] = "NaN"
            temp_out[f"nr_other{i}_ss_rsrq_db"] = "NaN"
            temp_out[f"nr_other{i}_csi_rsrp_dbm"] = "NaN"
            temp_out[f"nr_other{i}_csi_rsrq_db"] = "NaN"
            temp_out[f"nr_other{i}_is_signalStrAPI"] = "N/A"
            i += 1

        # LTE cells
        lte_cells = sorted(entry["cell_info"], key=lambda x: x["rsrp"])
        i = 1
        for cell in lte_cells:
            temp_out[f"lte_other{i}_pci"] = util.clean_signal(cell["pci"])
            temp_out[f"lte_other{i}_earfcn"] = util.clean_signal(
                cell["earfcn"])
            temp_out[f"lte_other{i}_band*"] = cell_helper.earfcn_to_band(
                cell["earfcn"])
            temp_out[f"lte_other{i}_freq_mhz*"] = cell_helper.earfcn_to_freq(
                cell["earfcn"])
            temp_out[f"lte_other{i}_rsrp_dbm"] = util.clean_signal(
                cell["rsrp"])
            temp_out[f"lte_other{i}_rsrq_db"] = util.clean_signal(
                cell["rsrq"])
            temp_out[f"lte_other{i}_rssi_dbm"] = util.clean_signal(
                cell["rssi"])
            i += 1
        while i < max_lte:
            temp_out[f"lte_other{i}_pci"] = "NaN"
            temp_out[f"lte_other{i}_earfcn"] = "NaN"
            temp_out[f"lte_other{i}_band*"] = "N/A"
            temp_out[f"lte_other{i}_freq_mhz*"] = "NaN"
            temp_out[f"lte_other{i}_rsrp_dbm"] = "NaN"
            temp_out[f"lte_other{i}_rsrq_db"] = "NaN"
            temp_out[f"lte_other{i}_rssi_dbm"] = "NaN"
            i += 1

        # Connected Wi-Fi
        wifi_conn = next(
            (val for val in entry["wifi_info"] if val["connected"]), None)
        if wifi_conn:
            temp_out["wifi_connected_ssid"] = wifi_conn["ssid"]
            temp_out["wifi_connected_bssid"] = wifi_conn["bssid"]
            temp_out["wifi_connected_primary_freq_mhz"] = wifi_conn[
                "primaryFreq"]
            temp_out["wifi_connected_center_freq_mhz"] = (
                wifi_conn["centerFreq1"] if wifi_conn["centerFreq1"] != 0
                else wifi_conn["centerFreq0"] if wifi_conn["centerFreq0"] != 0
                else wifi_conn["primaryFreq"])
            temp_out["wifi_connected_primary_ch*"] = (
                wifi_helper.get_channel_from_freq(wifi_conn["primaryFreq"], 20)
            )
            temp_out["wifi_connected_ch_num*"] = (
                wifi_helper.get_channel_from_freq(
                    wifi_conn["primaryFreq"], wifi_conn["width"])
                if wifi_conn["width"] > 0
                else temp_out["wifi_connected_primary_ch*"]
            )
            temp_out["wifi_connected_bw_mhz"] = (
                wifi_conn["width"] if wifi_conn["width"] > 0 else "NaN")
            temp_out["wifi_connected_rssi_dbm"] = util.clean_signal(
                wifi_conn["rssi"])
            temp_out["wifi_connected_standard"] = wifi_conn["standard"]
            temp_out["wifi_connected_tx_link_speed_mbps"] = wifi_conn[
                "txLinkSpeed"]
            temp_out["wifi_connected_rx_link_speed_mbps"] = wifi_conn[
                "rxLinkSpeed"]
            temp_out["wifi_connected_max_tx_link_speed_mbps"] = wifi_conn[
                "maxSupportedTxLinkSpeed"]
            temp_out["wifi_connected_max_rx_link_speed_mbps"] = wifi_conn[
                "maxSupportedRxLinkSpeed"]
        else:
            temp_out["wifi_connected_ssid"] = "N/A"
            temp_out["wifi_connected_bssid"] = "N/A"
            temp_out["wifi_connected_primary_freq_mhz"] = "NaN"
            temp_out["wifi_connected_center_freq_mhz"] = "NaN"
            temp_out["wifi_connected_primary_ch*"] = "NaN"
            temp_out["wifi_connected_ch_num*"] = "NaN"
            temp_out["wifi_connected_bw_mhz"] = "NaN"
            temp_out["wifi_connected_rssi_dbm"] = "NaN"
            temp_out["wifi_connected_standard"] = "N/A"
            temp_out["wifi_connected_tx_link_speed_mbps"] = "NaN"
            temp_out["wifi_connected_rx_link_speed_mbps"] = "NaN"
            temp_out["wifi_connected_max_tx_link_speed_mbps"] = "NaN"
            temp_out["wifi_connected_max_rx_link_speed_mbps"] = "NaN"

        # Wi-Fi other 2.4 GHz
        wifi_2_4 = [val for val in entry["wifi_info"]
                    if not val["connected"] and val["primaryFreq"] < 5000]
        temp_out["wifi_2.4_other_count"] = len(wifi_2_4)
        rssi_2_4 = np.array([val["rssi"] for val in wifi_2_4])
        logging.debug(f"RSSI 2.4 len: {len(rssi_2_4)}")
        if len(rssi_2_4) > 0:
            temp_out["wifi_2.4_other_mean_rssi_dbm"] = util.mw_to_dbm(
                np.mean(util.dbm_to_mw(rssi_2_4)))
            stddev_mw = np.std(util.dbm_to_mw(rssi_2_4))
            if stddev_mw != 0:
                temp_out["wifi_2.4_other_stddev_rssi_db"] = util.mw_to_dbm(
                    stddev_mw)
            else:
                temp_out["wifi_2.4_other_stddev_rssi_db"] = "NaN"
        else:
            temp_out["wifi_2.4_other_mean_rssi_dbm"] = "NaN"
            temp_out["wifi_2.4_other_stddev_rssi_db"] = "NaN"
        i = 1
        for cell in wifi_2_4:
            temp_out[f"wifi_2.4_other{i}_ssid"] = cell["ssid"]
            temp_out[f"wifi_2.4_other{i}_bssid"] = cell["bssid"]
            temp_out[f"wifi_2.4_other{i}_primary_freq_mhz"] = cell[
                "primaryFreq"]
            temp_out[f"wifi_2.4_other{i}_center_freq_mhz"] = (
                cell["centerFreq1"] if cell["centerFreq1"] != 0
                else cell["centerFreq0"] if cell["centerFreq0"] != 0
                else cell["primaryFreq"])
            temp_out[f"wifi_2.4_other{i}_primary_ch*"] = (
                wifi_helper.get_channel_from_freq(cell["primaryFreq"], 20)
            )
            temp_out[f"wifi_2.4_other{i}_ch_num*"] = (
                wifi_helper.get_channel_from_freq(
                    cell["primaryFreq"], cell["width"])
                if cell["width"] > 0
                else temp_out[f"wifi_2.4_other{i}_primary_ch*"]
            )
            temp_out[f"wifi_2.4_other{i}_bw_mhz"] = (
                cell["width"] if cell["width"] > 0 else "NaN")
            temp_out[f"wifi_2.4_other{i}_rssi_dbm"] = util.clean_signal(
                cell["rssi"])
            temp_out[f"wifi_2.4_other{i}_standard"] = cell["standard"]
            i += 1
        while i <= max_wifi_2_4:
            temp_out[f"wifi_2.4_other{i}_ssid"] = "N/A"
            temp_out[f"wifi_2.4_other{i}_bssid"] = "N/A"
            temp_out[f"wifi_2.4_other{i}_primary_freq_mhz"] = "NaN"
            temp_out[f"wifi_2.4_other{i}_center_freq_mhz"] = "NaN"
            temp_out[f"wifi_2.4_other{i}_primary_ch*"] = "NaN"
            temp_out[f"wifi_2.4_other{i}_ch_num*"] = "NaN"
            temp_out[f"wifi_2.4_other{i}_bw_mhz"] = "NaN"
            temp_out[f"wifi_2.4_other{i}_rssi_dbm"] = "NaN"
            temp_out[f"wifi_2.4_other{i}_standard"] = "N/A"
            i += 1

        # Wi-Fi other 5 GHz
        wifi_5 = [val for val in entry["wifi_info"]
                  if not val["connected"] and val["primaryFreq"] >= 5000
                  and val["primaryFreq"] < 5925]
        temp_out["wifi_5_other_count"] = len(wifi_5)
        rssi_5 = np.array([val["rssi"] for val in wifi_5])
        logging.debug(f"RSSI 2.4 len: {len(rssi_5)}")
        if len(rssi_5) > 0:
            temp_out["wifi_5_other_mean_rssi_dbm"] = util.mw_to_dbm(
                np.mean(util.dbm_to_mw(rssi_5)))
            stddev_mw = np.std(util.dbm_to_mw(rssi_5))
            if stddev_mw != 0:
                temp_out["wifi_5_other_stddev_rssi_db"] = util.mw_to_dbm(
                    stddev_mw)
            else:
                temp_out["wifi_5_other_stddev_rssi_db"] = "NaN"
        else:
            temp_out["wifi_5_other_mean_rssi_dbm"] = "NaN"
            temp_out["wifi_5_other_stddev_rssi_db"] = "NaN"
        i = 1
        for cell in wifi_5:
            temp_out[f"wifi_5_other{i}_ssid"] = cell["ssid"]
            temp_out[f"wifi_5_other{i}_bssid"] = cell["bssid"]
            temp_out[f"wifi_5_other{i}_primary_freq_mhz"] = cell[
                "primaryFreq"]
            temp_out[f"wifi_5_other{i}_center_freq_mhz"] = (
                cell["centerFreq1"] if cell["centerFreq1"] != 0
                else cell["centerFreq0"] if cell["centerFreq0"] != 0
                else cell["primaryFreq"])
            temp_out[f"wifi_5_other{i}_primary_ch*"] = (
                wifi_helper.get_channel_from_freq(cell["primaryFreq"], 20)
            )
            temp_out[f"wifi_5_other{i}_ch_num*"] = (
                wifi_helper.get_channel_from_freq(
                    cell["primaryFreq"], cell["width"])
                if cell["width"] > 0
                else temp_out[f"wifi_5_other{i}_primary_ch*"]
            )
            temp_out[f"wifi_5_other{i}_bw_mhz"] = (
                cell["width"] if cell["width"] > 0 else "NaN")
            temp_out[f"wifi_5_other{i}_rssi_dbm"] = util.clean_signal(
                cell["rssi"])
            temp_out[f"wifi_5_other{i}_standard"] = cell["standard"]
            i += 1
        while i <= max_wifi_5:
            temp_out[f"wifi_5_other{i}_ssid"] = "N/A"
            temp_out[f"wifi_5_other{i}_bssid"] = "N/A"
            temp_out[f"wifi_5_other{i}_primary_freq_mhz"] = "NaN"
            temp_out[f"wifi_5_other{i}_center_freq_mhz"] = "NaN"
            temp_out[f"wifi_5_other{i}_primary_ch*"] = "NaN"
            temp_out[f"wifi_5_other{i}_ch_num*"] = "NaN"
            temp_out[f"wifi_5_other{i}_bw_mhz"] = "NaN"
            temp_out[f"wifi_5_other{i}_rssi_dbm"] = "NaN"
            temp_out[f"wifi_5_other{i}_standard"] = "N/A"
            i += 1

        # Wi-Fi other 6 GHz
        wifi_6 = [val for val in entry["wifi_info"]
                  if not val["connected"] and val["primaryFreq"] >= 5925]
        temp_out["wifi_6_other_count"] = len(wifi_6)
        rssi_6 = np.array([val["rssi"] for val in wifi_6])
        logging.debug(f"RSSI 2.4 len: {len(rssi_6)}")
        if len(rssi_6) > 0:
            temp_out["wifi_6_other_mean_rssi_dbm"] = util.mw_to_dbm(
                np.mean(util.dbm_to_mw(rssi_6)))
            stddev_mw = np.std(util.dbm_to_mw(rssi_6))
            if stddev_mw != 0:
                temp_out["wifi_6_other_stddev_rssi_db"] = util.mw_to_dbm(
                    stddev_mw)
            else:
                temp_out["wifi_6_other_stddev_rssi_db"] = "NaN"
        else:
            temp_out["wifi_6_other_mean_rssi_dbm"] = "NaN"
            temp_out["wifi_6_other_stddev_rssi_db"] = "NaN"
        i = 1
        for cell in wifi_6:
            temp_out[f"wifi_6_other{i}_ssid"] = cell["ssid"]
            temp_out[f"wifi_6_other{i}_bssid"] = cell["bssid"]
            temp_out[f"wifi_6_other{i}_primary_freq_mhz"] = cell[
                "primaryFreq"]
            temp_out[f"wifi_6_other{i}_center_freq_mhz"] = (
                cell["centerFreq1"] if cell["centerFreq1"] != 0
                else cell["centerFreq0"] if cell["centerFreq0"] != 0
                else cell["primaryFreq"])
            temp_out[f"wifi_6_other{i}_primary_ch*"] = (
                wifi_helper.get_channel_from_freq(cell["primaryFreq"], 20)
            )
            temp_out[f"wifi_6_other{i}_ch_num*"] = (
                wifi_helper.get_channel_from_freq(
                    cell["primaryFreq"], cell["width"])
                if cell["width"] > 0
                else temp_out[f"wifi_6_other{i}_primary_ch*"]
            )
            temp_out[f"wifi_6_other{i}_bw_mhz"] = (
                cell["width"] if cell["width"] > 0 else "NaN")
            temp_out[f"wifi_6_other{i}_rssi_dbm"] = util.clean_signal(
                cell["rssi"])
            temp_out[f"wifi_6_other{i}_standard"] = cell["standard"]
            i += 1
        while i <= max_wifi_6:
            temp_out[f"wifi_6_other{i}_ssid"] = "N/A"
            temp_out[f"wifi_6_other{i}_bssid"] = "N/A"
            temp_out[f"wifi_6_other{i}_primary_freq_mhz"] = "NaN"
            temp_out[f"wifi_6_other{i}_center_freq_mhz"] = "NaN"
            temp_out[f"wifi_6_other{i}_primary_ch*"] = "NaN"
            temp_out[f"wifi_6_other{i}_ch_num*"] = "NaN"
            temp_out[f"wifi_6_other{i}_bw_mhz"] = "NaN"
            temp_out[f"wifi_6_other{i}_rssi_dbm"] = "NaN"
            temp_out[f"wifi_6_other{i}_standard"] = "N/A"
            i += 1

        logging.debug(temp_out)
        output_list.append(temp_out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path,
                        help="input SigCap folder or file")
    parser.add_argument("output_file", type=argparse.FileType('w'),
                        help="output CSV file with .csv suffix")
    parser.add_argument("--max-lte", type=int,
                        help="maximum number of LTE cells to be displayed")
    parser.add_argument("--max-nr", type=int,
                        help="maximum number of NR cells to be displayed")
    parser.add_argument("--max-wifi", type=int,
                        help="maximum number of Wi-Fi APs to be displayed")
    parser.add_argument("--filter", type=str,
                        help="filter of JSON string or path to JSON file")
    parser.add_argument("--include-invalid-op", action="store_true",
                        help="include invalid operator names")
    parser.add_argument("--print-sensor-data", action="store_true",
                        help="print out sensor data")
    parser.add_argument("--log-level", default="warning",
                        help="Log level, default=warning")
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level.upper())

    if (args.filter is not None):
        args.filter = util.create_json_filter(args.filter)
        print(f"Using filter: {args.filter}")

    print("===== Start preprocessing! =====")
    loader.load_json(args.input, cb_preprocess, options=args)

    print("Preprocessing finished!")
    print(f"Max number of LTE cells: {max_lte}")
    print(f"Max number of NR cells: {max_nr}")
    print(f"Max number of Wi-Fi 2.4 GHz: {max_wifi_2_4}")
    print(f"Max number of Wi-Fi 5 GHz: {max_wifi_5}")
    print(f"Max number of Wi-Fi 6 GHz: {max_wifi_6}")

    global output_list

    print("\n===== Start processing! =====")
    loader.load_json(args.input, cb_process, options=args)
    output_list = sorted(output_list, key=lambda x: x["timestamp"])
    logging.info(f"Len output_list {len(output_list)}")

    if len(output_list) > 0:
        print(f"Writing to {args.output_file.name} ...")
        logging.debug(f"Header list: {','.join(output_list[0].keys())}")
        csv_writer = csv.DictWriter(
            args.output_file,
            fieldnames=output_list[0].keys())
        csv_writer.writeheader()
        csv_writer.writerows(output_list)

        print(f"DONE!")
    else:
        print("Empty data! Nothing to write.")


if __name__ == "__main__":
    main()
