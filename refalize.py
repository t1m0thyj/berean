"""refalize.py - reference analysis functions"""

import re

from config import *

ABBREVS = {"ge": 1, "gen": 1, "ex": 2, "exo": 2, "exod": 2, "le": 3, "lev": 3,
    "nu": 4, "num": 4, "de": 5, "deu": 5, "deut": 5, "jos": 6, "josh": 6,
    "jdg": 7, "judg": 7, "ru": 8, "rut": 8, "ruth": 8, "1s": 9, "1sa": 9,
    "1sam": 9, "2s": 10, "2sa": 10, "2sam": 10, "1k": 11, "1ki": 11,
    "1kin": 11, "1kgs": 11, "2k": 12, "2ki": 12, "2kin": 12, "2kgs": 12,
    "1ch": 13, "1chr": 13, "2ch": 14, "2chr": 14, "ezr": 15, "ne": 16,
    "neh": 16, "es": 17, "est": 17, "esth": 17, "ps": 19, "psa": 19,
    "psalm": 19, "pr": 20, "pro": 20, "prov": 20, "ec": 21, "ecc": 21,
    "eccl": 21, "ca": 22, "can": 22, "cant": 22, "canticles": 22, "so": 22,
    "son": 22, "song": 22, "is": 23, "isa": 23, "je": 24, "jer": 24, "la": 25,
    "lam": 25, "eze": 26, "ezek": 26, "da": 27, "dan": 27, "ho": 28, "hos": 28,
    "joe": 29, "am": 30, "amo": 30, "ob": 31, "oba": 31, "obad": 31, "jon": 32,
    "mi": 33, "mic": 33, "na": 34, "nah": 34, "hab": 35, "zep": 36, "zeph": 36,
    "hag": 37, "zec": 38, "zech": 38, "mal": 39, "mat": 40, "matt": 40,
    "mar": 41, "mk": 41, "mrk": 41, "lk": 42, "lu": 42, "luk": 42, "joh": 43,
    "jh": 43, "jhn": 43, "ac": 44, "act": 44, "ro": 45, "rom": 45, "1co": 46,
    "1cor": 46, "2co": 47, "2cor": 47, "ga": 48, "gal": 48, "ep": 49,
    "eph": 49, "ph": 50, "phi": 50, "phil": 50, "phili": 50, "php": 50,
    "co": 51, "col": 51, "1th": 52, "1the": 52, "1thes": 52, "1thess": 52,
    "2th": 53, "2the": 53, "2thes": 53, "2thess": 53, "1ti": 54, "1tim": 54,
    "2ti": 55, "2tim": 55, "ti": 56, "tit": 56, "phile": 57, "phlm": 57,
    "phm": 57, "he": 58, "heb": 58, "ja": 59, "jam": 59, "jas": 59, "1p": 60,
    "1pe": 60, "1pet": 60, "2p": 61, "2pe": 61, "2pet": 61, "1j": 62,
    "1jo": 62, "1joh": 62, "1jh": 62, "1jhn": 62, "2j": 63, "2jo": 63,
    "2joh": 63, "2jh": 63, "2jhn": 63, "3j": 64, "3jo": 64, "3joh": 64,
    "3jh": 64, "3jhn": 64, "ju": 65, "jud": 65, "jde": 65, "re": 66, "rev": 66}
for i in range(66):
    ABBREVS[BOOK_NAMES[i].replace(" ", "").lower()] = i + 1


def get_book_index(abbrev, no_error=False):
    abbrev = abbrev.lower()
    for i, roman in enumerate(("i", "ii", "iii")):
        if abbrev.startswith(roman + " "):
            abbrev = str(i + 1) + abbrev[abbrev.index(" ") + 1:]
    abbrev = abbrev.replace(" ", "")
    if abbrev in ABBREVS:
        return ABBREVS[abbrev]
    elif no_error:
        return -1
    raise ValueError


def refalize(reference):
    groups = re.match(r"((?:[1-3]\s?|i{1,3}\s)?[a-z]+)\s*(\d+)?\W*(\d+)?",
        reference.lstrip(), flags=re.IGNORECASE).groups()
    book = get_book_index(groups[0])
    if groups[2]:
        return (book, int(groups[1]), int(groups[2]))
    elif groups[1]:
        if book not in (31, 57, 63, 64, 65):
            return (book, int(groups[1]), -1)
        else:
            return (book, 1, int(groups[1]))
    else:
        return (book, 1, -1)


def refalize2(references):
    references = filter(None, [reference.lstrip() for reference in
        re.split(r"[,;\n]", references)])
    start_pattern = re.compile(
        r"((?:[1-3]\s?|i{1,3}\s)?[a-z]+)?\s*(\d+)?\W*(\d+)?",
        flags=re.IGNORECASE)
    stop_pattern = re.compile(r"(\d+)\W*(\d+)?")
    has_verse = False
    failed = []
    for i in range(len(references)):
        try:
            if "-" in references[i]:
                start, stop = references[i].split("-")
            else:
                start, stop = references[i], None
            start_groups = start_pattern.match(start).groups()
            if start_groups[0]:
                book = get_book_index(start_groups[0])
            else:
                book = references[i - 1][0]
            has_verse2 = True
            if start_groups[2]:
                chapter, verse = int(start_groups[1]), int(start_groups[2])
            elif book in (31, 57, 63, 64, 65):
                chapter, verse = 1, int(start_groups[1])
            elif (not has_verse) or start_groups[0]:
                chapter, verse = int(start_groups[1]), 1
                has_verse2 = False
            else:
                chapter, verse = references[i - 1][1], int(start_groups[1])
            reference = [book, chapter, verse]
            has_verse = has_verse2
            if stop:
                stop_groups = stop_pattern.match(stop.lstrip()).groups()
                if stop_groups[1]:
                    chapter, verse = int(stop_groups[0]), int(stop_groups[1])
                elif book in (31, 57, 63, 64, 65):
                    chapter, verse = 1, int(stop_groups[0])
                elif not has_verse:
                    chapter = int(stop_groups[0])
                    verse = CHAPTER_LENGTHS[book - 1][chapter - 1]
                else:
                    chapter, verse = reference[1], int(stop_groups[0])
                reference.extend([chapter, verse])
            elif not has_verse:
                reference.extend([chapter,
                    CHAPTER_LENGTHS[book - 1][chapter - 1]])
            else:
                reference.extend([-1, -1])
            references[i] = reference + [references[i]]
        except Exception:
            failed.append(references[i])
    return (references, failed)


def validate(reference, check_book=True):
    reference = reference.strip()
    if reference[-1].isdigit():
        return True
    if check_book:
        for i, char in enumerate(reference):
            if i > 0 and char.isdigit():
                break
        return get_book_index(reference[:i].rstrip(), True) != -1
    return False
