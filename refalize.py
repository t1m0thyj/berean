"""refalize.py - reference analysis functions"""

import re

from config import *

ABBREVS = (("1 c", 46), ("1 chronicles", 13), ("1 corinthians", 46), ("1 jn",
    62), ("1 john", 62), ("1 k", 11), ("1 kgdms", 9), ("1 kgs", 11), ("1 king",
    11), ("1 kingdoms", 9), ("1 kings", 11), ("1 p", 60), ("1 paralipomenon",
    13), ("1 peter", 60), ("1 ptr", 60), ("1 samuel", 9), ("1 thessalonians",
    52), ("1 timothy", 54), ("1c", 46), ("1chr", 13), ("1chronicles", 13),
    ("1cor", 46), ("1corinthians", 46), ("1jn", 62), ("1john", 62), ("1k", 11),
    ("1kgdms", 9), ("1kgs", 11), ("1king", 11), ("1kingdoms", 9), ("1kings",
    11), ("1p", 60), ("1paralipomenon", 13), ("1pet", 60), ("1peter", 60),
    ("1ptr", 60), ("1sam", 9), ("1samuel", 9), ("1thess", 52),
    ("1thessalonians", 52), ("1tim", 54), ("1timothy", 54), ("2 c", 47),
    ("2 chronicles", 14), ("2 corinthians", 47), ("2 jn", 63), ("2 john", 63),
    ("2 k", 12), ("2 kgdms", 10), ("2 kgs", 12), ("2 king", 12), ("2 kingdoms",
    10), ("2 kings", 12), ("2 p", 61), ("2 paralipomenon", 14), ("2 peter",
    61), ("2 ptr", 61), ("2 samuel", 10), ("2 thessalonians", 53),
    ("2 timothy", 55), ("2c", 47), ("2chr", 14), ("2chronicles", 14), ("2cor",
    47), ("2corinthians", 47), ("2jn", 63), ("2john", 63), ("2k", 12),
    ("2kgdms", 10), ("2kgs", 12), ("2king", 12), ("2kingdoms", 10), ("2kings",
    12), ("2p", 61), ("2paralipomenon", 14), ("2pet", 61), ("2peter", 61),
    ("2ptr", 61), ("2sam", 10), ("2samuel", 10), ("2thess", 53),
    ("2thessalonians", 53), ("2tim", 55), ("2timothy", 55), ("3 jn", 64),
    ("3 john", 64), ("3 kgdms", 11), ("3 kgs", 11), ("3 kingdoms", 11),
    ("3 kings", 11), ("3jn", 64), ("3john", 64), ("3kgdms", 11), ("3kgs", 11),
    ("3kingdoms", 11), ("3kings", 11), ("4 kgdms", 12), ("4 kgs", 12),
    ("4 kingdoms", 12), ("4 kings", 12), ("4kgdms", 12), ("4kgs", 12),
    ("4kingdoms", 12), ("4kings", 12), ("acts", 44), ("amos", 30),
    ("apocalypse of john", 66), ("c", 51), ("canticle of canticles", 22),
    ("col", 51), ("colossians", 51), ("d", 5), ("dan", 27), ("daniel", 27),
    ("deut", 5), ("deuteronomy", 5), ("dt", 5), ("e", 2), ("eccl", 21),
    ("ecclesiastes", 21), ("ek", 26), ("eph", 49), ("ephesians", 49), ("es",
    17), ("ester", 17), ("esth", 17), ("esther", 17), ("exod", 2), ("exodus",
    2), ("ezek", 26), ("ezekiel", 26), ("ezk", 26), ("ezra", 15), ("g", 1),
    ("gal", 48), ("galatians", 48), ("gen", 1), ("genesis", 1), ("gn", 1),
    ("h", 58), ("hab", 35), ("habakkuk", 35), ("hag", 37), ("haggai", 37),
    ("heb", 58), ("hebrews", 58), ("hos", 28), ("hosea", 28), ("i", 23),
    ("i c", 46), ("i chronicles", 13), ("i corinthians", 46), ("i jn", 62),
    ("i john", 62), ("i k", 11), ("i kgdms", 9), ("i kgs", 11), ("i king", 11),
    ("i kingdoms", 9), ("i kings", 11), ("i p", 60), ("i paralipomenon", 13),
    ("i peter", 60), ("i ptr", 60), ("i samuel", 9), ("i thessalonians", 52),
    ("i timothy", 54), ("ic", 46), ("ichronicles", 13), ("icorinthians", 46),
    ("ii c", 47), ("ii chronicles", 14), ("ii corinthians", 47), ("ii jn", 63),
    ("ii john", 63), ("ii k", 12), ("ii kgdms", 10), ("ii kgs", 12),
    ("ii king", 12), ("ii kingdoms", 10), ("ii kings", 12), ("ii p", 61),
    ("ii paralipomenon", 14), ("ii peter", 61), ("ii ptr", 61), ("ii samuel",
    10), ("ii thessalonians", 53), ("ii timothy", 55), ("iic", 47),
    ("iichronicles", 14), ("iicorinthians", 47), ("iii jn", 64), ("iii john",
    64), ("iii kgdms", 11), ("iii kgs", 11), ("iii kingdoms", 11),
    ("iii kings", 11), ("iiijn", 64), ("iiijohn", 64), ("iiikgdms", 11),
    ("iiikgs", 11), ("iiikingdoms", 11), ("iiikings", 11), ("iijn", 63),
    ("iijohn", 63), ("iik", 12), ("iikgdms", 10), ("iikgs", 12), ("iiking",
    12), ("iikingdoms", 10), ("iikings", 12), ("iip", 61), ("iiparalipomenon",
    14), ("iipeter", 61), ("iiptr", 61), ("iisamuel", 10), ("iithessalonians",
    53), ("iitimothy", 55), ("ijn", 62), ("ijohn", 62), ("ik", 11), ("ikgdms",
    9), ("ikgs", 11), ("iking", 11), ("ikingdoms", 9), ("ikings", 11), ("ip",
    60), ("iparalipomenon", 13), ("ipeter", 60), ("iptr", 60), ("isa", 23),
    ("isaiah", 23), ("isamuel", 9), ("ithessalonians", 52), ("itimothy", 54),
    ("iv kgdms", 12), ("iv kgs", 12), ("iv kingdoms", 12), ("iv kings", 12),
    ("ivkgdms", 12), ("ivkgs", 12), ("ivkingdoms", 12), ("ivkings", 12),
    ("j", 6), ("james", 59), ("jas", 59), ("jb", 18), ("jd", 7), ("jdgs", 7),
    ("jer", 24), ("jeremiah", 24), ("jhn", 43), ("jn", 43), ("jo", 43), ("job",
    18), ("joel", 29), ("john", 43), ("jol", 29), ("jonah", 32), ("josh", 6),
    ("joshua", 6), ("js", 6), ("ju", 65), ("jude", 65), ("judg", 7), ("judges",
    7), ("l", 42), ("lam", 25), ("lamentations", 25), ("le", 3), ("lev", 3),
    ("leviticus", 3), ("lk", 42), ("luke", 42), ("lv", 3), ("ma", 40), ("mal",
    39), ("malachi", 39), ("mark", 41), ("matt", 40), ("matthew", 40), ("mic",
    33), ("micah", 33), ("mk", 41), ("mrk", 41), ("mt", 40), ("n", 4), ("nah",
    34), ("nahum", 34), ("nam", 34), ("neh", 16), ("nehemiah", 16), ("nm", 4),
    ("num", 4), ("numbers", 4), ("obad", 31), ("obadiah", 31), ("p", 19),
    ("phil", 50), ("philemon", 57), ("philippians", 50), ("phlm", 57), ("phm",
    57), ("php", 50), ("pr", 20), ("prov", 20), ("proverbs", 20), ("ps", 19),
    ("psalm", 19), ("psalms", 19), ("psm", 19), ("pss", 19), ("qohelet", 21),
    ("qoheleth", 21), ("rev", 66), ("revelation of john", 66), ("rom", 45),
    ("romans", 45), ("ruth", 8), ("s", 22), ("sng", 22), ("solomon", 22),
    ("song", 22), ("song of solomon", 22), ("song of songs", 22), ("t", 56),
    ("titus", 56), ("zech", 38), ("zechariah", 38), ("zeph", 36), ("zephaniah",
    36))


def get_book_index(abbrev, no_error=False):
    abbrev = abbrev.lower()
    for abbrev2, book_num in ABBREVS:
        if abbrev2.startswith(abbrev):
            return book_num
    if not no_error:
        raise ValueError
    else:
        return -1


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
