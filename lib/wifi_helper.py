def get_wifi_freq_code(freq):
    match freq:
        case num if num in range(2401, 2495):
            return "2.4"
        case num if num in range(5150, 5925):
            return "5"
        case num if num in range(5926, 7125):
            return "6"
        case _:
            return "unknown"
