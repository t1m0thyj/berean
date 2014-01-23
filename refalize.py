"""refalize.py - reference analysis functions"""

import re

from info import *

ABBREVS = {"ge": 1, "ex": 2, "exo": 2, "le": 3, "nu": 4, "de": 5, "deu": 5,
    "jos": 6, "jdg": 7, "ru": 8, "rut": 8, "1s": 9, "1sa": 9, "2s": 10,
    "2sa": 10, "1k": 11, "1ki": 11, "1kin": 11, "2k": 12, "2ki": 12,
    "2kin": 12, "1ch": 13, "2ch": 14, "ezr": 15, "ne": 16, "es": 17, "est": 17,
    "psa": 19, "psalm": 19, "pr": 20, "pro": 20, "ec": 21, "ecc": 21, "so": 22,
    "son": 22, "ca": 22, "can": 22, "cant": 22, "canticles": 22, "is": 23,
    "je": 24, "la": 25, "eze": 26, "da": 27, "ho": 28, "joe": 29, "am": 30,
    "amo":30, "ob": 31, "oba": 31, "jon": 32, "mi": 33, "na": 34, "zep": 36,
    "zec": 38, "mat": 40, "mar": 41, "mk": 41, "mrk": 41, "lu": 42, "luk": 42,
    "lk": 42, "joh": 43, "jh": 43, "jhn": 43, "ac": 44, "act": 44, "ro": 45,
    "1co": 46, "2co": 47, "ga": 48, "ep": 49, "ph": 50, "phi": 50, "phili": 50,
    "php": 50, "co": 51, "1th": 52, "1the": 52, "2th": 53, "2the": 53,
    "1ti": 54, "2ti": 55, "ti": 56, "tit": 56, "phile": 57, "phm": 57,
    "he": 58, "ja": 59, "jam": 59, "1p": 60, "1pe": 60, "2p": 61, "2pe": 61,
    "1j": 62, "1jo": 62, "1joh": 62, "1jh": 62, "1jhn": 62, "2j": 63,
    "2jo": 63, "2joh": 63, "2jh": 63, "2jhn": 63, "3j": 64, "3jo": 64,
    "3joh": 64, "3jh": 64, "3jhn": 64, "ju": 65, "jud": 65, "jde": 65,
    "re": 66}
for i in range(66):
    book_name = BOOK_NAMES[i].replace(" ", "").lower()
    ABBREVS[book_name] = i + 1
    book_abbrev = BOOK_ABBREVS[i].lower()
    if book_abbrev != book_name:
        ABBREVS[book_abbrev] = i + 1


def get_book_index(abbrev, no_error=False):
    abbrev = abbrev.lower()
    for i, roman in enumerate(("i", "ii", "iii")):
        if abbrev.startswith(roman + " "):
            abbrev = str(i + 1) + abbrev[abbrev.index(" ") + 1:]
    if abbrev in ABBREVS:
        return ABBREVS[abbrev.replace(" ", "")]
    elif no_error:
        return -1
    raise ValueError


def refalize(reference):
    groups = re.match(r'((?:[1-3]\s?|i{1,3}\s)?[A-Za-z]+)\s*(\d+)?\W*(\d+)?',
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


def refalize2(references, Bible):
    references = filter(None, [reference.lstrip() for reference in re.split(
        r'[,;\n]', references)])
    pattern = re.compile(
        r'((?:[1-3]\s?|i{1,3}\s)?[A-Za-z]+)?\s*(\d+)?\W*(\d+)?',
        flags=re.IGNORECASE)
    style = 1   # 0 = full reference, 1 = reference with no verse, 2 = reference with no chapter
    for i in range(len(references)):
        if "-" in references[i]:
            first, last = references[i].split("-")
        else:
            first = references[i]
            last = None
        match = pattern.match(first)
        groups = match.groups()
        if groups[0] and (groups[0].lower() not in
                ("c", "ch", "chap", "v", "ver", "vv")):
            book = get_book_index(groups[0])
        else:
            book = references[i - 1][1][0]
        if groups[2]:
            chapter = int(groups[1])
            verse = int(groups[2])
            style = 0
        elif book in (31, 57, 63, 64, 65):
            chapter = 1
            verse = int(groups[1])
            style = 2
        elif style != 1 and ((not groups[0]) or groups[0].lower() in
                ("v", "ver", "vv")):
            chapter = references[i - 1][1][1]
            verse = int(groups[1])
            style = 2
        else:
            chapter = int(groups[1])
            verse = 1
            style = 1
        first = (book, chapter, verse)
        if last:
            match2 = pattern.match(last.lstrip())
            if match2:
                groups2 = match2.groups()
                if groups2[0] and (groups2[0].lower() not in
                        ("c", "ch", "chap", "v", "ver", "vv")):
                    book = get_book_index(groups2[0])
                else:
                    book = first[0]
                if groups2[1] and groups2[2]:
                    chapter = int(groups2[1])
                    verse = int(groups2[2])
                    style = 0
                elif groups2[1] and not groups2[2]:
                    if book in (31, 57, 63, 64, 65):
                        chapter = 1
                        verse = int(groups2[1])
                    elif style != 1:
                        chapter = first[1]
                        verse = int(groups2[1])
                    else:
                        chapter = int(groups2[1])
                        verse = len(Bible[book][chapter]) - 1
                last = (book, chapter, verse)
            else:
                last = None
        elif re.search(r'\W*ff', references[i][match.end(len(groups)):],
                flags=re.IGNORECASE):  # Recognize 'ff'
            if style != 1:
                last = (book, chapter, len(Bible[book][chapter]) - 1)
            else:
                last = (book, len(Bible[book]) - 1, len(Bible[book][-1]) - 1)
        if not last:
            last = first
            if style == 1:
                last = (last[0], last[1], len(Bible[last[0]][last[1]]) - 1)
        references[i] = (first, last)
    return references


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
