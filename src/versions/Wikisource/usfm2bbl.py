import cPickle
import re
import sys

version = sys.argv[1].capitalize()
if version == "Tyndale":
    usfm_books = ("01_GEN", "02_EXO", "03_LEV", "04_NUM", "05_DEU", None, None,
                  None, None, None, None, None, None, None, None, None, None,
                  None, None, None, None, None, None, None, None, None, None,
                  None, None, None, None, "06_JON", None, None, None, None,
                  None, None, None, "07_MAT", "08_MRK", "09_LUK", "10_JHN",
                  "11_ACT", "12_ROM", "13_1CO", "14_2CO", "15_GAL", "16_EPH",
                  "17_PHP", "18_COL", "19_1TH", "20_2TH", "21_1TI", "22_2TI",
                  "23_TIT", "24_PHM", "25_HEB", "26_JAS", "27_1PE", "28_2PE",
                  "29_1JN", "30_2JN", "31_3JN", "32_JUD", "33_REV")
else:
    usfm_books = ("01_GEN", "02_EXO", "03_LEV", "04_NUM", "05_DEU", "06_JOS",
                  "07_JDG", "08_RUT", "09_1SA", "10_2SA", "11_1KI", "12_2KI",
                  "13_1CH", "14_2CH", "15_EZR", "16_NEH", "20_EST", "21_JOB",
                  "22_PSA", "23_PRO", "24_ECC", "25_SNG", "28_ISA", "29_JER",
                  "30_LAM", "33_EZK", "34_DAN", "35_HOS", "36_JOL", "37_AMO",
                  "38_OBA", "39_JON", "40_MIC", "41_NAM", "42_HAB", "43_ZEP",
                  "44_HAG", "45_ZEC", "46_MAL", "49_MAT", "50_MRK", "51_LUK",
                  "52_JHN", "53_ACT", "54_ROM", "55_1CO", "56_2CO", "57_GAL",
                  "58_EPH", "59_PHP", "60_COL", "61_1TH", "62_2TH", "63_1TI",
                  "64_2TI", "65_TIT", "66_PHM", "67_HEB", "68_JAS", "69_1PE",
                  "70_2PE", "71_1JN", "72_2JN", "73_3JN", "74_JUD", "75_REV")
Bible = [unicode(version)]
for b in range(1, 67):
    if not usfm_books[b - 1]:
        Bible.append(tuple())
        continue
    fileobj = open("%s_%s.usfm" % (version.lower(), usfm_books[b - 1]), 'r')
    lines = [line.rstrip() for line in fileobj]
    fileobj.close()
    if version == "Tyndale":
        if b == 40:
            lines[797] = "\\c 23"
            lines[1079] = "\\c 28"
        elif b == 53:
            lines[15] = lines[15][8:]
            lines.insert(15, "\\c 2")
        i = 0
        if 41 <= b <= 42 or 63 <= b <= 64:
            chapter = 1
        while i < len(lines):
            match = re.match(r"(\d+)([,.:]\s?)?(?=\w)", lines[i])
            if match:
                lines[i] = "\\v %s " % match.group(1) + lines[i][match.end():]
                index = lines[i].find("\\v", 3)
            else:
                index = lines[i].find("\\v")
            if ((41 <= b <= 42 or 63 <= b <= 64) and
                    lines[i].startswith("\\v 1 ")):
                lines.insert(i, "\\c %d" % chapter)
                i += 1
                chapter += 1
            while index > 0:
                lines.insert(i + 1, lines[i][lines[i].index(" ", index + 3):])
                lines[i] = lines[i][:index]
                i += 1
                index = lines[i].find("\\v", 3)
            i += 1
    Bible.append([None])
    c = 0
    for line in lines[lines.index("\\c 1"):]:
        if line == "\\b":
            continue
        elif line.startswith("\\c"):
            if c > 0:
                Bible[b][c] = tuple(Bible[b][c])
            Bible[b].append([None])
            c += 1
        else:
            if line.startswith("\\v"):
                line = line[line[3:].index(" ") + 3:]
            line = re.sub(r"\\f \+ .+?\\f\*", r"", line)
            if version == "Tyndale":
                line = re.sub(r"(?<!\s)\.(?=\w)", r". ", line)
            elif version == "Wycliffe":
                line = line.replace("`", "").lstrip()
                match = re.match(r"The (tit(le|il) of the )?.+? salm. ", line)
                if match:
                    Bible[b][c][0] = unicode(line[match.end():])
                    continue
                line = re.sub(r"\s(?=(\s|[!),.:;?]))|(?<=\[)\s", r"", line)
            Bible[b][c].append(unicode(line.strip()))
    Bible[b][-1] = tuple(Bible[b][-1])
    Bible[b] = tuple(Bible[b])
Bible = tuple(Bible)
with open("%s.bbl" % version, 'wb') as fileobj:
    cPickle.dump(Bible, fileobj, -1)
