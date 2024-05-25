from datetime import datetime
from os.path import isfile
import json


def create_sigcap_timestamp(input_str):
    # Fix tz format by adding ':'
    if (input_str[len(input_str) - 2] != ':'):
        input_str = input_str[:len(input_str) - 2] \
            + ':' \
            + input_str[len(input_str) - 2:]

    return datetime.fromisoformat(input_str).timestamp()


def create_json_filter(input_str):
    if (isfile(input_str)):
        with open(input_str) as input_file:
            json_obj = json.load(input_file)
    else:
        json_obj = json.loads(input_str)

    return json_obj


def get_operator_name(sigcap):
    op = sigcap["opName"]
    if (op == ""
            or op == "Searching for Service"
            or op == "Extended Network"
            or op == "Preferred System"):
        op = (sigcap["simName"] if sigcap["simName"]
              else sigcap["carrierName"] if sigcap["carrierName"]
              else "Unknown")

    op = op.strip()
    for usual_op in ["AT&T", "Sprint", "T-Mobile", "Verizon"]:
        if op != usual_op and op.startswith(usual_op):
            op = usual_op

    return op


def get_network_type(sigcap):
    has_nr = "nr_info" in sigcap and (len(sigcap["nr_info"]) > 0)
    has_primary_nr = has_nr and any([val["status"] == "primary"
                                     for val in sigcap["nr_info"]])
    has_lte = "cell_info" in sigcap and (len(sigcap["cell_info"]) > 0)
    if (has_nr and has_primary_nr and not has_lte):
        networkType = "NR"
    elif (has_nr and has_lte):
        networkType = "NR-NSA"
    elif (has_lte):
        networkType = "LTE"
    elif ("networkType" in sigcap):
        networkType = sigcap["networkType"]
    else:
        networkType = "unknown"

    return networkType