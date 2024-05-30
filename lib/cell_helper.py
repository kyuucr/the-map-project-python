import functools
import logging

REGION = {
    "GLOBAL": 255,
    "NAR": 1,
    "EU": 2,
    "EMEA": 6,
    "JAPAN": 8,
    "CHINA": 16,
    "APAC": 56,
    "NTN": 64,
    "UNKNOWN": 128
}

cell_table = [
    (1, 0, 599, 2110.0),
    (2, 600, 1199, 1930.0),
    (3, 1200, 1949, 1805.0),
    (4, 1950, 2399, 2110.0),
    (5, 2400, 2649, 869.0),
    (6, 2650, 2749, 875.0),
    (7, 2750, 3449, 2620.0),
    (8, 3450, 3799, 925.0),
    (9, 3800, 4149, 1844.9),
    (10, 4150, 4749, 2110.0),
    (11, 4750, 4949, 1475.9),
    (12, 5010, 5179, 729.0),
    (13, 5180, 5279, 746.0),
    (14, 5280, 5379, 758.0),
    (17, 5730, 5849, 734.0),
    (18, 5850, 5999, 860.0),
    (19, 6000, 6149, 875.0),
    (20, 6150, 6449, 791.0),
    (21, 6450, 6599, 1495.9),
    (22, 6600, 7399, 3510.0),
    (23, 7500, 7699, 2180.0),
    (24, 7700, 8039, 1525.0),
    (25, 8040, 8689, 1930.0),
    (26, 8690, 9039, 859.0),
    (27, 9040, 9209, 852.0),
    (28, 9210, 9659, 758.0),
    (29, 9660, 9769, 717.0),
    (30, 9770, 9869, 2350.0),
    (31, 9870, 9919, 462.5),
    (32, 9920, 10359, 1452.0),
    (33, 36000, 36199, 1900.0),
    (34, 36200, 36349, 2010.0),
    (35, 36350, 36949, 1850.0),
    (36, 36950, 37549, 1930.0),
    (37, 37550, 37749, 1910.0),
    (38, 37750, 38249, 2570.0),
    (39, 38250, 38649, 1880.0),
    (40, 38650, 39649, 2300.0),
    (41, 39650, 41589, 2496.0),
    (42, 41590, 43589, 3400.0),
    (43, 43590, 45589, 3600.0),
    (44, 45590, 46589, 703.0),
    (45, 46590, 46789, 1447.0),
    (46, 46790, 54539, 5150.0),
    (47, 54540, 55239, 5855.0),
    (48, 55240, 56739, 3550.0),
    (49, 56740, 58239, 3550.0),
    (50, 58240, 59089, 1432.0),
    (51, 59090, 59139, 1427.0),
    (52, 59140, 60139, 3300.0),
    (53, 60140, 60254, 2483.5),
    (65, 65536, 66435, 2110.0),
    (66, 66436, 67335, 2110.0),
    (67, 67336, 67535, 738.0),
    (68, 67536, 67835, 753.0),
    (69, 67836, 68335, 2570.0),
    (70, 68336, 68585, 1995.0),
    (71, 68586, 68935, 617.0),
    (72, 68936, 68985, 461.0),
    (73, 68986, 69035, 460.0),
    (74, 69036, 69465, 1475.0),
    (75, 69466, 70315, 1432.0),
    (76, 70316, 70365, 1427.0),
    (85, 70366, 70545, 728.0),
    (87, 70546, 70595, 420.0),
    (88, 70596, 70645, 422.0),
    (252, 255144, 256143, 5150.0),
    (255, 260894, 262143, 5725.0)
]

