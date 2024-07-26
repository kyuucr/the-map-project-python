import argparse
import csv
from datetime import datetime, timedelta
from lib import loader
from lib import filter_json
from lib import util
from lib import wifi_helper
import logging
from pathlib import Path

output_list = list()
device_timedata = dict()


def cb_process(obj):
    print(f"Processing... # of data: {len(obj['json'])}")
    if len(obj["files"]) < 10:
        print(f"Files: {','.join(obj['files'])}")

    sigcap = obj['json']
    options = obj['options']
    logging.info(options)
    global output_list, device_timedata

    # If filter exist, filter the sigcap object
    if (options.filter is not None):
        sigcap = filter_json.filter_array(options.filter, sigcap)
        print(f"After filter, # of data: {len(sigcap)}")

    for entry in sigcap:
        if entry["uuid"] not in device_timedata:
            device_timedata[entry["uuid"]] = list()

        overview_dict = {
            "sigcap_version": entry["version"],
            "android_version": entry["androidVersion"],
            "is_debug": entry["isDebug"],
            "uuid": entry["uuid"],
            "device_name": entry["deviceName"],
            "latitude": entry["location"]["latitude"],
            "longitude": entry["location"]["longitude"],
            "altitude": entry["location"]["altitude"],
            "hor_acc": entry["location"]["hor_acc"],
            "ver_acc": entry["location"]["ver_acc"],
        }
        timestamp = datetime.fromisoformat(entry["datetimeIso"])

        for wifi_entry in entry["wifi_info"]:
            freq_code = wifi_helper.get_freq_code(wifi_entry["primaryFreq"])
            if ((getattr(options, "skip_2.4ghz") and freq_code == "2.4")
                    or (options.skip_5ghz and freq_code == "5")
                    or (options.skip_6ghz and freq_code == "6")):
                continue

            timedelta_ms = timedelta(
                milliseconds=wifi_entry["timestampDeltaMs"])
            actual_timestamp = timestamp - timedelta_ms
            if actual_timestamp.timestamp() in device_timedata[entry["uuid"]]:
                continue

            device_timedata[entry["uuid"]].append(actual_timestamp.timestamp())
            temp_out = overview_dict.copy()
            temp_out["timestamp"] = actual_timestamp.isoformat()
            temp_out["ssid"] = wifi_entry["ssid"]
            temp_out["bssid"] = wifi_entry["bssid"]
            temp_out["primary_freq_mhz"] = wifi_entry["primaryFreq"]
            temp_out["center_freq_mhz"] = (
                wifi_entry["centerFreq0"] if wifi_entry["centerFreq1"] == 0
                else wifi_entry["centerFreq1"])
            temp_out["width_mhz"] = wifi_entry["width"]
            temp_out["channel_num"] = wifi_helper.get_channel_from_freq(
                wifi_entry["primaryFreq"], wifi_entry["width"])
            temp_out["primary_ch_num"] = wifi_helper.get_channel_from_freq(
                wifi_entry["primaryFreq"], 20)
            temp_out["rssi_dbm"] = util.clean_signal(
                wifi_entry["rssi"])
            temp_out["standard"] = wifi_entry["standard"]
            temp_out["connected"] = wifi_entry["connected"]
            temp_out["link_speed"] = util.clean_signal(
                wifi_entry["linkSpeed"])
            temp_out["tx_link_speed"] = util.clean_signal(
                wifi_entry["txLinkSpeed"])
            temp_out["rx_link_speed"] = util.clean_signal(
                wifi_entry["rxLinkSpeed"])
            temp_out["max_supported_tx_link_speed"] = util.clean_signal(
                wifi_entry["maxSupportedTxLinkSpeed"])
            temp_out["max_supported_rx_link_speed"] = util.clean_signal(
                wifi_entry["maxSupportedRxLinkSpeed"])
            temp_out["capabilities"] = wifi_entry["capabilities"]
            temp_out["sta_count"] = util.clean_signal(wifi_entry["staCount"])
            if temp_out["sta_count"] == -1:
                temp_out["sta_count"] = "NaN"
            temp_out["ch_util"] = util.clean_signal(wifi_entry["chUtil"])
            if temp_out["ch_util"] == -1:
                temp_out["ch_util"] = "NaN"
            temp_out["tx_power_dbm"] = util.clean_signal(wifi_entry["txPower"])
            temp_out["link_margin_db"] = util.clean_signal(
                wifi_entry["linkMargin"])
            temp_out["aruba_ap_name"] = (wifi_entry["apName"]
                                         if ("apName" in wifi_entry
                                             and wifi_entry["apName"])
                                         else "unknown")

            output_list.append(temp_out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path,
                        help="input SigCap folder or file")
    parser.add_argument("output_file", type=argparse.FileType('w'),
                        help="output CSV file with .csv suffix")
    parser.add_argument("--filter", type=str,
                        help="filter of JSON string or path to JSON file")
    parser.add_argument("--skip-2.4ghz", action="store_true",
                        help="Skip 2.4 GHz Wi-Fi APs")
    parser.add_argument("--skip-5ghz", action="store_true",
                        help="Skip 2.4 GHz Wi-Fi APs")
    parser.add_argument("--skip-6ghz", action="store_true",
                        help="Skip 2.4 GHz Wi-Fi APs")
    parser.add_argument("--log-level", default="warning",
                        help="Log level, default=warning")
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level.upper())

    if (args.filter is not None):
        args.filter = util.create_json_filter(args.filter)
        print(f"Using filter: {args.filter}")

    global output_list

    print("===== Start processing! =====")
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
