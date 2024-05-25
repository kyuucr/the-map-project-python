import json
import re


def load_json(input_dir, callback, options=None):

    re_exts = re.compile(r"\.(txt|json)$")
    list_files = [
        str(p) for p in
        input_dir.rglob("*")
        if re_exts.search(str(p))]

    # print(list_files)
    MAX_NUM_OBJ = 5000
    all_obj = []
    all_files = []
    result_obj = {
        "files": [],
        "json": []}
    if (options is not None):
        result_obj['options'] = options

    # with list_files[0] as file:
    for file in list_files:
        with open(file) as item_file:
            json_obj = json.load(item_file)
            all_files.append(file)
            if (isinstance(json_obj, list)):
                all_obj += json_obj
            else:
                all_obj.append(json_obj)
            if (len(all_obj) >= MAX_NUM_OBJ):
                result_obj['files'] = all_files
                result_obj['json'] = all_obj
                callback(result_obj)
                all_obj = []
                all_files = []

    if (len(all_obj) > 0):
        result_obj['files'] = all_files
        result_obj['json'] = all_obj
        callback(result_obj)
