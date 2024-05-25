import argparse
import csv
from lib import loader
from lib import filter_json
from lib import util
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
        if ("sensor" in entry and options.print_sensor_data):
            for key, val in entry["sensor"].items():
                temp_out[f"sensor.{key}"] = val

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

    print(f"Writing to {args.output_file.name} ...")
    fieldnames = [
        "sigcap_version",
        "android_version",
        "is_debug",
        "uuid",
        "device_name",
        "timestamp",
        "latitude",
        "longitude",
        "altitude",
        "hor_acc",
        "ver_acc",
        "operator",
        "network_type*",
        "override_network_type",
        "radio_type",
        "nrStatus",
        "nrAvailable",
        "dcNrRestricted",
        "enDcAvailable",
        "nrFrequencyRange",
        "cellBandwidths",
        "usingCA",
    ]
    if (args.print_sensor_data):
        fieldnames += [
            "sensor.deviceTempC",
            "sensor.ambientTempC",
            "sensor.accelXMs2",
            "sensor.accelYMs2",
            "sensor.accelZMs2",
            "sensor.battPresent",
            "sensor.battStatus",
            "sensor.battTechnology",
            "sensor.battCapPerc",
            "sensor.battTempC",
            "sensor.battChargeUah",
            "sensor.battVoltageMv",
            "sensor.battCurrNowUa",
            "sensor.battCurrAveUa",
            "sensor.battEnergyNwh"
        ]
    csv_writer = csv.DictWriter(
        args.output_file,
        fieldnames=fieldnames)
    csv_writer.writeheader()
    csv_writer.writerows(output_list)

    print(f"DONE!")


if __name__ == "__main__":
    main()
