"""refalize.py - reference analyzing functions"""

import re

from info import *

BOOK_NAMES = [book_name.replace(" ", "").lower() for book_name in BOOK_NAMES]


def refalize(reference):
    groups = re.match(r'((?:[1-3]\s?|i{1,3}\s)?[A-Za-z]+)\s*(\d+)?\W*(\d+)?',
        reference.lstrip(), flags=re.IGNORECASE).groups()
    abbrev = groups[0].replace(" ", "").lower()
    if abbrev not in BOOK_ABBREVS:
        for i in range(len(BOOK_NAMES)):
            if BOOK_NAMES[i].startswith(abbrev):
                book = i + 1
                break
    else:
        book = BOOK_ABBREVS[abbrev]
    if groups[2]:
        return (book, int(groups[1]), int(groups[2]))
    elif not groups[1]:
        return (book, 1, -1)
    elif book not in (31, 57, 63, 64, 65):
        return (book, int(groups[1]), -1)
    else:
        return (book, 1, int(groups[1]))


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
            abbrev = groups[0].replace(" ", "").lower()
            if abbrev not in BOOK_ABBREVS:
                for j in range(len(BOOK_NAMES)):
                    if BOOK_NAMES[j].startswith(abbrev):
                        book = j + 1
                        break
            else:
                book = BOOK_ABBREVS[abbrev]
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
                    abbrev = groups2[0].replace(" ", "").lower()
                    if abbrev not in BOOK_ABBREVS:
                        for j in range(len(BOOK_NAMES)):
                            if BOOK_NAMES[j].startswith(abbrev):
                                book = j + 1
                                break
                    else:
                        book = BOOK_ABBREVS[abbrev]
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


def validate(reference, numbers=False):
    reference = reference.strip()
    if reference[-1].isdigit():
        return True
    if not numbers:
        book = reference.replace(" ", "").lower()
        if book not in abbrevs:
            for i in range(len(books)):
                if books[i].startswith(book):
                    return True
        else:
            return True
    return False
