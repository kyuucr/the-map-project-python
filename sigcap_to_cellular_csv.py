import argparse
import csv
from lib import loader
from lib import filter_json
from lib import util
from lib import cell_helper
import logging
from pathlib import Path

output_list = list()


def cb_process(obj):
    print(f"Processing... # of data: {len(obj['json'])}")
    if len(obj["files"]) < 10:
        print(f"Files: {','.join(obj['files'])}")

    sigcap = obj['json']
    options = obj['options']
    logging.info(options)
    global output_list

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
        overview_dict = {
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

        # LTE primary
        lte_primary = next(
            (x for x in entry["cell_info"] if util.is_primary(x)), None)
        if lte_primary:
            temp_out = overview_dict.copy()
            temp_out["lte/nr"] = "lte"
            temp_out["pci"] = util.clean_signal(lte_primary["pci"])
            temp_out["lte-ci/nr-nci"] = util.clean_signal(lte_primary["ci"])
            temp_out["lte-earfcn/nr-arfcn"] = util.clean_signal(
                lte_primary["earfcn"])
            temp_out["band*"] = cell_helper.earfcn_to_band(
                temp_out["lte-earfcn/nr-arfcn"])
            temp_out["freq_mhz*"] = cell_helper.earfcn_to_freq(
                temp_out["lte-earfcn/nr-arfcn"])
            temp_out["width_mhz"] = util.clean_signal(lte_primary["width"])
            temp_out["rsrp_dbm"] = util.clean_signal(lte_primary["rsrp"])
            temp_out["rsrq_db"] = util.clean_signal(lte_primary["rsrq"])
            temp_out["lte-rssi/nr-sinr_dbm"] = util.clean_signal(
                lte_primary["rssi"])
            temp_out["primary/other*"] = "primary"
            output_list.append(temp_out)

        # NR
        for nr_entry in entry["nr_info"]:
            temp_out = overview_dict.copy()
            temp_out["lte/nr"] = (
                "nr-SignalStrAPI" if nr_entry["isSignalStrAPI"] else "nr")
            temp_out["pci"] = util.clean_signal(nr_entry["nrPci"])
            temp_out["lte-ci/nr-nci"] = util.clean_signal(nr_entry["nci"])
            temp_out["lte-earfcn/nr-arfcn"] = util.clean_signal(
                nr_entry["nrarfcn"])
            temp_out["band*"] = cell_helper.nrarfcn_to_band(
                temp_out["lte-earfcn/nr-arfcn"],
                reg=cell_helper.REGION[options.region])
            temp_out["freq_mhz*"] = cell_helper.nrarfcn_to_freq(
                temp_out["lte-earfcn/nr-arfcn"])
            temp_out["width_mhz"] = "NaN"
            temp_out["rsrp_dbm"] = util.clean_signal(nr_entry["ssRsrp"])
            temp_out["rsrq_db"] = util.clean_signal(nr_entry["ssRsrq"])
            temp_out["lte-rssi/nr-sinr_dbm"] = util.clean_signal(
                nr_entry["ssSinr"])
            temp_out["primary/other*"] = (
                "primary" if nr_entry["status"] == "primary" else "other")
            output_list.append(temp_out)

        # Rest of LTE
        lte_others = [val for val in entry["cell_info"] if val != lte_primary]
        for lte_entry in lte_others:
            temp_out = overview_dict.copy()
            temp_out["lte/nr"] = "lte"
            temp_out["pci"] = util.clean_signal(lte_primary["pci"])
            temp_out["lte-ci/nr-nci"] = util.clean_signal(lte_primary["ci"])
            temp_out["lte-earfcn/nr-arfcn"] = util.clean_signal(
                lte_primary["earfcn"])
            temp_out["band*"] = cell_helper.earfcn_to_band(
                temp_out["lte-earfcn/nr-arfcn"])
            temp_out["freq_mhz*"] = cell_helper.earfcn_to_freq(
                temp_out["lte-earfcn/nr-arfcn"])
            temp_out["width_mhz"] = util.clean_signal(lte_primary["width"])
            temp_out["rsrp_dbm"] = util.clean_signal(lte_primary["rsrp"])
            temp_out["rsrq_db"] = util.clean_signal(lte_primary["rsrq"])
            temp_out["lte-rssi/nr-sinr_dbm"] = util.clean_signal(
                lte_primary["rssi"])
            temp_out["primary/other*"] = "other"
            output_list.append(temp_out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path,
                        help="input SigCap folder or file")
    parser.add_argument("output_file", type=argparse.FileType('w'),
                        help="output CSV file with .csv suffix")
    parser.add_argument("--filter", type=str,
                        help="filter of JSON string or path to JSON file")
    parser.add_argument("--region", choices=cell_helper.REGION.keys(),
                        default="NAR",
                        help="Region for NR band conversion, default=NAR")
    parser.add_argument("--include-invalid-op", action="store_true",
                        help="include invalid operator names")
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
