from lib import util

OPERAND_LIST = ["=", "~", ">", "<"]


def compare(filter_obj, target_obj, is_date=False):
    ret = False

    if (isinstance(filter_obj, dict)):
        # If object, iterate members
        ret = True
        for param in filter_obj:
            # If target_obj is array, iterate over target_obj's entries
            if (isinstance(target_obj, dict) and param in target_obj):
                if (isinstance(target_obj[param], list)):
                    tempRet = False
                    for curr_target in target_obj[param]:
                        tempRet = tempRet or compare(
                            filter_obj[param],
                            curr_target,
                            (param == 'datetimeIso'
                                or param == 'local_datetime'))
                    ret = ret and tempRet
                else:
                    ret = ret and compare(
                        filter_obj[param],
                        target_obj[param],
                        (param == 'datetimeIso'
                            or param == 'local_datetime'))
            else:
                ret = False
    elif (isinstance(filter_obj, list)):
        # If filter_obj is array, do exclusive filter_obj on its entries
        # (assuming target_obj is neither array nor object)
        ret = True
        for curr_filter in filter_obj:
            ret = ret and compare(curr_filter, target_obj, is_date)
    else:
        # Check first char from filter_obj
        operand = ""
        if (isinstance(filter_obj, str)):
            operand = filter_obj[0:1]
        # If operand is valid, go ahead and cut filter_obj
        if (operand in OPERAND_LIST):
            filter_obj = filter_obj[1:]

        # Try to parse filter obj as int
        try:
            filter_obj = int(filter_obj)
        except ValueError:
            # do nothing
            pass

        # Special case if compared data is date
        if (is_date):
            filter_obj = util.create_sigcap_timestamp(filter_obj)
            target_obj = util.create_sigcap_timestamp(target_obj)
        elif (filter_obj == "undefined"):
            filter_obj = None

        # Special case if obj is string
        if (isinstance(target_obj, str) and isinstance(filter_obj, str)):
            match operand:
                case "=":
                    ret = filter_obj in target_obj
                case "~":
                    ret = filter_obj not in target_obj
                case _:
                    ret = filter_obj in target_obj
        else:
            match operand:
                case "=":
                    ret = (filter_obj == target_obj)
                case "~":
                    ret = (filter_obj != target_obj)
                case ">":
                    ret = (filter_obj < target_obj)
                case "<":
                    ret = (filter_obj > target_obj)
                case _:
                    ret = (filter_obj == target_obj)
    return ret


def filter_array(filter_list, target_list, is_reverse=False):
    output_list = []
    # Sanity check
    if (not isinstance(filter_list, list)):
        filter_list = [filter_list]

    # For each filter_list, add filter_list results to output_list
    # since this is inclusive, it may outputs 2 or more
    # same datapoints depends on the filter_lists
    for filter_obj in filter_list:
        for target_obj in target_list:
            result = compare(filter_obj, target_obj)
            if (is_reverse):
                result = not result
            if (result):
                output_list.append(target_obj)

    return output_list
