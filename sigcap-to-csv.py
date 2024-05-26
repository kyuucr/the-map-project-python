import argparse
import csv
from lib import loader
from lib import filter_json
from lib import util
from lib import cell_helper
from lib import wifi_helper
import logging
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
            match wifi_helper.get_wifi_freq_code(wifi_entry['primaryFreq']):
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

    if len(output_list) > 0:
        print(f"Writing to {args.output_file.name} ...")
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
