from argparse import ArgumentParser
from lib import loader
from lib import filter_json
from lib import util
from lib import wifi_helper

max_lte = -1
max_nr = -1
max_wifi_2_4 = -1
max_wifi_5 = -1
max_wifi_6 = -1


def cb_preprocess(obj):
    print(f"Preprocessing... # of data: {len(obj['json'])}; \
files: {','.join(obj['files'])}")

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
    print(f"Processing... # of data: {len(obj['json'])}; \
files: {','.join(obj['files'])}")

    sigcap = obj['json']
    options = obj['options']
    print(options)

    global max_lte, max_nr, max_wifi_2_4, max_wifi_5, max_wifi_6

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
        # print(entry)


def main():
    parser = ArgumentParser()
    parser.add_argument("input", help="input SigCap folder or file")
    parser.add_argument("output", help="output CSV file with .csv suffix")
    parser.add_argument("--max-lte", type=int,
                        help="maximum number of LTE cells to be displayed")
    parser.add_argument("--max-nr", type=int,
                        help="maximum number of NR cells to be displayed")
    parser.add_argument("--max-wifi", type=int,
                        help="maximum number of Wi-Fi APs to be displayed")
    parser.add_argument("--filter", type=str,
                        help="filter of JSON string or path to JSON file")
    parser.add_argument("--include-invalid-op",
                        help="include invalid operator names")
    parser.add_argument("--print-sensor-data", help="print out sensor data")
    parser.add_argument("--print-ping", help="print out ping data")
    parser.add_argument("--print-html-get", help="print out HTML GET data")
    args = parser.parse_args()

    if (args.filter is not None):
        args.filter = util.create_json_filter(args.filter)

    print("===== Start preprocessing! =====")
    loader.load_json(args.input, cb_preprocess, options=args)

    print("Preprocessing finished!")
    print(f"Max number of LTE cells: {max_lte}")
    print(f"Max number of NR cells: {max_nr}")
    print(f"Max number of Wi-Fi 2.4 GHz: {max_wifi_2_4}")
    print(f"Max number of Wi-Fi 5 GHz: {max_wifi_5}")
    print(f"Max number of Wi-Fi 6 GHz: {max_wifi_6}")

    print("\n===== Start processing! =====")
    loader.load_json(args.input, cb_process, options=args)


if __name__ == "__main__":
    main()