nr_table = [
    (1, 422000, 434000, REGION["GLOBAL"]),
    (2, 386000, 398000, REGION["NAR"]),
    (3, 361000, 376000, REGION["GLOBAL"]),
    (5, 173800, 178800, REGION["GLOBAL"]),
    (7, 524000, 538000, REGION["EMEA"]),
    (8, 185000, 192000, REGION["GLOBAL"]),
    (12, 145800, 149200, REGION["NAR"]),
    (13, 149200, 151200, REGION["NAR"]),
    (14, 151600, 153600, REGION["NAR"]),
    (18, 172000, 175000, REGION["JAPAN"]),
    (20, 158200, 164200, REGION["EMEA"]),
    (24, 305000, 311800, REGION["NAR"]),
    (25, 386000, 399000, REGION["NAR"]),
    (26, 171800, 178800, REGION["NAR"]),
    (28, 151600, 160600, (REGION["APAC"] | REGION["EU"])),
    (29, 143400, 145600, REGION["NAR"]),
    (30, 470000, 472000, REGION["NAR"]),
    (31, 92500, 93500, REGION["GLOBAL"]),
    (34, 402000, 405000, REGION["EMEA"]),
    (38, 514000, 524000, REGION["EMEA"]),
    (39, 376000, 384000, REGION["CHINA"]),
    (40, 460000, 480000, REGION["APAC"]),
    (41, 499200, 537999, REGION["GLOBAL"]),
    (46, 743334, 795000, REGION["GLOBAL"]),
    (47, 790334, 795000, REGION["GLOBAL"]),
    (48, 636667, 646666, REGION["GLOBAL"]),
    (50, 286400, 303400, REGION["EU"]),
    (51, 285400, 286400, REGION["EU"]),
    (53, 496700, 499000, REGION["UNKNOWN"]),
    (54, 334000, 335000, REGION["UNKNOWN"]),
    (65, 422000, 440000, REGION["GLOBAL"]),
    (66, 422000, 440000, REGION["NAR"]),
    (67, 147600, 151600, REGION["EMEA"]),
    (70, 399000, 404000, REGION["NAR"]),
    (71, 123400, 130400, REGION["NAR"]),
    (72, 92200, 93200, REGION["EMEA"]),
    (74, 295000, 303600, REGION["EMEA"]),
    (75, 286400, 303400, REGION["EU"]),
    (76, 285400, 286400, REGION["EU"]),
    (77, 620000, 680000, REGION["UNKNOWN"]),
    (78, 620000, 653333, REGION["UNKNOWN"]),
    (79, 693334, 733333, REGION["UNKNOWN"]),
    (85, 145600, 149200, REGION["NAR"]),
    (90, 499200, 538000, REGION["GLOBAL"]),
    (91, 285400, 286400, REGION["NAR"]),
    (92, 286400, 303400, REGION["NAR"]),
    (93, 285400, 286400, REGION["NAR"]),
    (94, 286400, 303400, REGION["NAR"]),
    (96, 795000, 875000, REGION["NAR"]),
    (100, 183880, 185000, REGION["UNKNOWN"]),
    (101, 380000, 382000, REGION["UNKNOWN"]),
    (102, 795000, 828333, REGION["UNKNOWN"]),
    (104, 828334, 875000, REGION["UNKNOWN"]),
    (105, 122400, 130400, REGION["UNKNOWN"]),
    (106, 187000, 188000, REGION["UNKNOWN"]),
    (109, 286400, 303400, REGION["UNKNOWN"]),
    (254, 496700, 500000, REGION["NTN"]),
    (255, 305000, 311800, REGION["NTN"]),
    (256, 434000, 440000, REGION["NTN"]),
    (257, 2054166, 2104165, REGION["GLOBAL"]),
    (258, 2016667, 2070832, REGION["GLOBAL"]),
    (259, 2270833, 2337499, REGION["GLOBAL"]),
    (260, 2229166, 2279165, REGION["GLOBAL"]),
    (261, 2070833, 2084999, REGION["NAR"]),
    (262, 2399166, 2415832, REGION["NAR"]),
    (263, 2564083, 2794243, REGION["GLOBAL"])
]

nr_freq_table = [
    (0.0, 0.005, 0, 599999),
    (3000.0, 0.015, 600000, 2016666),
    (24250.08, 0.06, 2016667, 3279165)
]


def earfcn_to_band(earfcn):
    logging.info(f"converting earfcn {earfcn} to band")
    if earfcn == "NaN":
        return "N/A"
    for cell in cell_table:
        if cell[1] <= earfcn and cell[2] >= earfcn:
            return cell[0]
    return 0


def earfcn_to_freq(earfcn):
    logging.info(f"converting earfcn {earfcn} to freq")
    if earfcn == "NaN":
        return "N/A"
    for cell in cell_table:
        if cell[1] <= earfcn and cell[2] >= earfcn:
            return (cell[3] + 0.1 * (earfcn - cell[1]))
    return 0.0


def nrarfcn_to_band(nrarfcn, reg=REGION["GLOBAL"], multiple=False):
    logging.info(f"converting nrarfcn {nrarfcn} to band, reg {reg}, "
                 f"multiple {multiple}")
    if nrarfcn == "NaN":
        return "N/A"
    ret = list()
    for cell in nr_table:
        if (cell[1] <= nrarfcn and cell[2] >= nrarfcn
            and ((reg & cell[3])
                 or cell[3] == REGION["UNKNOWN"])):
            ret.append({
                "num": cell[0],
                "reg": cell[3],
                "len": cell[2] - cell[1]})

    if multiple:
        return ("N/A" if len(ret == 0)
                else ",".join([f"n{val['num']}" for val in ret]))
    else:
        while len(ret) > 1:
            smallest = functools.reduce(
                lambda prev, curr: curr if curr["len"] < prev["len"] else prev,
                ret)
            if (smallest["reg"] == REGION["GLOBAL"]
                    or (smallest["reg"] == reg)):
                ret = [smallest]
            else:
                ret = [val for val in ret if val["num"] != smallest["num"]]
        return f"n{ret[0]['num']}"


def nrarfcn_to_freq(nrarfcn):
    logging.info(f"converting nrarfcn {nrarfcn} to freq")
    if nrarfcn == "NaN":
        return "NaN"
    for cell in nr_freq_table:
        if cell[2] <= nrarfcn and cell[3] >= nrarfcn:
            return round(cell[0] + cell[1] * (nrarfcn - cell[2]), 3)
    return 0.0
